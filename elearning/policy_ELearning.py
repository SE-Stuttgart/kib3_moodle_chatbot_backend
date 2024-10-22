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
from enum import Enum
import logging
import threading
import traceback
from typing import List, Tuple, TypedDict
import time
import locale


from elearning.booksearch import get_book_links
from services.service import PublishSubscribe
from services.service import Service
from utils import SysAct, SysActionType
from utils.domain.jsonlookupdomain import JSONLookupDomain
from utils import UserAct
from elearning.moodledb import ContentLinkInfo, UserSettings, WeeklySummary, fetch_available_new_course_section_ids, fetch_badge_info, fetch_branch_review_quizzes, fetch_closest_badge, fetch_content_link, fetch_first_available_course_module_id, fetch_h5pquiz_params, fetch_has_seen_any_course_modules, fetch_last_user_weekly_summary, fetch_last_viewed_course_modules, fetch_next_available_course_module_id, fetch_oldest_worst_grade_course_ids, fetch_section_completionstate, fetch_starter_module_id, fetch_topic_id_and_name, fetch_user_settings, fetch_user_statistics, fetch_viewed_course_modules_count
from utils.useract import UserActionType, UserAct
# from dotenv import load_dotenv
import os

# Load environment variables from the .env file
# load_dotenv()

# Retrieve the LC_TIME environment variable
locale_setting = os.getenv("LC_TIME")
print(locale_setting)
locale.setlocale(locale.LC_TIME, locale_setting)

TURNS = 'turns'
MODE = 'mode'
LAST_SEARCH = 'last_search'
LAST_SEARCH_INDEX = 'last_search_index'
REVIEW_QUIZZES = "review_quizzes"
CURRENT_REVIEW_QUIZ = "current_review_quiz"
REVIEW_QUIZ_IMPROVEMENTS = "review_quiz_improvements"
LAST_FINISHED_TOPIC_ID = 'last_finished_section'
NEXT_MODULE_SUGGESTIONS = 'next_module_suggestions'
SETTINGS = 'settings'

learning_material_types = ["url", "book", "resource", "icecreamgame"]
assignment_material_types = ['h5pactivity']# query day-wise completions


COURSE_PROGRESS_DISPLAY_PERCENTAGE_INCREMENT = 0.1


class ChatbotWindowSize(Enum):
    DEFAULT = 0
    LARGE = 1


class ChatbotOpeningContext(Enum):
    DEFAULT = "default"
    LOGIN = "openonlogin"
    QUIZ = "openonquiz"
    SECTION = "openonsection"
    BRANCH = "openonbranch"
    BADGE = "openonbadge"


