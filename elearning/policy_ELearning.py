###############################################################################
#
# Copyright 2020, University of Stuttgart: Institute for Natural Language Processing (IMS)
#
# This file is part of Adviser.
# Adviser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3.
#
# Adviser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Adviser.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from datetime import datetime, timedelta
import decimal
from enum import Enum
import random
import re
import traceback
from typing import List
import time
from copy import deepcopy
import locale

from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.sqltypes import DateTime

import config
from elearning.booksearch import get_book_links
from services.service import PublishSubscribe
from services.service import Service
from utils import SysAct, SysActionType
from utils.domain.jsonlookupdomain import JSONLookupDomain
from utils.logger import DiasysLogger
from utils import UserAct
from elearning.moodledb import BadgeCompletionStatus, MBadge, MChatbotSettings, MCourseModulesViewed, MCourseSection, MFile, MGradeItem, MRecentlyAcessedItem, connect_to_moodle_db, Base, MUser, MCourseModule, get_time_estimates, MModule, MChatbotProgressSummary, MChatbotWeeklySummary
from utils.useract import UserActionType, UserAct

locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')

LAST_ACCESSED_COURSEMODULE = 'last_accessed_coursemodule'
NEXT_SUGGESTED_COURSEMODULE = 'next_suggested_coursemodule'
COURSE_MODULE_ID = 'course_module_id'
ASSIGN_ID = 'assign_id'
TURNS = 'turns'
LAST_USER_ACT = 'last_act'
FIRST_TURN = 'first_turn'
MODE = 'mode'
S_INDEX = 's_index'
LAST_SEARCH = 'last_search'
REVIEW_QUIZZES = "review_quizzes"

# JUST_LOGGED_IN = "just_logged_in"

learning_material_types = ["url", "book", "resource"]
assignment_material_types = ['h5pactivity']# query day-wise completions


COURSE_PROGRESS_DISPLAY_PERCENTAGE_INCREMENT = 0.1



class ChatbotWindowSize(Enum):
	DEFAULT = 0
	LARGE = 1


