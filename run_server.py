import time
from typing import List
import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import asyncio

import config
from services.service import PublishSubscribe, Service, DialogSystem
# from utils.logger import DiasysLogger, LogLevel

io_loop = tornado.ioloop.IOLoop.current()
asyncio.set_event_loop(io_loop.asyncio_loop)

logger = None #DiasysLogger(name="userlog", console_log_lvl=LogLevel.ERRORS, file_log_lvl=LogLevel.DIALOGS)

def load_elearning_domain():
    print("LOADING ELEARNING DOMAIN")
    from elearning.policy_ELearning import ELearningPolicy
    from elearning.eLearningBst import ELearningBST
    from elearning.dbloggerhandler import DBLoggingHandler
    from services.nlg.nlg import ELearningNLG
    from services.nlu.nlu import ELearningNLU
    domain = 'ELearning'
    e_learning_nlu = ELearningNLU(domain=domain, logger=logger)
    e_learning_policy = ELearningPolicy(domain=domain, logger=logger)
    e_learning_bst = ELearningBST(domain=domain)
    e_learning_nlg = ELearningNLG(domain=domain, logger=logger)
    e_learning_logger = DBLoggingHandler(domain=domain)
    return domain, [e_learning_nlu, e_learning_bst, e_learning_policy, e_learning_nlg, e_learning_logger]

#  setup dialog system
domain_1, services_1 = load_elearning_domain()

import asyncio
class GUIServer(Service):
    NOT_FIRST_TURN = "NOT_FIRST_TURN"

    def __init__(self, domains, logger):
        super().__init__(domain="")
        self.websockets = {}
        self.domains = domains
        self.logger = logger

    def log_dialog_turn(self, msg: str):
        if not isinstance(self.logger, type(None)):
            self.logger.dialog_turn(msg)

    @PublishSubscribe(sub_topics=['socket_opened'], pub_topics=['user_utterance', 'sys_state'])
    def on_socket_opened(self, user_id: str, socket_opened: bool = True):
        """ If page (re-)load/transition is registered (websocket (re-)connected),
            we check if the current session state contains chat history for the given user already.
            If not, we start a new dialog by publishing an empty user_utterance and sys_state message to the backend.
        """
        if not socket_opened:
            return

        not_first_turn = self.get_state(user_id, GUIServer.NOT_FIRST_TURN)
        if not_first_turn:
            # check if history contains missed messages
            # if so, send and clear buffer
            missed = self.get_state(user_id, "MISSED_MESSAGES")
            if missed is not None:
                for msg in missed:
                    io_loop.asyncio_loop.call_soon_threadsafe(self.websockets[user_id].write_message, json.dumps([{"content": msg, "format": "text", "party": "system"}]))
                self.set_state(user_id, "MISSED_MESSAGES", None)
        else:
            # chat history not found, start new dialog in backend
            self.set_state(user_id, GUIServer.NOT_FIRST_TURN, True)
            return {f'user_utterance/{self.domains[0]}': '', f'sys_state/{self.domains[0]}': {}}


    @PublishSubscribe(pub_topics=['user_utterance', 'courseid'])
    def user_utterance(self, user_id, domain_idx = 0, courseid=0, message = ""):
        try:
            self.log_dialog_turn(f"# USER {user_id} # USR-UTTERANCE - {message}")

            # forward message from moodle frontend to dialog system backend
            return {f'user_utterance/{self.domains[domain_idx]}': message,
                    f'courseid/{self.domains[domain_idx]}': courseid}
        except:
            print("ERROR in GUIService - user_utterance: user=", user_id, "domain_idx=", domain_idx, "message=", message)
            import traceback
            import sys
            traceback.print_exc(file=sys.stdout)
            return {}
        
    @PublishSubscribe(pub_topics=['moodle_event'])
    def moodle_event(self, user_id, domain_idx=0, event_data: dict = None):
        if 'eventname' in event_data and event_data['eventname'].lower().strip() == "\\core\\event\\user_loggedin":
            # clear chat history when user logs back in
            self.clear_memory(user_id)
        return {f'moodle_event/{self.domains[domain_idx]}': event_data}
    
    @PublishSubscribe(pub_topics=['settings'])
    def settings_changed(self, user_id, domain_idx=0, settings: dict = None):
        return {f'settings/{self.domains[domain_idx]}': settings} 

    @PublishSubscribe(sub_topics=['control_event'])
    def forward_control_event_to_websocket(self, user_id, control_event: str = None):
        user_id = int(user_id)
        if not user_id in self.websockets:
            # store messages during page transition where socket is closed
            # print("MISSED MSG", sys_utterance)
            pass
        else:
            # forward message to moodle frontend
            io_loop.asyncio_loop.call_soon_threadsafe(self.websockets[user_id].write_message, json.dumps([{"content": control_event, "format": "text", "party": "control"}]))

    @PublishSubscribe(sub_topics=['sys_utterance'])
    def forward_message_to_websocket(self, user_id, sys_utterance: List[str] = None):
        user_id = int(user_id)

        for message in sys_utterance:
            if not user_id in self.websockets:
                # store messages during page transition where socket is closed
                missed = self.get_state(user_id, "MISSED_MESSAGES")
                if missed is None:
                    missed = []
                missed.append(message)
                self.set_state(user_id, "MISSED_MESSAGES", missed)
            else:
                # forward message to moodle frontend
                io_loop.asyncio_loop.call_soon_threadsafe(self.websockets[user_id].write_message, json.dumps([{"content": message, "format": "text", "party": "system"}]))