class PolicyReturn(TypedDict):
    sys_acts: List[SysAct]
    sys_state: SysAct


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

    def __init__(self, domain: JSONLookupDomain, max_turns: int = 25):
        """
        Initializes the policy

        Arguments:
            domain {domain.jsonlookupdomain.JSONLookupDomain} -- Domain

        """
        Service.__init__(self, domain=domain)
        self.max_turns = max_turns
        self.session = None
        self.session_lock = threading.Lock()
        self.webservice_user_id = None

    def get_webservice_user_id(self, user_id: int):
        return self.get_state(user_id, "WSUSERID")
    
    def get_moodle_server_time(self, userid: int) -> datetime:
        """ Returns the current moodle server time as unix timestamp """
        difference = self.get_state(userid, "SERVERTIMEDIFFERENCE")
        return datetime.fromtimestamp(int(time.time()) + difference)

    @PublishSubscribe(pub_topics=['control_event'])
    def open_chatbot(self, user_id: int, context: ChatbotOpeningContext, force: bool = False):
        """ Triggers the UI chatwindow to open, respecting the opening context and the user settings """
        if self.check_setting(user_id, 'enabled'):
            if force or (context == ChatbotOpeningContext.DEFAULT or self.check_setting(user_id=user_id, setting_key=context.value)):
                return {
                    "control_event": "UI_OPEN",
                    "user_id": user_id
                }
    
    @PublishSubscribe(pub_topics=['control_event'])
    def open_settings(self, user_id: int):
        """ Open settings modal in UI """
        return {
            "control_event": "UI_SETTINGS",
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
        
    def check_setting(self, user_id: int, setting_key: str):
        return getattr(self.get_state(user_id, SETTINGS), setting_key)

    def get_wstoken(self, userid: int):
        return self.get_state(userid, 'BOOKSEARCHTOKEN')

    def dialog_start(self, user_id: str):
        """
            resets the policy after each dialog
        """
        # set user dialog state
        try:
            if not self.get_state(user_id, TURNS):
                # get user settings
                settings = fetch_user_settings(wstoken=self.get_wstoken(user_id), userid=user_id)
                self.set_state(user_id, SETTINGS, settings)
                self.set_state(user_id, TURNS, 0)
                self.set_state(user_id, LAST_SEARCH, {})
                self.set_state(user_id, LAST_SEARCH, None)
                self.set_state(user_id, LAST_SEARCH_INDEX, 0)
                self.set_state(user_id, REVIEW_QUIZZES, [])
                self.set_state(user_id=user_id, attribute_name=CURRENT_REVIEW_QUIZ, attribute_value=None)
                self.set_state(user_id=user_id, attribute_name=REVIEW_QUIZ_IMPROVEMENTS, attribute_value=[])
                self.set_state(user_id, LAST_FINISHED_TOPIC_ID, -1)
                self.set_state(user_id, NEXT_MODULE_SUGGESTIONS, [])
        except:
            # Log error
            logging.getLogger("error_log").error("DIALOG_START: " + traceback.format_exc())

    def dialog_started(self, user_id: str) -> bool:
        """Returns true, if the dialog start was called successfully for the specified user"""
        return not self.get_state(user_id, TURNS) is None # Turn is only set in successful dialog_start call

    @PublishSubscribe(sub_topics=["settings"])
    def settings_changed(self, user_id: int, settings: dict):
        self.set_state(user_id, SETTINGS, UserSettings(**settings))

    @PublishSubscribe(sub_topics=["moodle_event"], pub_topics=["sys_acts", "sys_state"])
    def moodle_event(self, user_id: int, moodle_event: dict) -> PolicyReturn:
        """ Responsible for reacting to events from mooodle.
            Triggered by interaction with moodle (NOT the chatbot), e.g. when someone completes a coursemodule.

            Currently supports the following events:
            * \\core\\event\\course_module_completion_updated
        """
        event_name = moodle_event['eventname'].lower().strip()

        if event_name == "\\core\\event\\user_loggedin":
            self.clear_memory(user_id)
        elif event_name == "\\core\\event\\badge_awarded":
            return {'sys_acts': [
                self.congratulate_badge_issued(user_id=user_id, badge_id=moodle_event['objectid'], contextid=moodle_event['contextid'])
            ]}
        elif event_name == "\\core\\event\\course_module_completion_updated":
            # check if we finished a whole branch
            # TODO if so, offer congratulations, the review, and then next possibilities?
            cmid = moodle_event['contextinstanceid']

            # remove completed module from next module suggestion list s.t. user doesn't get the completed module as new suggestion
            self.set_state(user_id, NEXT_MODULE_SUGGESTIONS, list(filter(lambda sec_info: sec_info.firstcmid != cmid, self.get_state(user_id, NEXT_MODULE_SUGGESTIONS))))

            # find current section id from course module
            topic_id, topic_name = fetch_topic_id_and_name(wstoken=self.get_wstoken(user_id), cmid=cmid)
            branch_review_info = fetch_branch_review_quizzes(wstoken=self.get_wstoken(user_id), userid=user_id, topicname=topic_name)
            self.set_state(user_id, REVIEW_QUIZZES, branch_review_info.candidates)
            if branch_review_info.completed and len(branch_review_info.candidates) > 0:
                # we did complete a full branch, and there are review modules available
                # ask user if they want to review any of the quizzes
                self.open_chatbot(user_id=user_id, context=ChatbotOpeningContext.BRANCH)
                return {"sys_acts": [
                    SysAct(act_type=SysActionType.CongratulateCompletion, slot_values={"name": branch_review_info.branch, "branch": True}),
                    SysAct(act_type=SysActionType.RequestReviewOrNext)]}
            else:
                # did we complete a full section?
                section_completed = fetch_section_completionstate(wstoken=self.get_wstoken(user_id), userid=user_id, sectionid=section_id)
                if section_completed:
                    # reset current list of next module suggestions, because we will unlock new ones here
                    self.set_state(user_id, NEXT_MODULE_SUGGESTIONS, [])

                    # we get this event for each of the modules in a section with different materials (i.e., once for video, once for pdf, once for book):
                    # check that we didn't already offer congratulations, otherwise the autocomplete plugin will trigger this event for each material type
                    last_completed_section_id = self.get_state(user_id, LAST_FINISHED_TOPIC_ID)
                    if last_completed_section_id != section_id:
                        self.set_state(user_id, LAST_FINISHED_TOPIC_ID, section_id)
                        self.open_chatbot(user_id=user_id, context=ChatbotOpeningContext.SECTION)
                        sys_acts = [SysAct(SysActionType.CongratulateCompletion, slot_values={"name": section_name, 'branch': False})]
                        # TODO section id here should become a topic name
                        sys_acts += self.get_user_next_module(userid=user_id, courseid=moodle_event['courseid'],
                                                            add_last_viewed_course_module=False, current_topic=section_id)
                        return {
                            "sys_acts": sys_acts
                        }
        elif event_name == "\\mod_h5pactivity\\event\\statement_received" and moodle_event['component'] == 'mod_h5pactivity':
            previous_quiz_attempt_info = self.get_state(user_id=user_id, attribute_name=CURRENT_REVIEW_QUIZ)
            if (not previous_quiz_attempt_info is None) and int(moodle_event['contextinstanceid']) == previous_quiz_attempt_info.cmid:
                sys_acts = []
                current_grade = (moodle_event['other']['result']['score']['raw'] / moodle_event['other']['result']['score']['max']) * 100.0
                next_quizzes = self.get_state(user_id=user_id, attribute_name=REVIEW_QUIZZES)
                next_quiz_info = next_quizzes[0] if len(next_quizzes) > 0 else None
                self.set_state(user_id=user_id, attribute_name=REVIEW_QUIZZES, attribute_value=next_quizzes[1:])
                self.set_state(user_id=user_id, attribute_name=CURRENT_REVIEW_QUIZ, attribute_value=next_quiz_info)
                improvements = self.get_state(user_id=user_id, attribute_name=REVIEW_QUIZ_IMPROVEMENTS)
                improvements.append(True if current_grade > previous_quiz_attempt_info.grade else False)
                self.set_state(user_id=user_id, attribute_name=REVIEW_QUIZ_IMPROVEMENTS, attribute_value=improvements)
                if not next_quiz_info is None:
                    sys_acts.append(self.display_quiz(user_id=user_id, coursemoduleid=next_quiz_info.cmid))
                else:
                    # create a graphic summary of how many quizzes the user did better on
                    sys_acts.append(SysAct(act_type=SysActionType.DisplayQuizImprovements, slot_values={"improvements": improvements}))
                    self.resize_chatbot(user_id=user_id, size=ChatbotWindowSize.DEFAULT)
                return {"sys_acts": sys_acts}
            # In the case that the quiz is done outside the chatbot, give feedback (about absolute grade) and offer next quiz (if applicable)
            self.open_chatbot(user_id=user_id, context=ChatbotOpeningContext.QUIZ)
            success_percentage = (moodle_event['other']['result']['score']['raw'] / moodle_event['other']['result']['score']['max']) * 100.0
            next_quiz_id = fetch_next_available_course_module_id(wstoken=self.get_wstoken(user_id), userid=user_id, current_cmid=int(moodle_event['contextinstanceid']),
                                                                 include_types='h5pactivity', allow_only_unfinished=True, current_cm_completion=True)
            if next_quiz_id is None:
                # there are no more quizzes in the current section - suggest to move on to new section
                sys_acts = [SysAct(act_type=SysActionType.FeedbackToQuiz, slot_values=dict(
                            success_percentage=success_percentage,
                            url=None, displaytext=None, typename=None))]
                sys_acts.append(self.fetch_n_next_available_course_sections(userid=user_id, courseid=moodle_event['courseid']))
                return {"sys_acts": sys_acts}
            else:
                next_quiz_link = fetch_content_link(wstoken=self.get_wstoken(user_id), cmid=next_quiz_id) if next_quiz_id else None
                return {"sys_acts": [SysAct(act_type=SysActionType.FeedbackToQuiz, slot_values=dict(
                    success_percentage=success_percentage,
                    **next_quiz_link.to_dict("nächste Quiz")
                ))]}             
            # only in review loop comment on improvements, otherwise absolute grade only


    def get_weekly_progress(self, user_id: int, courseid: int, last_weekly_summary: WeeklySummary):
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
        for day in reversed(range((2-int(last_weekly_summary.first_week))*7)):
            # get day interval for DB query
            start_time = beginning_of_today - timedelta(days=day+1)
            end_time = beginning_of_today - timedelta(days=day)
            # get day name for chart display
            day_name = (now_chatbot_time - timedelta(days=day+1))

            # add module completions and quiz completions together.
            # module completions are divided by 3, because the autocomplete plugin always ensures 3 completions per module
            # completed = fetch_viewed_course_modules_count(wstoken=self.get_wstoken(user_id),
            #                                               userid=user_id,
            #                                               courseid=courseid,
            #                                               include_types=",".join(learning_material_types),
            #                                               starttime=start_time,
            #                                               endtime=end_time) / 3
            # completed += fetch_viewed_course_modules_count(wstoken=self.get_wstoken(user_id),
            #                                               userid=user_id,
            #                                               courseid=courseid,
            #                                               include_types=",".join(assignment_material_types),
            #                                               starttime=start_time,
            #                                               endtime=end_time)
            
            # We decided not to divide contents by 3, because this doesn't work consistently across later sections in ZQ as well as DQR.
            completed = fetch_viewed_course_modules_count(wstoken=self.get_wstoken(user_id),
                                                    userid=user_id,
                                                    courseid=courseid,
                                                    include_types=",".join(learning_material_types + assignment_material_types),
                                                    starttime=start_time,
                                                    endtime=end_time)
            if day < 7:
                last_week_data.append(completed)
                last_week_days.append(day_name)
            else:
                prev_week_data.append(completed)
                prev_week_days.append(day_name)

        best_weekly_days = [last_week_days[i].strftime('%A') for i in range(len(last_week_data)) if last_week_data[i] == max(last_week_data)] if max(last_week_data) > 0 else []
        # shorten week days for stats to 2 letters: strftime('%A')[:2]
        cumulative_weekly_completions = {"y": [sum(last_week_data[:(i+1)]) for i in range(len(last_week_data))], "x": [day.strftime('%A')[:2] for day in last_week_days]}
        cumulative_weekly_completions_prev = None if last_weekly_summary.first_week else {"y": [sum(prev_week_data[:(i+1)]) for i in range(len(prev_week_data))], "x": [day.strftime('%A')[:2] for day in prev_week_days]}

        # update timestamp of last stat output
        fetch_last_user_weekly_summary(wstoken=self.get_wstoken(user_id), userid=user_id, courseid=courseid, update_db=True)

        return dict(best_weekly_days=best_weekly_days,
                  weekly_completions=cumulative_weekly_completions,
                weekly_completions_prev=cumulative_weekly_completions_prev)
    
    def get_stat_summary(self, user_id: int, courseid: int, update_db: bool = False):
        # we should show total course progress every 10% of completion
        user_stats = fetch_user_statistics(wstoken=self.get_wstoken(user_id), userid=user_id, courseid=courseid, include_types=",".join(learning_material_types + assignment_material_types), update_db=update_db)
        return dict(percentage_done=user_stats.course_completion_percentage,
                    percentage_repeated_quizzes=user_stats.quiz_repetition_percentage)

    def get_starter_module_id(self, user_id: int, courseid: int) -> str:
        return fetch_starter_module_id(wstoken=self.get_wstoken(user_id), courseid=courseid)
        
    def choose_greeting(self, user_id: int, courseid: int) -> List[SysAct]:
        self.open_chatbot(user_id=user_id, context=ChatbotOpeningContext.LOGIN)
        acts = []

        last_weekly_summary = fetch_last_user_weekly_summary(wstoken=self.get_wstoken(user_id), userid=user_id, courseid=courseid)

        if last_weekly_summary.first_turn_ever:
            # user is seeing chatbot for the first time
            self.open_chatbot(user_id=user_id, context=ChatbotOpeningContext.LOGIN, force=True)
            first_cm_id = self.get_starter_module_id(user_id=user_id, courseid=courseid)
            first_cm_link = fetch_content_link(wstoken=self.get_wstoken(user_id), cmid=first_cm_id)
            if last_weekly_summary.first_week:
                # user has not yet completed any modules: show some introduction & ice cream game
                return [SysAct(act_type=SysActionType.Welcome, slot_values={"first_turn": True}),
                        SysAct(act_type=SysActionType.InformStarterModule, slot_values=dict(
                            module_link=first_cm_link.to_href_element()
                        ))]
            else:
                # user has completed some modules: show course summary, and next course section
                slot_values = self.get_stat_summary(user_id=user_id, courseid=courseid, update_db=True)
                return [
                    SysAct(act_type=SysActionType.Welcome, slot_values={"first_turn": True}),
                    SysAct(act_type=SysActionType.DisplayProgress, slot_values=slot_values),
                ] + self.get_user_next_module(userid=user_id, courseid=courseid, add_last_viewed_course_module=True)

        # Add greeting
        acts.append(SysAct(act_type=SysActionType.Welcome, slot_values={}))

        # check that we haven't displayed the weekly stats in more than 7 days
        append_suggestions = True
        if self.get_moodle_server_time(user_id) >= last_weekly_summary.timecreated + timedelta(days=7):
            # last time we showed the weekly stats is more than 7 days ago - show again
            slot_values = self.get_weekly_progress(user_id=user_id, courseid=courseid, last_weekly_summary=last_weekly_summary)
            acts.append(SysAct(act_type=SysActionType.DisplayWeeklySummary, slot_values=slot_values))
        else:
            # we should show total course progress every 10% of completion
            slot_values = self.get_stat_summary(user_id=user_id, courseid=courseid, update_db=True)

            if slot_values["percentage_done"] >= last_weekly_summary.course_progress_percentage + COURSE_PROGRESS_DISPLAY_PERCENTAGE_INCREMENT:
                acts.append(SysAct(act_type=SysActionType.DisplayProgress, slot_values=slot_values))
                acts.append(SysAct(act_type=SysActionType.RequestReviewOrNext))
                append_suggestions = False
            else:
                # check what user's next closest badge would be
                closest_badge_info = fetch_closest_badge(wstoken=self.get_wstoken(user_id), userid=user_id, courseid=courseid)
                if not isinstance(closest_badge_info.id, type(None)):
                    if closest_badge_info.completion_percentage >= 0.5:
                        # only display progress towards next closest batch if user is sufficiently close
                        acts.append(SysAct(act_type=SysActionType.DisplayBadgeProgress, slot_values=dict(
                            badge_name=closest_badge_info.name, percentage_done=closest_badge_info.completion_percentage,
                            missing_activities=[fetch_content_link(wstoken=self.get_wstoken(user_id), cmid=cmid).to_dict()
                                                for cmid in closest_badge_info.open_modules]
                        )))
                        append_suggestions=False

        if append_suggestions:
            # choose how to proceed
            acts += self.get_user_next_module(userid=user_id, courseid=courseid, add_last_viewed_course_module=True)
            
        return acts

    def _handle_request_badge_progress(self, user_id: int, courseid: int, min_progress: float = 0.5) -> SysAct:
        # check what user's next closest badge would be
        closest_badge_info = fetch_closest_badge(wstoken=self.get_wstoken(user_id), userid=user_id, courseid=courseid)
        if not isinstance(closest_badge_info.id, type(None)):
            if closest_badge_info.completion_percentage >= min_progress:
                # only display progress towards next closest batch if user is sufficiently close
                return SysAct(act_type=SysActionType.DisplayBadgeProgress, slot_values=dict(
                            badge_name=closest_badge_info.name, percentage_done=closest_badge_info.completion_percentage,
                            missing_activities=[fetch_content_link(wstoken=self.get_wstoken(user_id), cmid=cmid).to_dict()
                                                for cmid in closest_badge_info.open_modules]
                    ))
            else:
                return SysAct(SysActionType.DisplayBadgeProgress, slot_values=dict(
                    badge_name=None,
                    percentage_done=None,
                    missing_activities=None
                ))
        else: 
            # all badges aAre already completed
            return SysAct(act_type=SysActionType.DisplayBadgeProgress, slot_values=dict(
                badge_name=None, percentage_done=None, missing_activities=None
            ))

    def congratulate_badge_issued(self, user_id: int, badge_id: int, contextid: int) -> SysAct:
        self.open_chatbot(user_id=user_id, context=ChatbotOpeningContext.BADGE)
        # find badge
        badge_info = fetch_badge_info(wstoken=self.get_wstoken(user_id), badgeid=badge_id, contextid=contextid)
        # get badge image link
        return SysAct(act_type=SysActionType.CongratulateBadge,
            slot_values=dict(badge_name=badge_info.name,
                    badge_img_url=badge_info.url)
        )
    
    def display_quiz(self, user_id: int, coursemoduleid: int) -> SysAct:
        hvp_params = fetch_h5pquiz_params(wstoken=self.get_wstoken(user_id), cmid=coursemoduleid)
        self.resize_chatbot(user_id=user_id, size=ChatbotWindowSize.LARGE)
        return SysAct(act_type=SysActionType.DisplayQuiz, slot_values=dict(quiz_embed=hvp_params.serialize()))
    
    def reset_search_term(self, user_id: int, user_acts: List[UserAct]):
        """
        Reset last user's search term if no serach / load more act types found in user acts
        """
        search_act = any([act.type in [UserActionType.Search, UserActionType.LoadMoreSearchResults] for act in user_acts])
        if not search_act:
            self.set_state(user_id, LAST_SEARCH, None)
            self.set_state(user_id, LAST_SEARCH_INDEX, 0)

    def search_resources(self, user_id: int, courseid: int, search_term: str, search_idx: int, num_results: int = 3) -> Tuple[List[str], bool]:
        """
        Lookup resources, and increments search index. Also updates search term.
        Returns:
            List of search results
            Boolean: if there are more search results
        """
        book_links, has_more_results = get_book_links(webserviceuserid=user_id, wstoken=self.get_state(user_id, 'BOOKSEARCHTOKEN'), course_id=courseid, searchTerm=search_term, word_context_length=5, start=search_idx, end=search_idx+num_results)
        
        self.set_state(user_id=user_id, attribute_name=LAST_SEARCH_INDEX, attribute_value=search_idx + num_results)
        self.set_state(user_id=user_id, attribute_name=LAST_SEARCH, attribute_value=search_term)
        return book_links, has_more_results
    
    def fetch_n_next_available_course_sections(self, userid: int, courseid: int, max_display_options: int = 5) -> SysAct:
        # see if we currently have a list of next course id's that we can cycle through
        available_new_course_section_ids = self.get_state(userid, NEXT_MODULE_SUGGESTIONS)
        if len(available_new_course_section_ids) == 0:
            # we don't have any suggestions -> fetch all possible next sections
            available_new_course_section_ids = [section for section in 
                                                fetch_available_new_course_section_ids(wstoken=self.get_wstoken(userid), userid=userid, courseid=courseid)
                                                if section.section > 0]
        # extract n next suggestions. if we have none, the NLG will handle it.
        next_suggestions = available_new_course_section_ids[:max_display_options]
        remaining_suggestions = available_new_course_section_ids[max_display_options:]
        act = SysAct(act_type=SysActionType.InformNextOptions, slot_values=dict(
                    has_more=len(remaining_suggestions) > 0,
                    next_available_sections=[fetch_content_link(wstoken=self.get_wstoken(userid),
                                                                cmid=section.firstcmid).to_dict(section.name) 
                                                for section in next_suggestions])
        )
        # truncate list of next suggestions
        self.set_state(userid, NEXT_MODULE_SUGGESTIONS, remaining_suggestions)
        return act
        
    
    @PublishSubscribe(sub_topics=["user_acts", "beliefstate", "courseid"], pub_topics=["sys_acts", "sys_state"])
    def choose_sys_act(self, user_id: str, user_acts: List[UserAct], beliefstate: dict, courseid: int) -> PolicyReturn:
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
        if turns == 1:
            # print first turn message
            sys_acts = self.choose_greeting(user_id, courseid)
            sys_state["last_act"] = sys_acts
            return {'sys_acts': sys_acts, "sys_state": sys_state}
        # after first turn
        self.reset_search_term(user_id=user_id, user_acts=user_acts)
        review_act = False
        sys_acts = []
        for user_act in user_acts:
            if user_act.type == UserActionType.RequestReview:
                review_act = True
                review_candidates = self.get_state(user_id=user_id, attribute_name=REVIEW_QUIZZES)
                if len(review_candidates) == 0:
                    # get next quizzes to review, from worst and oAldest to better and newer
                    max_num_quizzes = self.check_setting(user_id=user_id, setting_key="numreviewquizzes")
                    review_candidates = fetch_oldest_worst_grade_course_ids(wstoken=self.get_wstoken(user_id), userid=user_id, courseid=courseid, max_num_quizzes=max_num_quizzes)
                next_quiz_info = review_candidates[0] if len(review_candidates) > 0 else None
                self.set_state(user_id=user_id, attribute_name=CURRENT_REVIEW_QUIZ, attribute_value=next_quiz_info)
                if not next_quiz_info is None:
                    sys_acts.append(self.display_quiz(user_id=user_id, coursemoduleid=next_quiz_info.cmid))
                else: 
                    sys_acts.append(SysAct(act_type=SysActionType.DisplayQuiz, slot_values={"quiz_embed": None}))
                self.set_state(user_id, REVIEW_QUIZZES, review_candidates[1:])
            elif user_act.type == UserActionType.RequestNextSection:
                sys_acts.append(self.fetch_n_next_available_course_sections(userid=user_id, courseid=courseid))
            elif user_act.type == UserActionType.RequestProgress:
                slot_values = self.get_stat_summary(user_id=user_id, courseid=courseid)
                sys_acts.append(SysAct(act_type=SysActionType.DisplayProgress, slot_values=slot_values))
            elif user_act.type == UserActionType.RequestBadgeProgress:
                sys_acts.append(self._handle_request_badge_progress(user_id=user_id, courseid=courseid, min_progress=0.0))
            elif user_act.type == UserActionType.ContinueOpenModules:
                sys_acts += self.get_user_next_module(userid=user_id, courseid=courseid)
            elif user_act.type in [UserActionType.Search, UserActionType.LoadMoreSearchResults]:
                if not user_act.value is None:
                    # if we have a new search term, reset the search index and give out first three results
                    # we already extracted the search term from the user query - return results immediately
                    book_link_list, has_more_search_results = self.search_resources(user_id=user_id, courseid=courseid, search_term=user_act.value, search_idx=0, num_results=self.check_setting(user_id, 'numsearchresults'))
                    sys_act = SysAct(act_type=SysActionType.InformSearchResults, slot_values={"search_results": book_link_list, "load_more": has_more_search_results})
                    sys_acts.append(sys_act)
                else:
                    if not self.get_state(user_id=user_id, attribute_name=LAST_SEARCH) is None:
                        # if we have a search term already, use that
                        last_search_term = self.get_state(user_id=user_id, attribute_name=LAST_SEARCH)
                        book_link_list, has_more_search_results = self.search_resources(user_id=user_id, courseid=courseid, search_term=last_search_term, search_idx=self.get_state(user_id=user_id, attribute_name=LAST_SEARCH_INDEX), num_results=self.check_setting(user_id, 'numsearchresults'))
                        sys_act = SysAct(act_type=SysActionType.InformSearchResults, slot_values={"search_results": book_link_list, "load_more": has_more_search_results})
                        sys_acts.append(sys_act)
                    else:
                        # otherwise we want to search, but didn't recognize the user input from the first query - ask for search term only
                        sys_act = SysAct(act_type=SysActionType.RequestSearchTerm, slot_values={})
                        sys_acts.append(sys_act)
            elif user_act.type == UserActionType.RequestSettings:
                # open settings modal
                self.open_settings(user_id=user_id)
                return
            elif user_act.type == UserActionType.Bad:
                sys_acts.append(SysAct(act_type=SysActionType.Bad))
            elif user_act.type == UserActionType.Hello:
                sys_acts.append(SysAct(act_type=SysActionType.Welcome))
            elif user_act.type == UserActionType.Thanks:
                sys_acts.append(SysAct(act_type=SysActionType.YouAreWelecome))
            elif user_act.type == UserActionType.RequestHelp:
                sys_acts.append(SysAct(act_type=SysActionType.InformHelp))
            elif user_act.type == UserActionType.RequestSectionSummary:
                # TODO 
                pass
        if not review_act:
            self.set_state(user_id, REVIEW_QUIZZES, [])
            self.set_state(user_id=user_id, attribute_name=CURRENT_REVIEW_QUIZ, attribute_value=None)
            self.set_state(user_id=user_id, attribute_name=REVIEW_QUIZ_IMPROVEMENTS, attribute_value=[]) 
            self.resize_chatbot(user_id=user_id, size=ChatbotWindowSize.DEFAULT)
        sys_state["last_act"] = sys_acts
        return {'sys_acts':  sys_acts, "sys_state": sys_state}

    def get_user_next_module(self, userid: int, courseid: int, add_last_viewed_course_module: bool = False, current_topic: str = None) -> List[SysAct]:
        # choose how to proceed
        acts = []
        has_seen_any_course_modules = fetch_has_seen_any_course_modules(wstoken=self.get_wstoken(userid), userid=userid, courseid=courseid)
        
        all_topic_completed = False
        if has_seen_any_course_modules:
            # last viewed module
            last_completed_course_modules = fetch_last_viewed_course_modules(wstoken=self.get_wstoken(userid),
                                                                             userid=userid,
                                                                             courseid=courseid, completed=True)
            if len(last_completed_course_modules) > 0:
                last_completed_course_module = last_completed_course_modules[0] # sorted ascending by date

                # get open modules across sections, 1 per section
                next_modules = {}
                # prioritize already viewed modules
                last_started_course_modules = fetch_last_viewed_course_modules(wstoken=self.get_wstoken(userid), userid=userid, courseid=courseid, completed=False)
                for unfinished_module in last_started_course_modules:
                    if not unfinished_module.topicid in next_modules and unfinished_module.topicname != current_topic and unfinished_module.topicname not in ["thema:kursüberblick", "thema:einstieg", "thema:einstiegsaktivität"]:
                        next_modules[unfinished_module.topicname] = unfinished_module.cmid
                # fill with other started sections
                for completed_module in last_completed_course_modules:
                    if not completed_module.topicname in next_modules and completed_module.topicname != current_topic and completed_module.topicname not in ["thema:kursüberblick", "thema:einstieg", "thema:einstiegsaktivität"]:
                        # get first open module from this section
                        next_module_id= fetch_first_available_course_module_id(wstoken=self.get_wstoken(userid), userid=userid, topicname=completed_module.topicname,
                                                                             courseid=courseid,
                                                                             includetypes=",".join(learning_material_types + assignment_material_types),
                                                                             allow_only_unfinished=True)
                        if not next_module_id is None:
                            next_modules[completed_module.topicname] = next_module_id
                next_available_module_links = []
                for cmid in next_modules.values():
                    topic_id, topic_name = fetch_topic_id_and_name(wstoken=self.get_wstoken(userid), cmid=cmid)
                    next_available_module_links.append(fetch_content_link(wstoken=self.get_wstoken(userid), cmid=cmid).to_dict(topic_name))

                # user has started, but not completed one or more sections
                if add_last_viewed_course_module:
                    acts.append(SysAct(act_type=SysActionType.InformLastViewedCourseModule, slot_values=dict(
                        last_viewed_course_module=fetch_content_link(wstoken=self.get_wstoken(userid), cmid=last_completed_course_module.cmid).to_dict()
                    )))
                if len(next_available_module_links) > 0:
                    acts.append(
                            SysAct(act_type=SysActionType.RequestContinueOrNext, slot_values=dict(
                                    next_available_modules=next_available_module_links
                            )))
                else:
                    all_topic_completed = True
            # TODO: Forum post info
            # TODO: Deadline reminder
                if all_topic_completed:
                    # user has completed all started sections, should get choice of next new and available sections
                    acts.append(self.fetch_n_next_available_course_sections(userid=userid, courseid=courseid))
            else:
                # has seen modules, but none completed or really started
                # return first module in course, e.g. ice cream game
                first_section_link = self.get_starter_module_id(user_id=userid, courseid=courseid)
                return [SysAct(act_type=SysActionType.Welcome, slot_values={"first_turn": True}),
                        SysAct(act_type=SysActionType.InformStarterModule, slot_values=dict(
                            module_link=first_section_link
                        ))]
        else:
            # return ice cream game
            # return first module in course, e.g. ice cream game
            first_section_link = self.get_starter_module_id(user_id=userid, courseid=courseid)
            return [SysAct(act_type=SysActionType.Welcome, slot_values={"first_turn": True}),
                    SysAct(act_type=SysActionType.InformStarterModule, slot_values=dict(
                        module_link=first_section_link
                    ))]
        return acts