class ELearningPolicy(Service):
	""" Base class for handcrafted policies.

	Provides a simple rule-based policy. Can be used for any domain where a user is
	trying to find an entity (eg. a course from a module handbook) from a database
	by providing constraints (eg. semester the course is offered) or where a user is
	trying to find out additional information about a named entity.

	Output is a system action such as:
	 * `inform`: provides information on an entity
	 * `request`: request more information from the user
	 * `bye`: issue parting message and end dialog

	In order to create your own policy, you can inherit from this class.
	Make sure to overwrite the `choose_sys_act`-method with whatever additionally
	rules/functionality required.

	"""

	def __init__(self, domain: JSONLookupDomain, logger: DiasysLogger = DiasysLogger(),
				 max_turns: int = 25):
		"""
		Initializes the policy

		Arguments:
			domain {domain.jsonlookupdomain.JSONLookupDomain} -- Domain

		"""
		Service.__init__(self, domain=domain)
		self.domain_key = domain.get_primary_key()
		self.logger = logger
		self.max_turns = max_turns
		self.session = None

	def get_session(self):
		if isinstance(self.session, type(None)):
			self._init_db()
		return self.session
	
	def get_moodle_server_time(self, userid: int) -> DateTime:
		""" Returns the current moodle server time as unix timestamp """
		difference = self.get_state(userid, "SERVERTIMEDIFFERENCE")
		return datetime.fromtimestamp(int(time.time()) + difference)

	@PublishSubscribe(pub_topics=['control_event'])
	def open_chatbot(self, user_id: int):
		""" Triggers the UI chatwindow to open """
		user = self.get_current_user(user_id)
		if (not user.settings) or user.settings.allow_auto_open:
			return {
				"control_event": "UI_OPEN",
				"user_id": user_id
			}
		
	@PublishSubscribe(pub_topics=['control_event'])
	def resize_chatbot(self, user_id: int, size: ChatbotWindowSize):
		""" Resizes the chatwindow """
		if size == ChatbotWindowSize.DEFAULT:
			return {
				"control_event": "UI_SIZE_DEFAULT",
				"user_id": user_id
			}
		elif size == ChatbotWindowSize.LARGE:
			return {
				"control_event": "UI_SIZE_LARGE",
				"user_id": user_id
			}
		
	def _init_db(self):
		success = False
		while not success:
			try:
				engine, conn = connect_to_moodle_db()
				self.Session = sessionmaker()
				self.Session.configure(bind=engine)
				self.session = self.Session()
				Base.metadata.create_all(engine)
				success = True
				print("====== SUCCESS ======")
			except:
				print("===== ERROR CONNECTING TO DB (Potentially have to wait for moodle setup to finish), RETRY IN 10 SECONDS ===== ")
				traceback.print_exc()
				time.sleep(10) 
	

	def dialog_start(self, user_id: str):
		"""
			resets the policy after each dialog
		"""
		if not self.get_state(user_id, TURNS):
			self.set_state(user_id, LAST_USER_ACT, None)
			self.set_state(user_id, TURNS, 0)
			self.set_state(user_id, FIRST_TURN, True)
			self.set_state(user_id, LAST_SEARCH, {})
			self.set_state(user_id, S_INDEX, 0)  # the index in current suggestions for the current system reccomendation

	def clean_completed_sections_from_recentlyaccessed_items(self, user_id: int, course_id: int):
		# check which module sections are completed.
		# if so, remove all of its modules from the recently accessed items list.
		user = self.get_current_user(user_id)
		recently_accessed_modules = self.get_session().query(MRecentlyAcessedItem).filter(MRecentlyAcessedItem._course_id==course_id, MRecentlyAcessedItem._userid==user_id).all()
		section_ids = set()
		for recent_item in recently_accessed_modules:
			section = recent_item.coursemodule.section
			if section.id in section_ids:
				continue # already checked this section
			section_ids.add(section.id)
			if section.is_completed(user_id=user_id, session=self.get_session(), include_types=learning_material_types + assignment_material_types):
				# all completed -> delete
				self.get_session().query(MRecentlyAcessedItem).filter(MRecentlyAcessedItem._coursemodule_id.in_(section.sequence), MRecentlyAcessedItem._course_id==course_id, MRecentlyAcessedItem._userid==user_id).delete()
		self.get_session().commit()
			
	
	@PublishSubscribe(sub_topics=["moodle_event"], pub_topics=["sys_acts", "sys_state", "html_content"])
	def moodle_event(self, user_id: int, moodle_event: dict) -> dict(sys_acts=List[SysAct], sys_state=SysAct, html_content=str):
		""" Responsible for reacting to events from mooodle.
			Triggered by interaction with moodle (NOT the chatbot), e.g. when someone completes a coursemodule.

			Currently supports the following events:
			* \\core\\event\\course_module_completion_updated
		"""
		event_name = moodle_event['eventname'].lower().strip()
		event_action = moodle_event['action'].lower().strip()

		print("=================")
		print("EVENT")
		print(event_name)
		print(moodle_event)
		print("COMPLETION UPDATED?", moodle_event == "\\core\\event\\course_module_completion_updated")
		print("=================")
		# \mod_h5pactivity\event\statement_received
		# if event_name == "\\core\\event\\user_loggedin":
		# 	self.set_state(user_id, JUST_LOGGED_IN, True)
		if event_name == "\\core\\event\\user_loggedin":
			self.clear_memory(user_id)
		elif event_name == "\\core\\event\\badge_awarded":
			return {'sys_acts': [
				self.congratulate_badge_issued(user_id=user_id, badge_id=moodle_event['objectid'], contextid=moodle_event['contextid'])
			]}
		elif event_name == "\\core\\event\\course_module_completion_updated":
			# TODO check if we finished a whole branch
			# TODO if so, offer congratulations, the review, and then next possibilities?
			# TODO recognize branches by Title / and or dependencies
			# TODO comment on improvement, if quiz?
			branch_quizzes = self.get_session().query(MCourseModule).get(moodle_event['contextinstanceid']).get_branch_quizes_if_complete(session=self.get_session(), user_id=user_id)
			self.set_state(user_id, REVIEW_QUIZZES, branch_quizzes)
			if len(branch_quizzes) > 0:
				# ask user if they want to review any of the quizzes
				return SysAct(act_type=SysActionType.RequestReviewOrNext)
		elif event_name == "\\core\\event\\user_graded":
			self.open_chatbot(user_id)
			# extract grade info
			gradeItem: MGradeItem = self.get_session().get(MGradeItem, int(moodle_event['other']['itemid']))
			# gradeItem: MGradeItem = grade.get_grade_item(self.get_session())
			finalgrade = float(moodle_event['other']['finalgrade'])
			if finalgrade == gradeItem.grademax:
				# all questions correct
				self.logger.dialog_turn(f"# USER {user_id} # POLICY_MOODLEEVENT - all questions correct, finalgrade: {finalgrade}")
				self.logger.dialog_turn(f"# USER {user_id} # POLICY_MOODLEEVENT - all questions correct, sysact: { SysAct(act_type=SysActionType.Inform, slot_values={'positiveFeedback': 'True', 'completedQuiz': 'True'})}")
				return {"sys_acts": [SysAct(act_type=SysActionType.Inform, slot_values={"positiveFeedback": "True", "completedQuiz": "True"})]}
			else:
				# not all questions correct
				self.logger.dialog_turn(f"# USER {user_id} # POLICY_MOODLEEVENT - some questions incorrect, finalgrade: {finalgrade}")
				self.logger.dialog_turn(f"# USER {user_id} # POLICY_MOODLEEVENT - some questions correct, sysact: { SysAct(act_type=SysActionType.Inform, slot_values={'negativeFeedback': 'True', 'finishedQuiz': 'True'})}")
				return {"sys_acts": [SysAct(act_type=SysActionType.Inform, slot_values={"negativeFeedback": "True", "finishedQuiz": "True"})]}
		elif event_name.endswith("event\\course_module_viewed"):
			pass

	def get_weekly_progress(self, user_id: int, courseid: int, last_weekly_summary: MChatbotWeeklySummary):
		# calculate offet from beginning of day and current time
		now_chatbot_time = datetime.now()
		beginning_of_today_chatbot_time = datetime(now_chatbot_time.year, now_chatbot_time.month, now_chatbot_time.day, 0, 0, 0)
		beginning_of_today = beginning_of_today_chatbot_time + timedelta(seconds=self.get_state(user_id, "SERVERTIMEDIFFERENCE"))
		
		last_week_data = []
		last_week_days = []
		best_week_days = []

		prev_week_data = []
		prev_week_days = []

		# iterate over the last 7 days if first week of user, else last 14
		for day in reversed(range((2-int(last_weekly_summary.firstweek))*7)):
			# get day interval for DB query
			start_time = beginning_of_today - timedelta(days=day+1)
			end_time = beginning_of_today - timedelta(days=day)
			# get day name for chart display
			day_name = (now_chatbot_time - timedelta(days=day+1))

			# add module completions and quiz completions together.
			# module completions are divided by 3, because the autocomplete plugin always ensures 3 completions per module
			completed = len(self.get_current_user(user_id).get_viewed_course_modules(session=self.get_session(),
															courseid=courseid,
															include_types=learning_material_types,
															timerange=[start_time, end_time])) / 3 \
								+ len(self.get_current_user(user_id).get_viewed_course_modules(session=self.get_session(),
															courseid=courseid,
															include_types=assignment_material_types,
															timerange=[start_time, end_time]))

			if day < 7:
				last_week_data.append(completed)
				last_week_days.append(day_name)
			else:
				prev_week_data.append(completed)
				prev_week_days.append(day_name)

		best_weekly_days = [last_week_days[i].strftime('%A') for i in range(len(last_week_data)) if last_week_data[i] == max(last_week_data)] if max(last_week_data) > 0 else []
		# shorten week days for stats to 2 letters: strftime('%A')[:2]
		cumulative_weekly_completions = {"y": [sum(last_week_data[:(i+1)]) for i in range(len(last_week_data))], "x": [day.strftime('%A')[:2] for day in last_week_days]}
		cumulative_weekly_completions_prev = None if last_weekly_summary.firstweek else {"y": [sum(prev_week_data[:(i+1)]) for i in range(len(prev_week_data))], "x": [day.strftime('%A')[:2] for day in prev_week_days]}

		# update timestamp of last stat output
		last_weekly_summary.timecreated = self.get_moodle_server_time(user_id)
		last_weekly_summary.firstweek = False
		self.get_session().commit()

		return dict(best_weekly_days=cumulative_weekly_completions,
			  	cumulative_weekly_completions=cumulative_weekly_completions,
				cumulative_weekly_completions_prev=cumulative_weekly_completions_prev)
	
	def get_stat_summary(self, user: MUser, courseid: int):
		# we should show total course progress every 10% of completion

		# calculate current progress percentage
		total_num_quizzes = self.get_session().query(MGradeItem).filter(MGradeItem._courseid==courseid).count()
		done_quizes = user.count_grades(self.get_session(), courseid)
		repeated_quizes = user.count_repeated_grades(self.get_session(), courseid)
		percentage_repeated_quizzes = repeated_quizes / total_num_quizzes

		total_num_modules = len(user.get_all_course_modules(session=self.get_session(), courseid=courseid,
													include_types=learning_material_types))
		done_modules = len(user.get_viewed_course_modules(session=self.get_session(), courseid=courseid,
													include_types=learning_material_types))
		percentage_done = (done_quizes + done_modules) / (total_num_quizzes + total_num_modules)

		return dict(percentage_done=percentage_done,
					percentage_repeated_quizzes=percentage_repeated_quizzes)

	
		
	def choose_greeting(self, user_id: int, courseid: int) -> List[SysAct]:
		self.open_chatbot(user_id)
		user = self.get_current_user(user_id)
		acts = []

		last_weekly_summaries = self.get_session().query(MChatbotWeeklySummary).filter(MChatbotWeeklySummary._userid==user_id)
		first_turn_ever = last_weekly_summaries.count()

		if first_turn_ever == 0:
			# user is seeing chatbot for the first time - show some introduction

			# create first entry for chatbot settings 
			settings = MChatbotSettings(allow_auto_open=True, _userid=user_id)
			# create first entry for weekly summaries
			last_weekly_summary = MChatbotWeeklySummary(_userid=user_id, timecreated=self.get_moodle_server_time(user_id), firstweek=True)
			# create first entry for progress summaries
			progress_summary = MChatbotProgressSummary(_userid=user_id, progress=0.0, timecreated=self.get_moodle_server_time(user_id))
			self.get_session().add_all([last_weekly_summary, progress_summary, settings])
			self.get_session().commit()

			return [SysAct(act_type=SysActionType.Welcome, slot_values={"first_turn": True})]
		
		self.clean_completed_sections_from_recentlyaccessed_items(user_id=user_id, course_id=courseid)

		# Add greeting
		acts.append(SysAct(act_type=SysActionType.Welcome, slot_values={}))

		# check that we haven't displayed the weekly stats in more than 7 days
		last_weekly_summaries = self.get_session().query(MChatbotWeeklySummary).filter(MChatbotWeeklySummary._userid==user_id)
		last_weekly_summary = last_weekly_summaries.first()

		append_suggestions = True
		if self.get_moodle_server_time(user_id) >= last_weekly_summary.timecreated + timedelta(days=7):
			# last time we showed the weekly stats is more than 7 days ago - show again
			slot_values = self.get_weekly_progress(user_id=user_id, courseid=courseid, last_weekly_summary=last_weekly_summary)
			acts.append(SysAct(act_type=SysActionType.DisplayWeeklySummary, slot_values=slot_values))
		else:
			# we should show total course progress every 10% of completion
			last_progress_percentage = user.progress.progress
			slot_values = self.get_stat_summary(user=user, courseid=courseid)

			if slot_values["percentage_done"] >= last_progress_percentage + COURSE_PROGRESS_DISPLAY_PERCENTAGE_INCREMENT:
				# update stat summary to current value
				progress = user.progress
				progress.progress = slot_values["percentage_done"] 
				progress.timecreated = self.get_moodle_server_time(user_id)
				self.get_session().commit()
				acts.append(SysAct(act_type=SysActionType.DisplayProgress, slot_values=slot_values))
				acts.append(SysAct(act_type=SysActionType.RequestReviewOrNext))
				append_suggestions = False
			else:
				# check what user's next closest badge would be
				closest_badge_info = user.get_closest_badge(session=self.get_session(), courseid=courseid)
				if not isinstance(closest_badge_info, type(None)):
					badge, badge_progress, badge_status, open_modules = closest_badge_info
					if badge_progress >= 0.5:
						# only display progress towards next closest batch if user is sufficiently close
						acts.append(SysAct(act_type=SysActionType.DisplayBadgeProgress, slot_values=dict(
							badge_name=badge.name, percentage_done=badge_progress,
							missing_activities=[module.get_content_link(session=self.get_session(), alternative_display_text=module.get_name(self.get_session()))
												for module in open_modules]
						)))
						append_suggestions=False

		if append_suggestions:
			# choose how to proceed
			has_seen_any_course_modules = self.get_session().query(MCourseModulesViewed).join(MCourseModule, MCourseModule.id==MCourseModulesViewed._coursemoduleid) \
										.filter(MCourseModulesViewed._userid==user_id, MCourseModule._course_id==courseid).count() > 0
			if has_seen_any_course_modules:
				# last viewed module
				last_completed_course_modules = user.last_viewed_course_modules(session=self.get_session(), courseid=courseid, completed=True)
				if len(last_completed_course_modules) > 0:
					last_completed_course_module = last_completed_course_modules[0] # sorted ascending by date

					# get open modules across sections, 1 per section
					next_modules = {}
					# prioritize already viewed modules
					last_started_course_modules = user.last_viewed_course_modules(session=self.get_session(), courseid=courseid, completed=False)
					for unfinished_module in last_started_course_modules:
						if not unfinished_module._section_id in next_modules:
							next_modules[unfinished_module._section_id] = unfinished_module
					# fill with other started sections
					for completed_module in last_completed_course_modules:
						if not completed_module._section_id in next_modules:
							# get first open module from this section
							next_module = completed_module.section.get_first_available_module(user=user, session=self.get_session(),
																				include_types=learning_material_types + assignment_material_types,
																				allow_only_unfinished=True)
							if next_module:
								next_modules[completed_module._section_id] = next_module
					next_available_module_links = [module.get_content_link(session=self.get_session(), alternative_display_text=module.section.name) for module in next_modules.values()]

					# user has started, but not completed one or more sections
					acts.append(
							SysAct(act_type=SysActionType.RequestContinueOrNext, slot_values=dict(
									last_viewed_course_module=last_completed_course_module.get_content_link(session=self.get_session(), alternative_display_text=last_completed_course_module.get_name(self.get_session())),
									next_available_modules=next_available_module_links
							)))
				# TODO: Forum post info
				# TODO: Deadline reminder
				else:
					# user has completed all started sections, should get choice of next new and available sections
					available_new_course_sections = user.get_available_new_course_sections(session=self.get_session(), courseid=courseid, current_server_time=self.get_moodle_server_time(user_id))
					acts.append(SysAct(act_type=SysActionType.InformNextOptions, slot_values=dict(
									next_available_sections=[section.get_link() for section in available_new_course_sections]
							)))
			else:
				# TODO return ice cream game
				pass
			
		return acts

	def _handle_request_badge_progress(self, user_id: int, courseid: int) -> SysAct:
		# check what user's next closest badge would be
		closest_badge_info = self.get_current_user(user_id).get_closest_badge(session=self.get_session(), courseid=courseid)
		if not isinstance(closest_badge_info, type(None)):
			badge, badge_progress, badge_status, open_modules = closest_badge_info
			if badge_status != BadgeCompletionStatus.INCOMPLETE and badge_progress >= 0.5:
				# only display progress towards next closest batch if user is sufficiently close
				return SysAct(act_type=SysActionType.DisplayBadgeProgress, slot_values=dict(
					badge_name=badge.name, percentage_done=badge_progress,
					missing_activities=[module.get_content_link(session=self.get_session(), alternative_display_text=module.get_name(self.get_session()))
										for module in open_modules]
				))
		else: 
			# all badges aAre already completed
			return SysAct(act_type=SysActionType.DisplayBadgeProgress, slot_values=dict(
				badge_name=None, percentage_done=None, missing_activities=None
			))

	def congratulate_badge_issued(self, user_id: int, badge_id: int, contextid: int) -> SysAct:
		self.open_chatbot(user_id=user_id)
		# find badge
		badge = self.get_session().query(MBadge).get(badge_id)
		# get badge image link
		return SysAct(act_type=SysActionType.CongratulateBadge,
			slot_values=dict(badge_name=badge.name,
					badge_img_url=f'<img src="{config.MOODLE_SERVER_URL}/pluginfile.php/{contextid}/badges/badgeimage/{badge.id}/f1" alt="{badge.name}"/>')
		)
	
	def display_quiz(self, user_id: int, coursemoduleid: int) -> SysAct:
		quiz = self.get_session().query(MCourseModule).get(coursemoduleid)
		hvp_params = quiz.get_h5p_parameters(self.get_session())
		self.resize_chatbot(user_id=user_id, size=ChatbotWindowSize.LARGE)
		return SysAct(act_type=SysActionType.DisplayQuiz, slot_values=dict(**hvp_params))

	@PublishSubscribe(sub_topics=["user_acts", "beliefstate", "courseid"], pub_topics=["sys_acts", "sys_state", "html_content"])
	def choose_sys_act(self, user_id: str, user_acts: List[UserAct], beliefstate: dict, courseid: int) -> dict(sys_act=SysAct,html_content=str):
		"""
			Responsible for walking the policy through a single turn. Uses the current user
			action and system belief state to determine what the next system action should be.

			To implement an alternate policy, this method may need to be overwritten

			Args:
				belief_state (BeliefState): a BeliefState obejct representing current system
										   knowledge

			Returns:
				(dict): a dictionary with the key "sys_acts" and the value that of the systems next
						action

		"""
		#print("USER ACTS\n", user_acts)

		# update the turn count
		turns = self.get_state(user_id, TURNS) + 1
		self.set_state(user_id, TURNS, turns)

		
		
		# go through the user acts 
		sys_state = {}
		if self.get_state(user_id, FIRST_TURN):
			# print first turn message
			self.set_state(user_id, FIRST_TURN, False)
			sys_acts = self.choose_greeting(user_id, courseid)
			sys_state["last_act"] = sys_acts
			for sys_act in sys_acts:
				self.logger.dialog_turn(f"# USER {user_id} # POLICY - {sys_act}")
			return {'sys_acts': sys_acts, "sys_state": sys_state}
		# after first turn
		sys_acts = []
		for user_act in user_acts:
			if user_act.type == UserActionType.RequestReview:
				if len(self.get_state(user_id=user_id, attribute_name=REVIEW_QUIZZES)) > 0:
					next_quiz = self.get_state(user_id=user_id, attribute_name=REVIEW_QUIZZES).pop()
					self.set_state(user_id, REVIEW_QUIZZES, self.get_state(user_id, REVIEW_QUIZZES)[1:])
					sys_acts.append(SysAct(act_type=SysActionType.DisplayQuiz, slot_values={"quiz_embed": next_quiz}))
			elif user_act.type == UserActionType.RequestNextSection:
				self.set_state(user_id, REVIEW_QUIZZES, [])
				user = self.get_current_user(user_id)
				available_new_course_sections = user.get_available_new_course_sections(session=self.get_session(), courseid=courseid, current_server_time=self.get_moodle_server_time(user_id))
				sys_acts.append(SysAct(act_type=SysActionType.InformNextOptions, slot_values=dict(
								next_available_sections=[section.get_link() for section in available_new_course_sections]
						)))
			elif user_act.type == UserActionType.RequestProgress:
				slot_values = self.get_stat_summary(user=self.get_current_user(user_id), courseid=courseid)
				sys_acts.append(SysAct(act_type=SysActionType.DisplayProgress, slot_values=slot_values))
			elif user_act.type == UserActionType.RequestBadgeProgress:
				sys_acts.append(self._handle_request_badge_progress(user_id=user_id, courseid=courseid))

			
			# elif user_act.slot and 'LoadMoreSearchResults' in user_act.slot:
			# 	# load more search results
			# 	# get the last search term and counter (from the nlu)
			# 	search_term = self.get_state(user_id, LAST_SEARCH)
			# 	counter = int(user_act.slot.split(":")[-1])
			# 	book_links = get_book_links(wstoken=self.get_state(user_id, 'SLIDEFINDERTOKEN'), course_id=courseid, searchTerm=search_term, word_context_length=5, start=counter, end=counter + 3)
			# 	if book_links:
			# 		book_link_str = "<br />".join(f'<br /> - <a href="{book_links[name][1]}">{name}</a> {book_links[name][0]}' for name in book_links)
			# 		book_link_str = book_link_str + "<br /><br />"
			# 	else:
			# 		book_link_str = "End"
			# 	sys_act = SysAct(act_type=SysActionType.Inform, slot_values={"modulContent": "modulContent", "link": book_link_str})

			# elif user_act.slot == 'SearchForContent' or user_act.slot == 'SearchForDefinition':
			# 	reg = "(Woher hätte ich die Antwort auf (?P<content1>.*) (kennen|wissen) sollen(\?)?|Woher hätte ich wissen sollen, was mit (?P<content2>.*) gemeint ist(\?)?|Wo finde ich (?<!neue)((et)?was|Info(s|rmation(en)?)? )?(über(s| das| die| den)? (Thema )?|zu(m)? (Thema )?)?(?P<content3>.*)(\?)?|Wo steht ((et)?was )?(über(s| das| die| den)? (Thema )?|zu(m)? (Thema )?)?(?P<content6>.*)(\?)?|Wo kann ich Info(s|rmation(en)?)? (über(s| das| die| den)? (Thema )?|zu(m)? (Thema )?)?(?P<content4>.*) finden(\?)?|Was war (nochmal )?mit (?P<content9>.*) gemeint(\?)?|Was ist (nochmal )?mit (?P<content5>.*) gemeint(\?)?|Wo wird (das Thema |etwas zum Thema |der Bergiff )?(?P<content10>.*) erklärt(\?)?)"
			# 	matches = re.match(reg, user_act.text, re.I)
			# 	if matches:
			# 		matches = matches.groupdict()
			# 		for key in matches.keys():
			# 			if key.startswith("content") and matches.get(key):
			# 				search_term = matches.get(key)
					
			# 		self.set_state(user_id, LAST_SEARCH, search_term)
			# 		book_links = get_book_links(wstoken=self.get_state(user_id, 'SLIDEFINDERTOKEN'), course_id=courseid, searchTerm=search_term, word_context_length=5, start=0, end=3)
			# 		if book_links:
			# 			book_link_str = "<br />".join(f'<br /> - <a href="{book_links[name][1]}">{name}</a> {book_links[name][0]}' for name in book_links)
			# 			book_link_str = book_link_str + "<br /><br />"
			# 		else:
			# 			book_link_str = "None"
			# 		sys_act = SysAct(act_type=SysActionType.Inform, slot_values={"modulContent": "modulContent", "link": book_link_str})
			# 	else:
			# 		# Nicht erkannt -> nachfragen!
			# 		sys_act = SysAct(act_type=SysActionType.Request, slot_values={"modulContent": "modulContent"})
			
			# elif user_act.slot == 'SearchTerm':
			# 	# system asked for only the search term -> utterance is the search term
			# 	search_term = user_act.text
			# 	self.set_state(user_id, LAST_SEARCH, search_term)
			# 	book_links = get_book_links(wstoken=self.get_state(user_id, 'SLIDEFINDERTOKEN'), course_id=courseid, searchTerm=search_term, word_context_length=5, start=0, end=3)
			# 	if book_links:
			# 		book_link_str = "<br />".join(f'<br /> - <a href="{book_links[name][1]}">{name}</a> {book_links[name][0]}' for name in book_links)
			# 		book_link_str = book_link_str + "<br /><br />"
			# 	else:
			# 		book_link_str = "End"
			# 	sys_act = SysAct(act_type=SysActionType.Inform, slot_values={"modulContent": "modulContent", "link": book_link_str})
			
		sys_state["last_act"] = sys_acts
		self.logger.dialog_turn(f"# USER {user_id} # POLICY - {sys_acts}")
		return {'sys_acts':  sys_acts, "sys_state": sys_state}
	
	def get_current_user(self, user_id) -> MUser:
			""" Get Moodle user by id from Chat Interface (or start run_chat with --user_id=...) """
			user = self.get_session().get(MUser, int(user_id))
			return user
	
	def get_user_next_module(self, user_id, courseid):
		# while loop ends in infinite loop if all courses are completed
		# Wie werden "Lücken" oder andere Reihenfolgen behandelt?

		user = self.get_current_user(user_id)
		last_completed: MCourseModule = user.get_last_completed_coursemodule(self.get_session(), courseid, self.get_moodle_server_time(user_id))
		self.set_state(user_id, LAST_ACCESSED_COURSEMODULE, last_completed)

		if not last_completed:
			# new user - no completed modules so far
			next_module = user.get_available_course_modules(self.get_session(), courseid=courseid, current_server_time=self.get_moodle_server_time(user_id))[0]
			self.set_state(user_id, NEXT_SUGGESTED_COURSEMODULE, next_module)
			return next_module.get_name(self.get_session()), next_module.id

		# existing user, already completed some content
		next_module: MCourseModule = last_completed.section.get_next_available_module(last_completed, self.get_current_user(user_id), self.get_session())

		# muss hier oder in get_next_available_module getestet werden ob nächstes modul nicht schon abgeschlossen ist
		# Was ist mit nicht "abschliessbaren" modules?

		if next_module:
			self.set_state(user_id, NEXT_SUGGESTED_COURSEMODULE, next_module)
			return next_module.get_name(self.get_session()), next_module.id

		# next course module in section of last completed module is not available - choose available one from other section
		# next_module = user.get_available_course_modules(self.get_session())[0]
		# print("EXISTING USER -> SECTION COMPLETE -> ", next_module.get_name(self.get_session()), next_module.get_type_name(self.get_session()))
		next_sections = user.get_incomplete_available_course_sections(self.get_session(), courseid, self.get_moodle_server_time(user_id)) # Problem: gibt schon abgeschlossenen wieder
		if next_sections:
			next_section: MCourseSection = next_sections[0]
			next_module: MCourseModule = next_section.get_next_available_module(currentModule=None, user=self.get_current_user(user_id), session=self.get_session())

			if not next_module:
				return "Kein verfügbares Modul gefunden", -1
		self.set_state(user_id, NEXT_SUGGESTED_COURSEMODULE, next_module)
		return next_module.get_name(self.get_session()), next_module.id

	def get_repeatable_modul_sys_act(self, user_id, courseid):
		"""
			Get a (random) module to repeat. 3 different types:
			- finished (and completed) modules -> quiz
			- insufficient modules (grade < 60%) -> hvp
			- open modules (not finished) -> "continue"
		"""
		two_weeks_ago = datetime.datetime.now() - datetime.timedelta(weeks=2)
		finished_modules = self.get_modules(since_date=two_weeks_ago, is_finished=True, user_id=user_id, courseid=courseid)
		grades = self.get_current_user(user_id).get_grades(self.get_session(), course_id=courseid) # get user grades
		insufficient_modules = [grade for grade in grades if
				grade.finalgrade and grade.finalgrade < (grade.rawgrademax * decimal.Decimal(0.6))] # threshold 60%

		open_modules = self.get_modules(since_date=two_weeks_ago, is_finished=False, user_id=user_id, courseid=courseid)
		
		repeat_content_choices = []
		if len(finished_modules) > 0:
			repeat_content_choices.append("finished")
		if len(insufficient_modules) > 0:
			repeat_content_choices.append("insufficient")
		if len(open_modules) > 0:
			repeat_content_choices.append("open")

		if len(repeat_content_choices) == 0:
			# no content to repeat
			self.set_state(user_id, MODE, 'new')
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"moduleName": "moduleName", "repeatContent": "noContent", "link":"-"})
		
		repeatContent = random.choice(repeat_content_choices)
		if repeatContent == "finished":
			self.set_state(user_id, MODE, 'quiz')
			moduleName = random.choice(finished_modules)
		if repeatContent == "insufficient":
			instanceId = random.choice(insufficient_modules).get_grade_item(self.get_session()).iteminstance
			quizModuleId = self.get_session().query(MModule).filter(MModule.name=='hvp').first().id
			moduleName = self.get_session().query(MCourseModule).filter(MCourseModule.instance==instanceId, MCourseModule._type_id==quizModuleId).first()
		if repeatContent == "open":
			moduleName = random.choice(finished_modules)
		
		link = self.get_session().query(MCourseModule).filter(MCourseModule.id == moduleName.id).one().get_content_link(self.get_session())
		
		contentType = moduleName.get_type_name(self.get_session())
		return SysAct(act_type=SysActionType.Inform,
					  slot_values={"moduleName": moduleName.section.name, "repeatContent": repeatContent, "link": link,
								   "contentType": contentType if contentType in ["resource", "hvs", "quiz", "book"] else "else"})

	def get_modules(self, since_date, is_finished, user_id, courseid) -> List[MCourseModule]:
			"""
				get all modules where last_modified by current user is older than 'since_date' and
				current user has finished module equals 'is_finished'
			"""
			user = self.get_current_user(user_id)
			if is_finished:
				courses = user.get_completed_course_modules_before_date(since_date, self.get_session(), courseid)
			else:
				courses = user.get_not_finished_courses_before_date(since_date, self.get_session(), courseid)
			return [course for course in courses]

	def total_open_modules(self, user_id, courseid):
		user = self.get_current_user(user_id)
		return len(user.get_incomplete_available_course_modules(self.get_session(), courseid=courseid, current_server_time=self.get_moodle_server_time(user_id)))

	def total_completed_modules(self, user_id, courseid):
		user = self.get_current_user(user_id)
		return len(user.get_completed_course_modules(self.get_session(), courseid=courseid))

	def convert_time_to_minutes(self, sentence):
		time_units = {"minute": 1, "minuten": 1, "stunde": 60, "stunden": 60,}
		
		spelled_numbers = {"eine": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5, 
		     			"sechs": 6,"sieben": 7, "acht": 8, "neun": 9, "zehn": 10,}
		
		spelled_special = {"eine halbe": 30, "eine viertel": 15, "eine dreiviertel": 45,}
		
		pattern = r"\b(eine halbe|eine viertel|eine dreiviertel|\b(?:eine|zwei|drei|vier|fünf|sechs|sieben|acht|neun|zehn)\b|\d+)\s*(minute|minuten|stunde|stunden)?\b"
		matches = re.findall(pattern, sentence, re.IGNORECASE)

		total_minutes = 0
		
		for match in matches:
			number = match[0].lower()
			unit_spelled = match[1].lower() if match[1] else None

			found_special = False
			for word in match:
				word = word.lower()
				if word in spelled_special:
					total_minutes += spelled_special[word]
					found_special = True
					break
			
			if found_special:
				continue
			unit = 1		

			if unit_spelled:
				if unit_spelled in time_units:
					unit = time_units[unit_spelled]
			
			if number in spelled_numbers:
				quantity = spelled_numbers[number]
			else:
				quantity = int(number)
			
			total_minutes += quantity * unit		
		
		return total_minutes