# setup dialog system
domains = [domain_1]
gui_service = GUIServer(domains, logger)
services = [gui_service]
services.extend(services_1)
ds = DialogSystem(services=services)
error_free = ds.is_error_free_messaging_pipeline()
if not error_free:
    ds.print_inconsistencies()
# ds.draw_system_graph()
print('setup system')


class SimpleWebSocket(tornado.websocket.WebSocketHandler):
    """ Websocket for communication between frontend and backend """ 
    def _extract_token(self, uri):
        start=len("/ws?token=")
        return int(uri[start:])

    def log_dialog_turn(self, msg: str):
        if not isinstance(logger, type(None)):
            logger.dialog_turn(msg)

    def open(self, *args):
        # print("openng connection")
        self.userid = self._extract_token(self.request.uri)
        self.log_dialog_turn(f"# USER {self.userid} # SERVER - Connecting")
        if self.userid:
            gui_service.websockets[self.userid] = self
 
    def on_message(self, message):
        data = json.loads(message)
        # print("got message", data)
        if self.userid:
            print("RECEIVED DATA:", data)
            topic = data['topic']
            domain_index = data['domain']
            courseid = int(data['courseid'])
            if topic == 'start_dialog':
                self.log_dialog_turn(f"# USER {self.userid} # DIALOG-START")
                # Set webservice token for the POLICY state
                slidefindertoken = data['slidefindertoken']
                wsuserid = data['wsuserid']
                moodle_timestamp = int(data['timestamp'])
                time_diff_chatbot_moodle = moodle_timestamp - int(time.time()) # add this constant difference to chatbot time to get moodle server time
                print(" - slidefindertoken", slidefindertoken)
                print(" - moodle timestamp", moodle_timestamp)
                print(" - time difference moodle-chatbot", time_diff_chatbot_moodle)
                services_1[2].set_state(self.userid, "SLIDEFINDERTOKEN", slidefindertoken)
                services_1[2].set_state(self.userid, "SERVERTIMESTAMP", moodle_timestamp)
                services_1[2].set_state(self.userid, "WSUSERID", wsuserid)
                services_1[2].set_state(self.userid, "SERVERTIMEDIFFERENCE", time_diff_chatbot_moodle)
                services_1[-1].set_state(self.userid, "SLIDEFINDERTOKEN", slidefindertoken)

                ds._start_dialog(start_signals={f'socket_opened/{domains[domain_index]}': True, f'courseid/{domains[domain_index]}': courseid}, user_id=self.userid)
            elif topic == 'user_utterance':
                gui_service.websockets[self.userid] = self # set active websocket to last interaction (user might have multiple tabs open)
                gui_service.user_utterance(user_id=self.userid, domain_idx=domain_index, courseid=courseid, message=data['msg'])
    
    def on_close(self):
        # find right connection to delete
        self.log_dialog_turn(f"# USER {self.userid} # SOCKET-CLOSE")
        if self.userid in gui_service.websockets:
           del gui_service.websockets[self.userid]

    def check_origin(self, *args, **kwargs):
        # allow cross-origin
        return True

class MoodleEventHandler(tornado.web.RequestHandler):
    def get(self):
        pass
        # self.write("GET: Hello, world")

    def post(self):
        event_data = json.loads(self.request.body)
        # print("GOT MOODLE EVENT", event_data)
        
        user_id = int(event_data['userid'])
        gui_service.moodle_event(user_id=user_id, event_data=event_data)


class UserSettingsHandler(tornado.web.RequestHandler):
    def get(self):
        pass

    def post(self):
        settings_data = json.loads(self.request.body)
        user_id = int(settings_data.pop("userid"))
        gui_service.settings_changed(user_id=user_id, settings=settings_data)

def make_app():
    return tornado.web.Application([
        (r"/ws", SimpleWebSocket),
        (r"/event", MoodleEventHandler),
        (r"/usersettings", UserSettingsHandler)
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(config.DS_SERVER_PORT)
    print("Starting tornado...")
    tornado.ioloop.IOLoop.current().start()
