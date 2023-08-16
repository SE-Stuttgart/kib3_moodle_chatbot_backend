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
import datetime
import decimal
import random
from operator import attrgetter
import re
import traceback
from typing import List, Tuple

import httplib2
import urllib

from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import next_value
from sqlalchemy.sql.sqltypes import DateTime
from config import MOODLE_SERVER_ADDR

from elearning.booksearch import get_book_links
from services.service import PublishSubscribe
from services.service import Service
from utils import SysAct, SysActionType
from utils.beliefstate import BeliefState
from utils.domain.jsonlookupdomain import JSONLookupDomain
from utils.logger import DiasysLogger
from utils import UserAct
from elearning.moodledb import MAssign, MAssignSubmission, MCourse, MCourseModulesCompletion, MCourseSection, MGradeGrade, MGradeItem, connect_to_moodle_db, Base, MUser, MCourseModule, \
	get_time_estimate_module, get_time_estimates, MModule
from utils.useract import UserActionType, UserAct


LAST_ACCESSED_COURSEMODULE = 'last_accessed_coursemodule'
NEXT_SUGGESTED_COURSEMODULE = 'next_suggested_coursemodule'
COURSE_MODULE_ID = 'course_module_id'
ASSIGN_ID = 'assign_id'
TURNS = 'turns'
LAST_USER_ACT = 'last_act'
FIRST_TURN = 'first_turn'
CURRENT_SUGGESTIONS = 'current_suggestions'
MODE = 'mode'
S_INDEX = 's_index'
LAST_SEARCH = 'last_search'

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
		engine, conn = connect_to_moodle_db()
		self.Session = sessionmaker()
		self.Session.configure(bind=engine)
		self.session = self.Session()
		Base.metadata.create_all(engine)

	def dialog_start(self, user_id: str):
		"""
			resets the policy after each dialog
		"""
		if not self.get_state(user_id, TURNS):
			self.set_state(user_id, LAST_USER_ACT, None)
			self.set_state(user_id, TURNS, 0)
			self.set_state(user_id, FIRST_TURN, True)
			self.set_state(user_id, LAST_SEARCH, {})
			self.set_state(user_id, CURRENT_SUGGESTIONS, []) # list of current suggestions
			self.set_state(user_id, S_INDEX, 0)  # the index in current suggestions for the current system reccomendation

	@PublishSubscribe(sub_topics=["moodle_event"], pub_topics=["sys_act", "sys_state", "html_content"])
	def moodle_event(self, user_id: int, moodle_event: dict) -> dict(sys_act=SysAct, sys_state=SysAct, html_content=str):
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
		print("=================")

		if event_name == """\\core\\event\\user_graded""":
			# extract grade info
			gradeItem: MGradeItem = self.session.query(MGradeItem).get(int(moodle_event['other']['itemid']))
			# gradeItem: MGradeItem = grade.get_grade_item(self.session)
			finalgrade = float(moodle_event['other']['finalgrade'])
			if finalgrade == gradeItem.grademax:
				# all questions correct
				self.logger.dialog_turn(f"# USER {user_id} # POLICY_MOODLEEVENT - all questions correct, finalgrade: {finalgrade}")
				self.logger.dialog_turn(f"# USER {user_id} # POLICY_MOODLEEVENT - all questions correct, sysact: { SysAct(act_type=SysActionType.Inform, slot_values={'positiveFeedback': 'True', 'completedQuiz': 'True'})}")
				return {"sys_act": SysAct(act_type=SysActionType.Inform, slot_values={"positiveFeedback": "True", "completedQuiz": "True"})}
			else:
				# not all questions correct
				self.logger.dialog_turn(f"# USER {user_id} # POLICY_MOODLEEVENT - some questions incorrect, finalgrade: {finalgrade}")
				self.logger.dialog_turn(f"# USER {user_id} # POLICY_MOODLEEVENT - some questions correct, sysact: { SysAct(act_type=SysActionType.Inform, slot_values={'negativeFeedback': 'True', 'finishedQuiz': 'True'})}")
				return {"sys_act": SysAct(act_type=SysActionType.Inform, slot_values={"negativeFeedback": "True", "finishedQuiz": "True"})}

	@PublishSubscribe(sub_topics=["user_acts", "beliefstate", "courseid"], pub_topics=["sys_act", "sys_state", "html_content"])
	def choose_sys_act(self, user_id: str, user_acts: List[UserAct], beliefstate: dict, courseid: int) -> dict(sys_act=SysAct,html_content=str):
		"""
			Responsible for walking the policy through a single turn. Uses the current user
			action and system belief state to determine what the next system action should be.

			To implement an alternate policy, this method may need to be overwritten

			Args:
				belief_state (BeliefState): a BeliefState obejct representing current system
										   knowledge

			Returns:
				(dict): a dictionary with the key "sys_act" and the value that of the systems next
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
			sys_act = SysAct(act_type=SysActionType.Inform,
					  slot_values={"welcomeMsg": "repeat", "daysToSubmission": "empty"})
			sys_state["last_act"] = sys_act
			self.logger.dialog_turn(f"# USER {user_id} # POLICY - {sys_act}")
			return {'sys_act': sys_act, "sys_state": sys_state}
		# after first turn
		for user_act in user_acts:
			if user_act is not None:
				if user_act.slot == 'InformTimeConstraint':
					# What can I learn in 5 minutes?...

					# search for the number of minutes in the user act
					regex = r"\d+"
					matches = re.search(regex, user_act.text, re.MULTILINE | re.IGNORECASE)
					
					if matches:
						# find the right module for this time constraint
						incomplete_modules_with_time_est = get_time_estimates(self.session, self.get_current_user(user_id), courseid=courseid)

						module_names = [module for module, time in incomplete_modules_with_time_est if time and time <= int(matches[0])]
						hasModule = len(module_names) > 0
						link = ""
						# create link
						if hasModule:
							link = module_names[0].get_content_link(self.session)
							sys_act = SysAct(act_type=SysActionType.Inform,
										slot_values={"moduleName": link, "hasModule": "true" if hasModule else "false"})
						else:
							sys_act = SysAct(act_type=SysActionType.Inform,
										slot_values={"moduleName": None, "hasModule": "true" if hasModule else "false"})

					# if no time is found, return an ask for the time specifically
					# not in nlg yet
					# set last act
					else:
						self.set_state(user_id, LAST_USER_ACT, user_act)
						
						sys_act = SysAct(act_type=SysActionType.Request,
						slot_values={"learningTime": "empty"})
						#sys_act = SysAct(act_type=SysActionType.Bad)
				
				elif user_act.slot and 'LoadMoreSearchResults' in user_act.slot:
					# load more search results
					# get the last search term and counter (from the nlu)
					search_term = self.get_state(user_id, LAST_SEARCH)
					counter = int(user_act.slot.split(":")[-1])
					book_links = get_book_links(course_id=courseid, searchTerm=search_term, word_context_length=5, start=counter, end=counter + 3)
					if book_links:
						book_link_str = "<br />".join(f'<br /> - <a href="{link}">{book_links[link][0]}</a> {book_links[link][1]}' for link in book_links)
					else:
						book_link_str = "End"
					sys_act = SysAct(act_type=SysActionType.Inform, slot_values={"modulContent": "modulContent", "link": book_link_str})


				elif user_act.slot == 'Greet':
					# repeat welcome message
					sys_act = SysAct(act_type=SysActionType.Inform,
					  slot_values={"welcomeMsg": "repeat", "daysToSubmission": "empty"})
					
				elif user_act.slot == 'SearchForContent' or user_act.slot == 'SearchForDefinition':
					reg = "(Woher hätte ich die Antwort auf (?P<content1>.*) (kennen|wissen) sollen(\?)?|Woher hätte ich wissen sollen, was mit (?P<content2>.*) gemeint ist(\?)?|Wo finde ich (?<!neue)((et)?was|Info(s|rmation(en)?)? )?(über(s| das| die| den)? (Thema )?|zu(m)? (Thema )?)?(?P<content3>.*)(\?)?|Wo steht ((et)?was )?(über(s| das| die| den)? (Thema )?|zu(m)? (Thema )?)?(?P<content6>.*)(\?)?|Wo kann ich Info(s|rmation(en)?)? (über(s| das| die| den)? (Thema )?|zu(m)? (Thema )?)?(?P<content4>.*) finden(\?)?|Was war (nochmal )?mit (?P<content9>.*) gemeint(\?)?|Was ist (nochmal )?mit (?P<content5>.*) gemeint(\?)?|Wo wird (das Thema |etwas zum Thema |der Bergiff )?(?P<content10>.*) erklärt(\?)?)"
					matches = re.match(reg, user_act.text, re.I)
					if matches:
						matches = matches.groupdict()
						for key in matches.keys():
							if key.startswith("content") and matches.get(key):
								search_term = matches.get(key)
						
						self.set_state(user_id, LAST_SEARCH, search_term)
						book_links = get_book_links(course_id=courseid, searchTerm=search_term, word_context_length=5, start=0, end=3)
						if book_links:
							book_link_str = "<br />".join(f'<br /> - <a href="{link}">{book_links[link][0]}</a> {book_links[link][1]}' for link in book_links)
							book_link_str = book_link_str + "<br /><br />"
						else:
							book_link_str = "None"
						sys_act = SysAct(act_type=SysActionType.Request, slot_values={"modulContent": "modulContent"})
					else:
						# Nicht erkannt -> nachfragen!
						sys_act = SysAct(act_type=SysActionType.Request, slot_values={"modulContent": "modulContent"})
				
				elif user_act.slot == 'SearchTerm':
					# system asked for only the search term -> utterance is the search term
					search_term = user_act.text
					self.set_state(user_id, LAST_SEARCH, search_term)
					book_links = get_book_links(course_id=courseid, searchTerm=search_term, word_context_length=5, start=0, end=3)
					if book_links:
						book_link_str = "<br />".join(f'<br /> - <a href="{link}">{book_links[link][0]}</a> {book_links[link][1]}' for link in book_links)
					else:
						book_link_str = "End"
					sys_act = SysAct(act_type=SysActionType.Inform, slot_values={"modulContent": "modulContent", "link": book_link_str})

				
				elif user_act.slot == 'No':
					# TODO: does this need to be here or only as follow up to a question?
					sys_act =  SysAct(act_type=SysActionType.Bad)
				
				elif user_act.slot == 'Yes':
					# Same as above
					sys_act =  SysAct(act_type=SysActionType.Bad)

				elif user_act.slot == 'InformCompletionGoal':
					# TODO: implement
					sys_act =  SysAct(act_type=SysActionType.Bad)
				
				elif user_act.slot == 'GetNextModule':
					# TODO: old complicated -> adapt?
					[_, next_module_id] = self.get_user_next_module(user_id, courseid)
					next_module = self.session.query(MCourseModule).filter(MCourseModule.id == next_module_id).one()
					module_link = next_module.get_content_link(self.session)
					self.set_state(user_id, COURSE_MODULE_ID, next_module.id)
					sys_act = SysAct(act_type=SysActionType.Inform,
						  slot_values={"nextModule": "", "moduleName": module_link})
					
				elif user_act.slot == 'GetProgress':
					open_modules = self.total_open_modules(user_id, courseid)
					completed_modules = self.total_completed_modules(user_id, courseid)
					if completed_modules > 0:
						sys_act = SysAct(act_type=SysActionType.Inform,
									slot_values={"motivational": f"{completed_modules} von {open_modules + completed_modules}", "taskLeft": str(open_modules)})
					else:
						sys_act = SysAct(act_type=SysActionType.Inform,
									slot_values={"NoMotivational": f"{completed_modules} von {open_modules + completed_modules}", "taskLeft": str(open_modules)})
		
				elif user_act.slot == 'RequestTest':	
					# TODO can this be simplified? why positive feedback?
					nextStep = random.choice(["test", "repeatQuiz"])
					if nextStep == "test":
						sys_act = SysAct(act_type=SysActionType.Inform,
									slot_values={"positiveFeedback": "cool", "test": "true"})
					elif nextStep == "repeatQuiz":
						sys_act = SysAct(act_type=SysActionType.Inform,
									slot_values={"positiveFeedback": "cool", "repeatQuiz": "true"})

				elif user_act.slot == 'SuggestImprovement': 
					sys_act = SysAct(act_type=SysActionType.Inform,
						  slot_values={"suggestion": random.choice(["quiz", "learningTime", "offerHelp"]),
									   "offerhelp": "content"})
	
				elif user_act.slot == 'SuggestRepetition':
					# TODO: complicated -> adapt
					sys_act = self.get_repeatable_modul_sys_act(user_id, courseid)
				
				elif user_act.type == UserActionType.Thanks:
					sys_act = SysAct(act_type=SysActionType.RequestMore,
						  slot_values={"moduleContent": "x"})
				
				elif user_act.slot == 'ChangeConfig':
					# TODO: implement
					sys_act = SysAct(act_type=SysActionType.Bad)
				
				elif user_act.type == UserActionType.Bye:
					sys_act = SysAct(act_type=SysActionType.Bye)
				
				elif user_act.slot == 'Help':
					sys_act = SysAct(act_type=SysActionType.Inform,
						  slot_values={"help":"x"})
				
				else:
					print("Unknown user act: ", user_act)
					sys_act = SysAct(act_type=SysActionType.Bad)
			else:
				sys_act = SysAct(act_type=SysActionType.Bad)
			
		sys_state["last_act"] = sys_act
		self.logger.dialog_turn(f"# USER {user_id} # POLICY - {sys_act}")
		return {'sys_act': sys_act, "sys_state": sys_state}
	
	def get_current_user(self, user_id) -> MUser:
			""" Get Moodle user by id from Chat Interface (or start run_chat with --user_id=...) """
			user = self.session.query(MUser).get(int(user_id))
			return user
	
	def get_user_next_module(self, user_id, courseid):
		# while loop ends in infinite loop if all courses are completed
		# Wie werden "Lücken" oder andere Reihenfolgen behandelt?

		user = self.get_current_user(user_id)
		last_completed: MCourseModule = user.get_last_completed_coursemodule(self.session, courseid)
		self.set_state(user_id, LAST_ACCESSED_COURSEMODULE, last_completed)

		if not last_completed:
			# new user - no completed modules so far
			next_module = user.get_available_course_modules(self.session, courseid=courseid)[0]
			self.set_state(user_id, NEXT_SUGGESTED_COURSEMODULE, next_module)
			return next_module.get_name(self.session), next_module.id

		# existing user, already completed some content
		next_module: MCourseModule = last_completed.section.get_next_available_module(last_completed, self.get_current_user(user_id), self.session)

		# muss hier oder in get_next_available_module getestet werden ob nächstes modul nicht schon abgeschlossen ist
		# Was ist mit nicht "abschliessbaren" modules?

		if next_module:
			self.set_state(user_id, NEXT_SUGGESTED_COURSEMODULE, next_module)
			return next_module.get_name(self.session), next_module.id

		# next course module in section of last completed module is not available - choose available one from other section
		# next_module = user.get_available_course_modules(self.session)[0]
		# print("EXISTING USER -> SECTION COMPLETE -> ", next_module.get_name(self.session), next_module.get_type_name(self.session))
		next_sections = user.get_incomplete_available_course_sections(self.session, courseid) # Problem: gibt schon abgeschlossenen wieder
		if next_sections:
			next_section: MCourseSection = next_sections[0]
			next_module: MCourseModule = next_section.get_next_available_module(currentModule=None, user=self.get_current_user(user_id), session=self.session)

			if not next_module:
				return "Kein verfügbares Modul gefunden", -1
		self.set_state(user_id, NEXT_SUGGESTED_COURSEMODULE, next_module)
		return next_module.get_name(self.session), next_module.id

	def get_repeatable_modul_sys_act(self, user_id, courseid):
		"""
			Get a (random) module to repeat. 3 different types:
			- finished (and completed) modules -> quiz
			- insufficient modules (grade < 60%) -> hvp
			- open modules (not finished) -> "continue"
		"""
		two_weeks_ago = datetime.datetime.now() - datetime.timedelta(weeks=2)
		finished_modules = self.get_modules(since_date=two_weeks_ago, is_finished=True, user_id=user_id, courseid=courseid)
		grades = self.get_current_user(user_id).get_grades(self.session, course_id=courseid) # get user grades
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
			instanceId = random.choice(insufficient_modules).get_grade_item(self.session).iteminstance
			quizModuleId = self.session.query(MModule).filter(MModule.name=='hvp').first().id
			moduleName = self.session.query(MCourseModule).filter(MCourseModule.instance==instanceId, MCourseModule._type_id==quizModuleId).first()
		if repeatContent == "open":
			moduleName = random.choice(finished_modules)
		
		link = self.session.query(MCourseModule).filter(MCourseModule.id == moduleName.id).one().get_content_link(self.session)
		
		contentType = moduleName.get_type_name(self.session)
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
				courses = user.get_completed_courses_before_date(since_date, self.session, courseid)
			else:
				courses = user.get_not_finished_courses_before_date(since_date, self.session, courseid)
			return [course for course in courses]

	def total_open_modules(self, user_id, courseid):
		user = self.get_current_user(user_id)
		return len(user.get_incomplete_available_course_modules(self.session, courseid=courseid))

	def total_completed_modules(self, user_id, courseid):
		user = self.get_current_user(user_id)
		return len(user.get_completed_courses(self.session, courseid=courseid))
