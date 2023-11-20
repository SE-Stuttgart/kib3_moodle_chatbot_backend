import threading
import time
from datetime import datetime
import traceback
from typing import List, Tuple

from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.sqltypes import DateTime

from elearning.moodledb import Base, MChatbotHistory, connect_to_moodle_db
from services.service import PublishSubscribe, Service
from utils.useract import UserAct

class DBLoggingHandler(Service):
    def __init__(self, domain: str) -> None:
        super().__init__(domain=domain)
        self.session = None
        self.session_lock = threading.Lock()
    
    def get_session(self):
        if isinstance(self.session, type(None)):
            self._init_db()
        return self.session
   
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
    # TODO set moodle server time difference

    def get_moodle_server_time(self, userid: int) -> DateTime:
        """ Returns the current moodle server time as unix timestamp """
        difference = self.get_state(userid, "SERVERTIMEDIFFERENCE")
        return datetime.fromtimestamp(int(time.time()) + difference)
    
    @PublishSubscribe(sub_topics=['user_utterance', 'user_acts'])
    def log_user_utterance(self, user_id: int, user_utterance: str, user_acts: List[UserAct]):
        log_items = []
        for act in user_acts:
            log_items.append(MChatbotHistory(timecreated=self.get_moodle_server_time(user_id),
                                    speaker="USER",
                                    message=user_utterance,
                                    act=act.type.name,
                                    _userid=user_id))
        self.session_lock.acquire()
        try:
            self.get_session().add_all(log_items)
            self.get_session().commit()
        except:
            traceback.print_exc()
        finally:
            self.session_lock.release()


    @PublishSubscribe(sub_topics=['sys_utterance'])
    def log_sys_utterance(self, user_id: int, sys_utterance: List[Tuple[str, List[str]]]):
        log_items = []
        for utterance_tuple in sys_utterance:
            log_items.append(MChatbotHistory(timecreated=self.get_moodle_server_time(user_id),
                                    speaker="SYSTEM",
                                    message=utterance_tuple[0].replace("\n", " "),
                                    act="",
                                    _userid=user_id))
        self.session_lock.acquire()
        try:
            self.get_session().add_all(log_items)
            self.get_session().commit()
        except:
            traceback.print_exc()
        finally:
            self.session_lock.release()


    @PublishSubscribe(sub_topics=["moodle_event"])
    def log_moodle_event(self, user_id: int, moodle_event: dict):
        event_name = moodle_event['eventname'].lower().strip()
        if event_name == "\\core\\event\\user_loggedin":
            log_item = MChatbotHistory(timecreated=self.get_moodle_server_time(user_id),
                                    speaker="MOODLE_EVENT",
                                    message="",
                                    act="\\core\\event\\user_loggedin",
                                    _userid=user_id)
            self.session_lock.acquire()
            try:
                self.get_session().add(log_item)
                self.get_session().commit()
            except:
                traceback.print_exc()
            finally:
                self.session_lock.release()
        elif event_name == "\\core\\event\\user_loggedout":
            log_item = MChatbotHistory(timecreated=self.get_moodle_server_time(user_id),
                                    speaker="MOODLE_EVENT",
                                    message="",
                                    act="\\core\\event\\user_loggedout",
                                    _userid=user_id)
            self.session_lock.acquire()
            try:
                self.get_session().add(log_item)
                self.get_session().commit()
            except:
                traceback.print_exc()
            finally:
                self.session_lock.release()