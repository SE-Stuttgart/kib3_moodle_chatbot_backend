import time
from typing import List, Tuple
from elearning.moodledb import UserSettings, api_call, fetch_user_settings

from services.service import PublishSubscribe, Service
from utils.useract import UserAct

ALLOW_LOGGING = 'allow_logging'

class DBLoggingHandler(Service):
    def __init__(self, domain: str) -> None:
        super().__init__(domain=domain)

    def _log(self, userid: int, courseid: int, speaker: str, message: str, act: str):
        # don't bother waiting for response (is only ACK=true)
        api_call(wstoken=self.get_state(userid, "BOOKSEARCHTOKEN"), wsfunction="block_chatbot_log_interaction", params=dict(
            userid=userid,
            courseid=courseid,
            speaker=speaker,
            message=message,
            act=act
        ))

    def get_wstoken(self, userid: int):
        return self.get_state(userid, 'BOOKSEARCHTOKEN')

    @PublishSubscribe(sub_topics=["settings"])
    def settings_changed(self, user_id: int, settings: dict):
        settings = UserSettings(**settings)
        self.set_state(user_id, ALLOW_LOGGING, settings.logging)

    def check_log_allowed(self, userid: int) -> bool:
        """ Check if the user allowed logging. """
        allow_logging = self.get_state(userid, ALLOW_LOGGING)
        if allow_logging is None:
            settings = fetch_user_settings(wstoken=self.get_wstoken(userid), userid=userid)
            allow_logging = settings.logging
            self.set_state(userid, ALLOW_LOGGING, allow_logging)
        return allow_logging

    @PublishSubscribe(sub_topics=["courseid", 'user_utterance', 'user_acts'])
    def log_user_utterance(self, user_id: int, courseid: int, user_utterance: str, user_acts: List[UserAct]):
        if not self.check_log_allowed(user_id):
            return
        for act in user_acts:
            self._log(userid=user_id, courseid=courseid, speaker="USER", message=user_utterance, act=act.type.name)
          

    @PublishSubscribe(sub_topics=['courseid', 'sys_utterance'])
    def log_sys_utterance(self, user_id: int, courseid: int, sys_utterance: List[Tuple[str, List[str]]]):
        if not self.check_log_allowed(user_id):
            return
        for utterance_tuple in sys_utterance:
            self._log(userid=user_id, courseid=courseid, speaker="SYSTEM", message=utterance_tuple[0].replace("\n", " "), act="")


    # @PublishSubscribe(sub_topics=["moodle_event"])
    # def log_moodle_event(self, user_id: int, moodle_event: dict):
        # if not self.check_log_allowed(user_id):
        #     return
        # event_name = moodle_event['eventname'].lower().strip()
        # if event_name == "\\core\\event\\user_loggedin":
        #     log_item = MChatbotHistory(timecreated=self.get_moodle_server_time(user_id),
        #                             speaker="MOODLE_EVENT",
        #                             message="",
        #                             act="\\core\\event\\user_loggedin",
        #                             _userid=user_id)
        #     self.session_lock.acquire()
        #     try:
        #         self.get_session().add(log_item)
        #         self.get_session().commit()
        #     except:
        #         traceback.print_exc()
        #     finally:
        #         self.session_lock.release()
        # elif event_name == "\\core\\event\\user_loggedout":
        #     log_item = MChatbotHistory(timecreated=self.get_moodle_server_time(user_id),
        #                             speaker="MOODLE_EVENT",
        #                             message="",
        #                             act="\\core\\event\\user_loggedout",
        #                             _userid=user_id)
        #     self.session_lock.acquire()
        #     try:
        #         self.get_session().add(log_item)
        #         self.get_session().commit()
        #     except:
        #         traceback.print_exc()
        #     finally:
        #         self.session_lock.release()