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
import threading
import traceback
from typing import List, Tuple
import time
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
from elearning.moodledb import BadgeCompletionStatus, MBadge, MCourseModulesViewed, MGradeItem, MH5PActivity, connect_to_moodle_db, Base, MUser, MCourseModule, fetch_branch_review_quizzes, fetch_section_completionstate, fetch_section_id_and_name, fetch_user_settings, MModule, MChatbotProgressSummary, MChatbotWeeklySummary
from utils.useract import UserActionType, UserAct

locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')

TURNS = 'turns'
MODE = 'mode'
LAST_SEARCH = 'last_search'
LAST_SEARCH_INDEX = 'last_search_index'
REVIEW_QUIZZES = "review_quizzes"
CURRENT_REVIEW_QUIZ = "current_review_quiz"
REVIEW_QUIZ_IMPROVEMENTS = "review_quiz_improvements"
LAST_FINISHED_SECTION_ID = 'last_finished_section'
SETTINGS = 'settings'

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
        self.session_lock = threading.Lock()
        self.webservice_user_id = None

    def get_session(self):
        if isinstance(self.session, type(None)):
            self._init_db()
        return self.session
    
    def get_webservice_user_id(self):
        if self.webservice_user_id is None:
            self.webservice_user_id = self.get_session().query(MUser.id).filter(MUser.username=="kib3_webservice",
                                                                    MUser.firstname=="KIB3 Webservice",
                                                                    MUser.lastname=="KIB3 Webservice").first()[0]
        return self.webservice_user_id
    
    def get_moodle_server_time(self, userid: int) -> DateTime:
        """ Returns the current moodle server time as unix timestamp """
        difference = self.get_state(userid, "SERVERTIMEDIFFERENCE")
        return datetime.fromtimestamp(int(time.time()) + difference)

    @PublishSubscribe(pub_topics=['control_event'])
    def open_chatbot(self, user_id: int):
        """ Triggers the UI chatwindow to open """
        if self.check_setting(user_id, 'enabled'):
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

    def check_setting(self, user_id: int, setting_key: str):
        return getattr(self.get_state(user_id, SETTINGS), setting_key)

    def get_wstoken(self, userid: int):
        self.get_state(userid, 'SLIDEFINDERTOKEN')

    def dialog_start(self, user_id: str):
        """
            resets the policy after each dialog
        """
        # set user dialog state
        if not self.get_state(user_id, TURNS):
            self.set_state(user_id, TURNS, 0)
            self.set_state(user_id, LAST_SEARCH, {})
            self.set_state(user_id, LAST_SEARCH, None)
            self.set_state(user_id, LAST_SEARCH_INDEX, 0)
            self.set_state(user_id, REVIEW_QUIZZES, [])
            self.set_state(user_id=user_id, attribute_name=CURRENT_REVIEW_QUIZ, attribute_value=(None, None))
            self.set_state(user_id=user_id, attribute_name=REVIEW_QUIZ_IMPROVEMENTS, attribute_value=[])
            self.set_state(user_id, LAST_FINISHED_SECTION_ID, -1)

            # get user settings
            settings = fetch_user_settings(wstoken=self.get_wstoken(user_id), userid=user_id)
            self.set_state(user_id, SETTINGS, settings)

   

    @PublishSubscribe(sub_topics=["moodle_event"], pub_topics=["sys_acts", "sys_state"])
    def moodle_event(self, user_id: int, moodle_event: dict) -> dict(sys_acts=List[SysAct], sys_state=SysAct):
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
            # check if we finished a whole branch
            # TODO if so, offer congratulations, the review, and then next possibilities?

            # find current section id from course module
            cmid = moodle_event['contextinstanceid']
            section_id, section_name = fetch_section_id_and_name(wstoken=self.get_wstoken(user_id), cmid=cmid)
            branch_review_info = fetch_branch_review_quizzes(wstoken=self.get_wstoken(user_id), userid=user_id, sectionid=section_id)
            self.set_state(user_id, REVIEW_QUIZZES, branch_review_info.candidates)
            if branch_review_info.completed and len(branch_review_info.candidates) > 0:
                # we did complete a full branch, and there are review modules available
                # ask user if they want to review any of the quizzes
                if self.check_setting(user_id, 'openonbranch'):
                    self.open_chatbot(user_id=user_id)
                return {"sys_acts": [
                    SysAct(act_type=SysActionType.CongratulateCompletion, slot_values={"name": branch_review_info.branch, "branch": True}),
                    SysAct(act_type=SysActionType.RequestReviewOrNext)]}
            else:
                # did we complete a full section?
                section_completed = fetch_section_completionstate(wstoken=self.get_wstoken(user_id), userid=user_id, sectionid=section_id)
                if section_completed:
                    # we get this event for each of the modules in a section with different materials (i.e., once for video, once for pdf, once for book):
                    # check that we didn't already offer congratulations, otherwise the autocomplete plugin will trigger this event for each material type
                    last_completed_section_id = self.get_state(user_id, LAST_FINISHED_SECTION_ID)
                    if last_completed_section_id != section_id:
                        self.set_state(user_id, LAST_FINISHED_SECTION_ID, section_id)
                        if self.check_setting(user_id, 'openonsection'):
                            self.open_chatbot(user_id=user_id)
                        sys_acts = [SysAct(SysActionType.CongratulateCompletion, slot_values={"name": section_name, 'branch': False})]
                        sys_acts += self.get_user_next_module(user=self.get_current_user(user_id), courseid=moodle_event['courseid'],
                                                            add_last_viewed_course_module=False, current_section_id=section_id)
                        return {
                            "sys_acts": sys_acts
                        }

        elif event_name == "\\mod_h5pactivity\\event\\statement_received" and moodle_event['component'] == 'mod_h5pactivity':
            current_shown_quiz_id, previous_grade = self.get_state(user_id=user_id, attribute_name=CURRENT_REVIEW_QUIZ)
            if int(moodle_event['contextinstanceid']) == current_shown_quiz_id:
                sys_acts = []
                current_grade = (moodle_event['other']['result']['score']['raw'] / moodle_event['other']['result']['score']['max']) * 100.0
                next_quizzes = self.get_state(user_id=user_id, attribute_name=REVIEW_QUIZZES)
                next_quiz_id, next_quiz_grade = next_quizzes[0] if len(next_quizzes) > 0 else (None, None)
                self.set_state(user_id=user_id, attribute_name=REVIEW_QUIZZES, attribute_value=next_quizzes[1:])
                self.set_state(user_id=user_id, attribute_name=CURRENT_REVIEW_QUIZ, attribute_value=(next_quiz_id, next_quiz_grade))
                improvements = self.get_state(user_id=user_id, attribute_name=REVIEW_QUIZ_IMPROVEMENTS)
                improvements.append(True if current_grade > previous_grade else False)
                self.set_state(user_id=user_id, attribute_name=REVIEW_QUIZ_IMPROVEMENTS, attribute_value=improvements)
                if next_quiz_id:
                    sys_acts.append(self.display_quiz(user_id=user_id, coursemoduleid=next_quiz_id))
                else:
                    # create a graphic summary of how many quizzes the user did better on
                    sys_acts.append(SysAct(act_type=SysActionType.DisplayQuizImprovements, slot_values={"improvements": improvements}))
                    self.resize_chatbot(user_id=user_id, size=ChatbotWindowSize.DEFAULT)
                return {"sys_acts": sys_acts}
            # In the case that the quiz is done outside the chatbot, give feedback (about absolute grade) and offer next quiz (if applicable)
            if self.check_setting(user_id, 'openonquiz'):
                self.open_chatbot(user_id=user_id)
            course_module = self.get_session().query(MCourseModule).get(int(moodle_event['contextinstanceid']))
            success_percentage = (moodle_event['other']['result']['score']['raw'] / moodle_event['other']['result']['score']['max']) * 100.0
            section = course_module.section
            next_quiz_id = section.get_next_available_module(currentModule=course_module, user=self.get_current_user(user_id),
                                                          session=self.get_session(), include_types=['h5pactivity', 'hvp'],
                                                          allow_only_unfinished=True, currentModuleCompletion=True)
            next_quiz_link = next_quiz_id.get_content_link(session=self.get_session(), alternative_display_text="nächste Quiz") if next_quiz_id else None
            return {"sys_acts": [SysAct(act_type=SysActionType.FeedbackToQuiz, slot_values=dict(
                success_percentage=success_percentage,
                next_quiz_link=next_quiz_link
            ))]}             
            # only in review loop comment on improvements, otherwise absolute grade only

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
        self.session_lock.acquire()
        try:
            self.get_session().commit()
        except:
            traceback.print_exc()
        finally:
            self.session_lock.release()

        return dict(best_weekly_days=best_weekly_days,
                  weekly_completions=cumulative_weekly_completions,
                weekly_completions_prev=cumulative_weekly_completions_prev)
    
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
        if self.check_setting(user_id, 'openonlogin'):
            self.open_chatbot(user_id)
        user = self.get_current_user(user_id)
        acts = []

        last_weekly_summaries = self.get_session().query(MChatbotWeeklySummary).filter(MChatbotWeeklySummary._userid==user_id)
        first_turn_ever = last_weekly_summaries.count()

        if first_turn_ever == 0:
            # user is seeing chatbot for the first time - show some introduction

            # create first entry for weekly summaries
            last_weekly_summary = MChatbotWeeklySummary(_userid=user_id, timecreated=self.get_moodle_server_time(user_id), firstweek=True)
            # create first entry for progress summaries
            progress_summary = MChatbotProgressSummary(_userid=user_id, progress=0.0, timecreated=self.get_moodle_server_time(user_id))
            self.session_lock.acquire()
            try:
                self.get_session().add_all([last_weekly_summary, progress_summary])
                self.get_session().commit()
            except:
                traceback.print_exc()
            finally:
                self.session_lock.release()
            # return ice cream game
            icecreamgame_module_id = self.get_session().query(MModule).filter(MModule.name=='icecreamgame').first().id
            icecreamgame_module = self.get_session().query(MCourseModule).filter(MCourseModule._course_id==courseid, MCourseModule._type_id==icecreamgame_module_id).first()
            return [SysAct(act_type=SysActionType.Welcome, slot_values={"first_turn": True}),
                    SysAct(act_type=SysActionType.InformStarterModule, slot_values=dict(
                        module_link=icecreamgame_module.get_content_link(session=self.get_session(), alternative_display_text="hier")
                    ))]
        
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
                self.session_lock.acquire()
                try:
                    self.get_session().commit()
                except:
                    traceback.print_exc()
                finally:
                    self.session_lock.release()
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
            acts.extend(self.get_user_next_module(user=user, courseid=courseid, add_last_viewed_course_module=True))
            
        return acts

    def _handle_request_badge_progress(self, user_id: int, courseid: int, min_progress: float = 0.5) -> SysAct:
        # check what user's next closest badge would be
        closest_badge_info = self.get_current_user(user_id).get_closest_badge(session=self.get_session(), courseid=courseid)
        if not isinstance(closest_badge_info, type(None)):
            badge, badge_progress, badge_status, open_modules = closest_badge_info
            if badge_status == BadgeCompletionStatus.INCOMPLETE and badge_progress >= min_progress:
                # only display progress towards next closest batch if user is sufficiently close
                return SysAct(act_type=SysActionType.DisplayBadgeProgress, slot_values=dict(
                    badge_name=badge.name, percentage_done=badge_progress,
                    missing_activities=[module.get_content_link(session=self.get_session(), alternative_display_text=module.get_name(self.get_session()))
                                        for module in open_modules]
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
        if self.check_setting(user_id, 'openonbadge'):
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
        return SysAct(act_type=SysActionType.DisplayQuiz, slot_values=dict(quiz_embed=hvp_params))
    
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
        book_links, has_more_results = get_book_links(webserviceuserid=self.get_webservice_user_id(), wstoken=self.get_state(user_id, 'SLIDEFINDERTOKEN'), course_id=courseid, searchTerm=search_term, word_context_length=5, start=search_idx, end=search_idx+num_results+1)
        
        self.set_state(user_id=user_id, attribute_name=LAST_SEARCH_INDEX, attribute_value=search_idx + num_results)
        self.set_state(user_id=user_id, attribute_name=LAST_SEARCH, attribute_value=search_term)
        return book_links, has_more_results
    
    def get_most_reviewable_quizzes(self, user_id: int, courseid: int, max_quizzes: int = 3) -> List[Tuple[int, float]]:
        review_grade_items = self.get_current_user(user_id).get_oldest_worst_grade_attempt_quizzes(
            session=self.get_session(),
            courseid=courseid,
            max_results=max_quizzes
        )
        # get corresonding course modules
        return list(map(lambda gradeItem: (self.get_session().query(MH5PActivity).get(gradeItem[0].iteminstance).get_course_module(self.get_session()).id, float(100*gradeItem[1].finalgrade/gradeItem[1].rawgrademax)),
                        review_grade_items))

    @PublishSubscribe(sub_topics=["user_acts", "beliefstate", "courseid"], pub_topics=["sys_acts", "sys_state"])
    def choose_sys_act(self, user_id: str, user_acts: List[UserAct], beliefstate: dict, courseid: int) -> dict(sys_act=SysAct):
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
            for sys_act in sys_acts:
                self.logger.dialog_turn(f"# USER {user_id} # POLICY - {sys_act}")
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
                    # get next quizzes to review, from worst and oldest to better and newer
                    review_candidates = self.get_most_reviewable_quizzes(user_id=user_id, courseid=courseid, max_quizzes=self.check_setting(user_id, 'numreviewquizzes'))
                next_quiz_id, next_quiz_grade = review_candidates[0] if len(review_candidates) > 0 else (None, None)
                self.set_state(user_id=user_id, attribute_name=CURRENT_REVIEW_QUIZ, attribute_value=(next_quiz_id, next_quiz_grade))
                if not next_quiz_id is None:
                    sys_acts.append(self.display_quiz(user_id=user_id, coursemoduleid=next_quiz_id))
                else: 
                    sys_acts.append(SysAct(act_type=SysActionType.DisplayQuiz, slot_values={"quiz_embed": None}))
                self.set_state(user_id, REVIEW_QUIZZES, review_candidates[1:])
            elif user_act.type == UserActionType.RequestNextSection:
                user = self.get_current_user(user_id)
                available_new_course_sections = user.get_available_new_course_sections(session=self.get_session(), courseid=courseid, current_server_time=self.get_moodle_server_time(user_id))
                sys_acts.append(SysAct(act_type=SysActionType.InformNextOptions, slot_values=dict(
                                next_available_sections=[section.get_link() for section in available_new_course_sections]
                        )))
            elif user_act.type == UserActionType.RequestProgress:
                slot_values = self.get_stat_summary(user=self.get_current_user(user_id), courseid=courseid)
                sys_acts.append(SysAct(act_type=SysActionType.DisplayProgress, slot_values=slot_values))
            elif user_act.type == UserActionType.RequestBadgeProgress:
                sys_acts.append(self._handle_request_badge_progress(user_id=user_id, courseid=courseid, min_progress=0.0))
            elif user_act.type == UserActionType.ContinueOpenModules:
                user = self.get_current_user(user_id=user_id)
                sys_acts.extend(self.get_user_next_module(user=user, courseid=courseid))
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
            self.set_state(user_id=user_id, attribute_name=CURRENT_REVIEW_QUIZ, attribute_value=(None, None))
            self.set_state(user_id=user_id, attribute_name=REVIEW_QUIZ_IMPROVEMENTS, attribute_value=[]) 
            self.resize_chatbot(user_id=user_id, size=ChatbotWindowSize.DEFAULT)
        sys_state["last_act"] = sys_acts
        self.logger.dialog_turn(f"# USER {user_id} # POLICY - {sys_acts}")
        return {'sys_acts':  sys_acts, "sys_state": sys_state}
    
    def get_current_user(self, user_id) -> MUser:
            """ Get Moodle user by id from Chat Interface (or start run_chat with --user_id=...) """
            user = self.get_session().get(MUser, int(user_id))
            return user
    
    def get_user_next_module(self, user: MUser, courseid: int, add_last_viewed_course_module: bool = False, current_section_id: int = None) -> List[SysAct]:
        # choose how to proceed
        acts = []
        has_seen_any_course_modules = self.get_session().query(MCourseModulesViewed).join(MCourseModule, MCourseModule.id==MCourseModulesViewed._coursemoduleid) \
                                    .filter(MCourseModulesViewed._userid==user.id, MCourseModule._course_id==courseid).count() > 0
        all_sections_completed = False
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
                    if not unfinished_module._section_id in next_modules and unfinished_module._section_id != current_section_id:
                        next_modules[unfinished_module._section_id] = unfinished_module
                # fill with other started sections
                for completed_module in last_completed_course_modules:
                    if not completed_module._section_id in next_modules and completed_module._section_id != current_section_id:
                        # get first open module from this section
                        next_module = completed_module.section.get_first_available_module(user=user, session=self.get_session(),
                                                                            include_types=learning_material_types + assignment_material_types,
                                                                            allow_only_unfinished=True)
                        if next_module:
                            next_modules[completed_module._section_id] = next_module
                next_available_module_links = [module.get_content_link(session=self.get_session(), alternative_display_text=module.section.name) for module in next_modules.values()]

                # user has started, but not completed one or more sections
                if add_last_viewed_course_module:
                    acts.append(SysAct(act_type=SysActionType.InformLastViewedCourseModule, slot_values=dict(
                        last_viewed_course_module=last_completed_course_module.get_content_link(session=self.get_session()),
                    )))
                if len(next_available_module_links) > 0:
                    acts.append(
                            SysAct(act_type=SysActionType.RequestContinueOrNext, slot_values=dict(
                                    next_available_modules=next_available_module_links
                            )))
                else:
                    all_sections_completed = True
            # TODO: Forum post info
            # TODO: Deadline reminder
            if all_sections_completed:
                # user has completed all started sections, should get choice of next new and available sections
                available_new_course_sections = user.get_available_new_course_sections(session=self.get_session(), courseid=courseid, current_server_time=self.get_moodle_server_time(user.id))
                acts.append(SysAct(act_type=SysActionType.InformNextOptions, slot_values=dict(
                                next_available_sections=[section.get_link() for section in available_new_course_sections]
                        )))
        else:
            # return ice cream game
            icecreamgame_module_id = self.get_session().query(MModule).filter(MModule.name=='icecreamgame').first().id
            icecreamgame_module = self.get_session().query(MCourseModule).filter(MCourseModule._course_id==courseid, MCourseModule._type_id==icecreamgame_module_id).first()
            acts.append(SysAct(act_type=SysActionType.InformStarterModule, slot_values=dict(
                module_link=icecreamgame_module.get_content_link(session=self.get_session(), alternative_display_text="hier")
            )))
        return acts
    
    
   
 