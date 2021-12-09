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
from re import L
from typing import List, Tuple

from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.sqltypes import DateTime

from services.service import PublishSubscribe
from services.service import Service
from utils import SysAct, SysActionType
from utils.beliefstate import BeliefState
from utils.domain.jsonlookupdomain import JSONLookupDomain
from utils.logger import DiasysLogger
from utils import UserAct
from elearning.moodledb import MAssignSubmission, connect_to_moodle_db, Base, MUser, MCourseModule, \
	get_time_estimate_module, get_time_estimates, MModule
from utils.useract import UserActionType


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
		self.first_turn = True
		Service.__init__(self, domain=domain)
		self.current_suggestions = []  # list of current suggestions
		self.s_index = 0  # the index in current suggestions for the current system reccomendation
		self.domain_key = domain.get_primary_key()
		self.logger = logger
		self.max_turns = max_turns
		engine, conn = connect_to_moodle_db()
		self.Session = sessionmaker()
		self.Session.configure(bind=engine)
		self.state = dict()
		self.session = self.Session()
		Base.metadata.create_all(engine)

	def dialog_start(self, user_id: str):
		"""
			resets the policy after each dialog
		"""
		self.turns = 0
		self.first_turn = True
		self.current_suggestions = []  # list of current suggestions
		self.s_index = 0  # the index in current suggestions for the current system reccomendation

	@PublishSubscribe(sub_topics=["user_acts", "beliefstate"], pub_topics=["sys_act", "sys_state", "html_content"])
	def choose_sys_act(self, user_id: str, beliefstate: dict, user_acts: List[UserAct]) -> dict(sys_act=SysAct,html_content=str):
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
		print(user_acts)


		self.turns += 1
		# do nothing on the first turn --LV
		sys_state = {}
		if self.first_turn:
			self.first_turn = False
			sys_act = self.start_msg(user_id)
			sys_state["last_act"] = sys_act
			return {'sys_act': sys_act, "sys_state": sys_state}
		for act in user_acts:
			sys_act = self.get_sys_act(act, user_id)
			if sys_act:
				sys_state["last_act"] = sys_act
				result = {"sys_act": sys_act, "sys_state": sys_state}
				for slot in sys_act.slot_values:
					if slot == "quiz_links":
						# we have a link - add html embed code to display quiz inline in chat
						result["html_content"] = sys_act.slot_values[slot]
				return result
		return {"sys_act": SysAct(act_type=SysActionType.Bad), "sys_state": sys_state}

	def get_current_user(self, userid) -> MUser:
		user = self.session.query(MUser).filter(MUser.id==userid).first()
		print("USER:", user.username)
		return user

	def get_repeatable_modul_sys_act(self, userid):
		two_weeks_ago = datetime.datetime.now() - datetime.timedelta(weeks=6)
		old_finished_modules = self.get_modules(since_date=two_weeks_ago, is_finished=True, userid=userid)
		insufficient_modules = self.get_modules_by_grade(grade_threshold=0.6, userid=userid)
		open_modules = self.get_modules(since_date=two_weeks_ago, is_finished=False, userid=userid)
		repeat_content_choices = []
		if len(old_finished_modules) > 0:
			repeat_content_choices.append("quiz")
		if len(insufficient_modules) > 0:
			repeat_content_choices.append("module")
		if len(open_modules) > 0:
			repeat_content_choices.append("oldcontent")

		if len(repeat_content_choices) == 0:
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"moduleName": "moduleName", "repeatContent": "noContent"})
		repeatContent = random.choice(repeat_content_choices)
		if repeatContent == "quiz":
			moduleName = random.choice(old_finished_modules)
		if repeatContent == "module":
			# TODO try/catch block or check for none, could return None!
			moduleName = random.choice(insufficient_modules).get_grade_item(self.session)._courseid
		if repeatContent == "oldcontent":
			moduleName = random.choice(old_finished_modules)
		return SysAct(act_type=SysActionType.Inform,
					  slot_values={"moduleName": moduleName, "repeatContent": repeatContent})

	def get_submission_sys_act(self, userid):
		"""
		Return the next upcoming incomplete submission
		"""
		# Beispiel Use Cases:
		# Wann ist die erste Abgabe?
		user = self.get_current_user(userid)
		next_submission = None
		due_date = None
		submission_name = None

		new_assignments = self.session.query(MAssignSubmission).filter(MAssignSubmission._user_id==user.id, MAssignSubmission.status=="new").all()
		for assign in new_assignments:
			if not next_submission or assign.assignment.duedate < due_date:
				next_submission = assign
				due_date = next_submission.assignment.duedate
				submission_name = next_submission.assignment.name

		if next_submission:
			# offenes assignment gefunden: suche course module heraus
			course_module_section = self.session.query(MCourseModule).filter(MCourseModule.instance==next_submission.assignment.id).all()[0].section
			course_module_name = course_module_section.name
			due_date = due_date.strftime("%d.%m.%y, %H:%M:%S")
		else: 
			# kein offenes assignment gefunden
			course_module_name = "kein Modul"
			due_date = "-"
			submission_name = "kein Assignment"

		return SysAct(act_type=SysActionType.Inform,
					  slot_values={"moduleName": course_module_name, "submission": due_date})

	def get_new_goal_system_act(self, userid):
		module_name, course_module_id = self.get_user_next_module(userid)
		if module_name is None:
			return SysAct(act_type=SysActionType.Inform, slot_values="all_finished")
		self.state['course_module_id'] = course_module_id
		return SysAct(act_type=SysActionType.Inform,
					  slot_values={"moduleName": module_name, "moduleRequirements": "true", "moduleRequired": "true"})

	def get_new_module_by_time(self, time_avaible: int, userid):
		"""
		NOTE: time_available sollte in Minuten sein (int)
		"""
		# Beispiel Use Cases:
		# Was kann ich heute lernen? -> Wie viel Zeit hast du heute? -> Je nach Dauer vorschlagen
		incomplete_modules_with_time_est = get_time_estimates(self.session, self.get_current_user(userid))
		matches = [module for module, time in incomplete_modules_with_time_est if time and time <= time_avaible]
		return matches
		# TODO beatrice: hier aus matches ausgeben, was du ausgeben willst (die ganze Liste oder nur ein Kursmodul)

	def get_sys_act(self, act: UserAct, userid) -> SysAct:
		if act.type == UserActionType.Request and act.slot == "infoContent":
			# Implement search by Content
			return SysAct(act_type=SysActionType.Inform, slot_values={"notImplementedYet": "True"})
		if act.type == UserActionType.Request and act.slot == "content":
			course_id = self.state.get("course_id")
			course_module_id = self.state.get("course_module_id")
			if course_module_id:
				link = self.get_link_by_course_module_id(course_module_id)
				return SysAct(act_type=SysActionType.Inform,
							  slot_values={"modulContent": "modulContent", "link": link})
		if act.slot == "repeatableModul":
			return self.get_repeatable_modul_sys_act(userid)
		elif act.slot == "learnableModul":
			return SysAct(act_type=SysActionType.Request,
						  slot_values={"learningTime": ""})
		elif act.slot == "learningTime":
			import re
			regex = r"\d+"
			matches = re.search(regex, act.text, re.MULTILINE | re.IGNORECASE)
			if matches:
				module_names = self.get_new_module_by_time(int(matches[0]), userid)
				hasModule = len(module_names) > 0
				if hasModule:
					module_name = str(module_names[0])
				return SysAct(act_type=SysActionType.Inform,
							  slot_values={"moduleName": module_name, "hasModule": "true" if hasModule else "false"})
			return {"sys_act": SysAct(act_type=SysActionType.Bad)}
		elif act.slot == "submission":
			return self.get_submission_sys_act(userid)
		elif act.slot == "finishedGoal":
			nextStep = random.choice(["test", "repeatQuiz"])
			if nextStep == "test":
				return SysAct(act_type=SysActionType.Inform,
							  slot_values={"positiveFeedback": "cool", "test": "true"})
			if nextStep == "repeatQuiz":
				return SysAct(act_type=SysActionType.Inform,
							  slot_values={"positiveFeedback": "cool", "repeatQuiz": "true"})
		elif act.slot == "goal" and act.type == UserActionType.Request:
			return SysAct(act_type=SysActionType.Request,
						  slot_values={"goal": ""})
		elif act.slot == "goalAlternative" or act.slot == "toReachGoal":
			module_name, open_task = self.find_open_tasks()
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"moduleName": module_name, "finishContent": open_task})
		elif act.slot == "goal" and act.type == UserActionType.Inform:
			if act.value == "neue":
				return self.get_new_goal_system_act(userid)
			if act.value == "wiederholen":
				return self.get_repeatable_modul_sys_act(userid)
		elif act.type == UserActionType.Request and act.slot == "moduleRequired":
			module_name = self.get_last_completed_module(userid)
			return SysAct(act_type=SysActionType.Request,
						  slot_values={"pastModule": module_name})
		elif act.slot == "pastModule":
			if act.value == "true":
				module_link, course_module_id = self.get_user_next_module_link(userid)
				self.state['course_module_id'] = course_module_id
				return SysAct(act_type=SysActionType.Inform,
							  slot_values={"positiveFeedback":"", "newModule": module_link})
			if act.value == "false":
				module_link = self.get_user_last_module_link(userid)
				return SysAct(act_type=SysActionType.Inform,
							  slot_values={"pastModule": "a", "repeatContent": module_link})

		elif act.slot == "finishTask" and act.type == UserActionType.Inform:
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"nextStep": random.choice(["newModule", "repeatConcepts", "repeatContents"])})
		elif act.slot == "finishTask" and act.type == UserActionType.Request:
			open_modules = self.total_open_modules(userid)
			completed_modules = self.total_completed_modules(userid)
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"motivational": f"{completed_modules} von {open_modules + completed_modules}", "taskLeft": str(open_modules)})
		elif act.slot == "finishGoal":
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"positiveFeedback": "positiveFeedback", "repeatQuiz": ""})
		elif act.slot == "nextModule":
			module_link, course_module_id = self.get_user_next_module_link(userid)
			self.state['course_module_id'] = course_module_id
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"nextModule": "", "moduleName": module_link})
		elif act.slot == "infoContent":
			# regex für mögliche Inputs implementiert
			# ToDo: Suchfunktion in Moodle implementieren
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"modulContent": "a", "value": "answer"})

		elif act.slot == "content":
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"modulContent": "a", "value": "content"})

		elif act.slot == "firstGoal":
			first_goal = self.first_open_module()
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"moduleName": first_goal, "firstGoal": first_goal})

		elif act.slot == "needHelp":
			# useful information:
			#   - how much time delta between last time access the module and done the quiz
			#   - how much time the user was logged in

			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"suggestion": random.choice(["quiz", "learningTime", "offerHelp"]),
									   "offerhelp": "content"})

		elif act.slot == "insufficient":
			module_names, course_module_id = self.get_insufficient_module(userid)
			self.state["course_module_id"] = course_module_id
			insufficient = "true" if len(module_names) > 0 else "false"
			return SysAct(act_type=SysActionType.Request,
						  slot_values={"quiz_link": "",
									   "module": module_names or '',
									   "insufficient": insufficient})

		elif act.slot == "quiz_link":
			if act.value == "false":
				return SysAct(act_type=SysActionType.Inform,
							  slot_values={"motivateForQuiz": ""})
			else:
				quiz: MCourseModule = self.get_quiz_for_user_by_course_id("6", userid)[1]
				print("QUIZ", quiz)
				print("QUIZ LINK", quiz.get_hvp_embed_html(self.session))
				return SysAct(act_type=SysActionType.Inform,
							  slot_values={"quiz_link": quiz.get_hvp_embed_html(self.session)})

		elif act.type == UserActionType.Thanks:
			return SysAct(act_type=SysActionType.RequestMore,
						  slot_values={"moduleContent": "x"})
		elif act.type == UserActionType.RequestMore:
			return SysAct(act_type=SysActionType.RequestMore)
		elif act.type == UserActionType.Deny:
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"positiveFeedback": "", "offerHelp": ""})
		elif act.type == UserActionType.Bye:
			return SysAct(act_type=SysActionType.Bye)

		elif act.slot == "dueContent":
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"contentTaskRequired": "x"})

		elif act.slot == "welcomeMsgNearAffirm":
			course_id = self.state.get('course_id')
			quizzes = self.get_quiz_for_user_by_course_id(course_id)
			if len(quizzes) == 0:
				return SysAct(act_type=SysActionType.Request,
							  slot_values={"fitForSubmission":"", "newTask":""})

			# Fixme: es funktioniert nicht, weil die session null ist => link = quizzes[0].get_content_link()
			link = str(quizzes[0])
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"fitForTest": "true", "link": link})

		elif act.slot == "welcomeMsgNearDeny":
			link = "link_to_quiz" #self.get_quiz_for_user_by_module_name(act.value)
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"fitForTest": "false", "link": link})

		elif act.slot == "welcomeMsgWeekAffirm":
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"complete_Module_affirm": "x"})

		elif act.slot == "welcomeMsgWeekDeny":
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"complete_Module_deny": "x"})

		elif act.slot == "welcomeRepeatAffirm":
			course_module_id = self.state["course_module_id"]
			module_link = self.get_link_by_course_module_id(course_module_id)
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"repeat_module_affirm": "x", "module_link": module_link})

		elif act.slot == "welcomeRepeatDeny":
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"repeat_module_deny": "x"})

		elif act.slot == "welcomeMsgNewAffirm":
			course_module_id = self.state["course_module_id"]
			module_link = self.get_link_by_course_module_id(course_module_id)
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"repeat_module_affirm": "x", "module_link": module_link})

		elif act.slot == "welcomeMsgNewDeny":
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"new_module_deny": "x"})



	def get_modules(self, since_date, is_finished, userid) -> List[str]:
		"""
			get all modules where last_modified by current user is older than 'since_date' and
			 current user has finished module equals 'is_finished'
		"""
		user = self.get_current_user(userid)
		if is_finished:
			courses = user.get_completed_courses_before_date(since_date, self.session)
		else:
			courses = user.get_not_finished_courses_before_date(since_date, self.session)
		return [course.course.fullname for course in courses]

	def get_modules_by_grade(self, grade_threshold, userid):
		"""
			get modules where grades are lower then 'grade_threshold
		"""
		user = self.get_current_user(userid)
		grades = user.get_grade_history(self.session)
		return [grade for grade in grades if
				grade.finalgrade and grade.finalgrade < (grade.rawgrademax * decimal.Decimal(grade_threshold))]

	def get_user_modules(self, userid):
		user = self.get_current_user(userid)
		user.get_enrolled_course()

	def get_user_next_module(self, userid):
		# while loop ends in infinite loop if all courses are completed
		user = self.get_current_user(userid)
		module = user.get_last_completed_coursemodule(self.session)
		next_module: MCourseModule = module.section.get_next_available_module(module, self.get_current_user(userid), self.session)
		if next_module is None:
			return None
		return str(next_module), next_module.id

	def get_user_next_module_link(self, userid):
		# while loop ends in infinite loop if all courses are completed
		user = self.get_current_user(userid)
		module = user.get_last_completed_coursemodule(self.session)
		next_module: MCourseModule = module.section.get_next_available_module(module, self.get_current_user(userid), self.session)
		if next_module is None:
			return None
		return next_module.get_content_link(self.session), next_module.id

	def get_user_last_module_link(self, userid):
		# while loop ends in infinite loop if all courses are completed
		user = self.get_current_user(userid)
		module = user.get_last_completed_coursemodule(self.session)
		if module is None:
			return None
		return module.get_content_link(self.session)

	def get_last_completed_module(self, userid):
		# while loop ends in infinite loop if all courses are completed
		user = self.get_current_user(userid)
		module = user.get_last_completed_coursemodule(self.session)
		return module.course.fullname

	def find_open_tasks(self):
		# ToDo: Chatbot muss aus Moodle die Info bekommen, welche Tasks nicht beendet wurden
		# TODO: Q: Was sind Tasks? meinst du verschiedene Course Module Typen? Z.B. Quiz, Buch, ... oder ist das noch was anderes?
		# @Dirk ich meinte alle Module, d.h. auch Quiz
		return self.get_user_next_module(), random.choice(["video", "frage", "module", "doku"])

	def total_open_modules(self, userid):
		user = self.get_current_user(userid)
		return len(user.get_incomplete_available_course_modules(self.session))

	def total_completed_modules(self, userid):
		user = self.get_current_user(userid)
		return len(user.get_completed_courses(self.session))

	def first_open_module(self, userid):
		user = self.get_current_user(userid)
		course_modules = user.get_incomplete_available_course_modules(self.session)
		return course_modules[0].section.name

	def get_insufficient_module(self, userid):
		user = self.get_current_user(userid)
		grades = user.get_grade_history(self.session)
		return [(grade.get_grade_item(self.session).course.fullname, grade.get_grade_item(self.session).course.id) for grade in grades if
				grade.finalgrade and grade.finalgrade < grade.get_grade_item(self.session).gradepass or grade.finalgrade is None and grade.get_grade_item(self.session)][0]

	def get_quiz_for_user_by_course_id(self, course_id: str, userid):
		user = self.get_current_user(userid)
		return user.find_quiz_by_course_id(course_id, self.session)

	def start_msg(self, userid):
		module_name, due_date = self.get_module_and_next_due_date(userid)
		if not due_date:
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"welcomeMsg": "repeat", "daysToSubmission": "empty"})
		days_to_due_date = (due_date.date() - datetime.date.today()).days
		if days_to_due_date < 3:
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"welcomeMsg": "due_date", "daysToSubmission": "near", "moduleName": module_name})
		elif days_to_due_date < 6:
			return SysAct(act_type=SysActionType.Inform,
						  slot_values={"welcomeMsg": "due_date", "daysToSubmission": "week", "moduleName": module_name})
		else:
			return SysAct(act_type=SysActionType.Inform,
					  slot_values={"welcomeMsg": "repeat", "daysToSubmission": "empty"})


	def get_module_and_next_due_date(self, userid) -> Tuple[str, None]:
		user = self.get_current_user(userid)
		assignments = self.session.query(MAssignSubmission).filter(MAssignSubmission._user_id == user.id).all()
		assigns = [assign.assignment for assign in assignments if assign.assignment.duedate > datetime.datetime.now()]
		if not assigns:
			return None, None
		min_assigns = min(assigns, key=attrgetter('duedate'))
		self.state['course_id'] = min_assigns.course
		self.state['assign_id'] = min_assigns.id
		return min_assigns.name, min_assigns.duedate

	def get_link_by_course_module_id(self, course_module_id):
		course = self.session.query(MCourseModule).filter(MCourseModule.id == course_module_id).one()
		return course.get_content_link(self.session)
