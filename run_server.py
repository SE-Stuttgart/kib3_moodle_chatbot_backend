import datetime
from datetime import timedelta, datetime
from passlib.context import CryptContext
import jwt
import tornado.ioloop
import tornado.web
import tornado.websocket
import json

from services.service import PublishSubscribe, Service, DialogSystem
from utils.logger import DiasysLogger, LogLevel

# to get a string like this run: openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = DiasysLogger(name="userlog", console_log_lvl=LogLevel.ERRORS, file_log_lvl=LogLevel.DIALOGS)


def load_nlg(domain=None):
    from services.nlg.nlg import HandcraftedNLG
    nlg = HandcraftedNLG(domain=domain)
    return nlg

def load_elearning_domain():
    from utils.domain.jsonlookupdomain import JSONLookupDomain
    from elearning.policy_ELearning import ELearningPolicy
    from elearning.eLearningBst import ELearningBST
    from services.nlu.nlu import HandcraftedNLU
    domain = JSONLookupDomain('ELearning', display_name="ELearning")
    e_learning_nlu = HandcraftedNLU(domain=domain)
    e_learning_policy = ELearningPolicy(domain=domain)
    e_learning_bst = ELearningBST(domain=domain)
    e_learning_nlg = load_nlg(domain=domain)
    return domain, [e_learning_nlu, e_learning_bst, e_learning_policy, e_learning_nlg]

#  setup dialog system
domain_1, services_1 = load_elearning_domain()

import asyncio
class GUIServer(Service):
    def __init__(self, domains, logger):
        super().__init__(domain="")
        self.websockets = {}
        self.domains = domains
        self.logger = logger
        self.loopy_loop = asyncio.new_event_loop()

    @PublishSubscribe(pub_topics=['user_utterance'])
    def user_utterance(self, user_id = "default", domain_idx = 0, message = ""):
        try:
            self.logger.dialog_turn(f"# USER {user_id} # USR-UTTERANCE ({self.domains[domain_idx].get_domain_name()}) - {message}")
            # forward_message_from_react('gen_user_utterance', message)
            return {f'user_utterance/{self.domains[domain_idx].get_domain_name()}': message}
        except:
            print("ERROR in GUIService - user_utterance: user=", user_id, "domain_idx=", domain_idx, "message=", message)
            import traceback
            import sys
            traceback.print_exc(file=sys.stdout)
            return {}

    @PublishSubscribe(sub_topics=['sys_utterance'])
    def forward_message_to_websocket(self, user_id = "default", sys_utterance: str = None):
        asyncio.set_event_loop(self.loopy_loop)
        self.websockets[user_id].write_message(json.dumps({"content": sys_utterance, "format": "text"}))

    
    @PublishSubscribe(sub_topics=['html_content'])
    def forward_html_to_websocket(self, user_id = "default", html_content: str = None):
        asyncio.set_event_loop(self.loopy_loop)
        self.websockets[user_id].write_message(json.dumps({'content': html_content, "format": "html"}))

    @PublishSubscribe(pub_topics=['moodle_event'])
    def moodle_event(self, user_id = 'default', domain_idx=0, event_data: dict = None):
        asyncio.set_event_loop(self.loopy_loop)
        return {f'moodle_event/{self.domains[domain_idx].get_domain_name()}': event_data}


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
    def _extract_token(self, uri):
        start=len("/ws?token=")
        return uri[start:]

    def open(self, *args):
        print("opening connection")
        self.userid = self._extract_token(self.request.uri)
        print(' - user', self.userid)
        if self.userid:
            gui_service.websockets[self.userid] = self
 
    def on_message(self, message):
        data = json.loads(message)
        print("got message", data)
        # print("user ids correct?", data['userid'] == self.userid)
        if self.userid:
            topic = data['topic']
            domain_index = data['domain']
            print(" - domain index", domain_index)
            if topic == 'start_dialog':
                logger.dialog_turn(f"# USER {self.userid} # DIALOG-START ({domains[domain_index].get_domain_name()})")
                ds._start_dialog(start_signals={f'user_utterance/{domains[domain_index].get_domain_name()}': '', "sys_state/ELearning": {}}, user_id=self.userid)
            elif topic == 'user_utterance':
                gui_service.user_utterance(user_id=self.userid, domain_idx=domain_index, message=data['msg'])
    
    def on_close(self):
        print('closing')
        # find right connection to delete
        if self.userid in gui_service.websockets:
            logger.dialog_turn(f"# USER {self.userid} # SOCKET-CLOSE")
            del gui_service.websockets[self.userid]

    def check_origin(self, *args, **kwargs):
        # allow cross-origin
        return True

class MoodleEventHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("GET: Hello, world")

    def post(self):
        event_data = json.loads(self.request.body)
        print("GOT MOODLE EVENT", event_data)
        
        user_id = event_data['userid']
        gui_service.moodle_event(user_id=user_id, event_data=event_data)

def make_app():
    return tornado.web.Application([
        (r"/ws", SimpleWebSocket),
        (r"/event", MoodleEventHandler)
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(44123)
    print("Starting tornado...")
    tornado.ioloop.IOLoop.current().start()
