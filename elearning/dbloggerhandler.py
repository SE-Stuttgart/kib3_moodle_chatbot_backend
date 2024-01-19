import time
from datetime import datetime
from typing import List, Tuple

from services.service import PublishSubscribe, Service
from utils.useract import UserAct

SETTING_ALLOW_LOGGING = 'setting_allow_logging'

class DBLoggingHandler(Service):
    def __init__(self, domain: str) -> None:
        super().__init__(domain=domain)
        # self.session = None
        # self.session_lock = threading.Lock()
    
   
    def dialog_start(self, user_id: str):
        self.set_state(user_id, SETTING_ALLOW_LOGGING, None)

    def check_log_allowed(self, userid: int) -> bool:
        """ Check if the user allowed logging. """
        # allow_logging = self.get_state(userid, SETTING_ALLOW_LOGGING)
        # if allow_logging is None:
        #     allow_logging = self.get_session().query(MUserSettings).filter(MUserSettings._userid==userid).first().logging
        #     self.set_state(userid, SETTING_ALLOW_LOGGING, allow_logging)
        # return allow_logging
        return False

    def get_moodle_server_time(self, userid: int) -> datetime:
        """ Returns the current moodle server time as unix timestamp """
        difference = self.get_state(userid, "SERVERTIMEDIFFERENCE")
        return datetime.fromtimestamp(int(time.time()) + difference)
    
    @PublishSubscribe(sub_topics=['user_utterance', 'user_acts'])
    def log_user_utterance(self, user_id: int, user_utterance: str, user_acts: List[UserAct]):
        # TODO re-enable logging
        # if not self.check_log_allowed(user_id):
        #     return
        # log_items = []
        # for act in user_acts:
        #     log_items.append(MChatbotHistory(timecreated=self.get_moodle_server_time(user_id),
        #                             speaker="USER",
        #                             message=user_utterance,
        #                             act=act.type.name,
        #                             _userid=user_id))
        # self.session_lock.acquire()
        # try:
        #     self.get_session().add_all(log_items)
        #     self.get_session().commit()
        # except:
        #     traceback.print_exc()
        # finally:
        #     self.session_lock.release()
        pass


    @PublishSubscribe(sub_topics=['sys_utterance'])
    def log_sys_utterance(self, user_id: int, sys_utterance: List[Tuple[str, List[str]]]):
        # TODO re-enable logging
        # if not self.check_log_allowed(user_id):
        #     return
        # log_items = []
        # for utterance_tuple in sys_utterance:
        #     log_items.append(MChatbotHistory(timecreated=self.get_moodle_server_time(user_id),
        #                             speaker="SYSTEM",
        #                             message=utterance_tuple[0].replace("\n", " "),
        #                             act="",
        #                             _userid=user_id))
        # self.session_lock.acquire()
        # try:
        #     self.get_session().add_all(log_items)
        #     self.get_session().commit()
        # except:
        #     traceback.print_exc()
        # finally:
        #     self.session_lock.release()
        pass


    @PublishSubscribe(sub_topics=["moodle_event"])
    def log_moodle_event(self, user_id: int, moodle_event: dict):
        # TODO re-enable logging
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
        pass