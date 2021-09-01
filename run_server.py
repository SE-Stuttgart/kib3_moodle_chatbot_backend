import datetime
from datetime import timedelta, datetime
from passlib.context import CryptContext
import jwt
import tornado.ioloop
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


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

class User():
    def __init__(self, userid, hashed_password, disabled):
        super().__init__()
        self.userid = userid
        self.hashed_password = hashed_password
        self.disabled = disabled


# TODO connect to django models
def get_user(conn, userid: str):
    try:
        # cursor = conn.cursor()
        # cursor.execute("SELECT * FROM Users WHERE userid=?", (userid,))
        # result = cursor.fetchone()
        # if result:
        #     return User(userid=userid, hashed_password=result[1], disabled=result[2])
        return User(userid=12345, hashed_password='12345', disabled=False)
    except:
        pass
    finally:
        pass
        # cursor.close()
    return None

# TODO
def authenticate_user(conn, userid: str, password: str):
    user = get_user(conn, userid)
    if not user:
        print(f"ACCESS WARNING: user '{userid}' not in DB")
        return False
    if not verify_password(password, user.hashed_password):
        print(f"ACCESS WARNING: wrong password for user '{userid}'")
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt.decode("utf-8")

def user_from_token(token):
    """ Extract userid from token, if token is still valid.
    If user is registered + token is not expired, returns userid
    else, return None
    """
    try:
        # TODO fix with real tokens
        return '12345'
        # automatically checks expired property
        jwt_payload = jwt.decode(token, SECRET_KEY, verify=True, algorithm=ALGORITHM)
        if 'userid' in jwt_payload:
            return jwt_payload['userid']
    except:
        pass
    return None


class CorsJsonHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        # allow requests from anywhere (CORS)
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with,access-control-allow-origin,authorization,content-type")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def options(self):
        # no body
        self.set_status(204)
        self.finish()
    
    def prepare(self):
        # extract json
        if self.request.headers.get("Content-Type", "").startswith("application/json"):
            self.json_args = json.loads(self.request.body)
        else:
            self.json_args = None


class LoginHandler(CorsJsonHandler):
    def post(self):
        if self.json_args:
            userid = self.json_args['userid']
            pwd_plaintext = self.json_args['pwd']
            user = authenticate_user(None, userid, pwd_plaintext)
            if user:
                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(data={"userid": userid}, expires_delta=access_token_expires)
                self.write({"access_token": access_token})
                self.set_status(200)
            else:
                self.set_status(401, reason="Unauthorized")
        else:
            self.set_status(402, reason="Expected JSON")
        self.finish()

class RegisterHandler(CorsJsonHandler):
    def post(self):
        if self.json_args:
            userid = self.json_args['userid']
            pwd_plaintext = self.json_args['pwd']

            print("registering user", userid)
            if get_user(None, userid):
                print(f"user {userid} already exists")
                self.set_status(401, reason="User already exists")
            # else:
            #     if not insert_user(None, userid=userid, pwd_plaintext=pwd_plaintext):
            #         self.set_status(402, reason="Error while creating new User")
        else:
            self.set_status(403, reason="Expected JSON")
        self.finish() 

def load_lecturer_domain():
    from services.nlu.nlu import HandcraftedNLU
    from services.bst import HandcraftedBST
    from services.nlg.nlg import HandcraftedNLG
    from services.policy import HandcraftedPolicy 
    from utils.domain.jsonlookupdomain import JSONLookupDomain
    domain = JSONLookupDomain('ImsLecturers', display_name="Lecturers")
    lect_nlu = HandcraftedNLU(domain=domain, logger=logger)
    lect_bst = HandcraftedBST(domain=domain)
    lect_policy = HandcraftedPolicy(domain=domain, logger=logger)
    lect_nlg = HandcraftedNLG(domain=domain, logger=logger)
    return domain, [lect_nlu, lect_bst, lect_policy, lect_nlg]

#  setup dialog system
domain_1, services_1 = load_lecturer_domain()

import asyncio
class GUIServer(Service):
    def __init__(self, domains, logger):
        super().__init__(domain="")
        self.websockets = {}
        self.domains = domains
        self.logger = logger

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
    def forward_message_to_react(self, user_id = "default", sys_utterance = None):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.websockets[user_id].write_message(sys_utterance)

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
        token = self._extract_token(self.request.uri)
        print(' - token', token)
        userid = user_from_token(token)
        print(' - user', userid)
        if userid:
            gui_service.websockets[userid] = self
 
    def on_message(self, message):
        data = json.loads(message)
        print("got message", data)
        # check token validity
        user_id = user_from_token(data['access_token'])
        print(' - user id', user_id)
        if user_id:
            topic = data['topic']
            domain_index = data['domain']
            print(" - domain index", domain_index)
            if topic == 'start_dialog':
                logger.dialog_turn(f"# USER {user_id} # DIALOG-START ({domains[domain_index].get_domain_name()})")
                ds._start_dialog(start_signals={f'user_utterance/{domains[domain_index].get_domain_name()}': ''}, user_id=user_id)
            elif topic == 'user_utterance':
                gui_service.user_utterance(user_id=user_id, domain_idx=domain_index, message=data['msg'])
    
    def on_close(self):
        print('closing')
        # find right connection to delete
        for userid in gui_service.websockets:
            if gui_service.websockets[userid] == self:
                logger.dialog_turn(f"# USER {userid} # SOCKET-CLOSE")
                del gui_service.websockets[userid]
                break

    def check_origin(self, *args, **kwargs):
        # allow cross-origin
        return True


def make_app():
    return tornado.web.Application([
        # (r"/login", LoginHandler),
        # (r"/register", RegisterHandler),
        (r"/ws", SimpleWebSocket)
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(44123)
    tornado.ioloop.IOLoop.current().start()
