import os


MOOLDE_SERVER_PROTOCOL = "https" if os.environ['MOODLE_SERVER_SSL'] == 'true' else "http" # change this to HTTP or HTTPS (or set the environemnt variable)
MOODLE_SERVER_WEB_HOST = "webserver" # IP Adress / domain (and port, if not default 80) of moodle webserver, e.g. "myaddress.com", "myaddress:1234" (excluding protocol)
DS_SERVER_PORT = 44123 # Port under which the chatbot should accept websocket connections / http requests

##
## INTERNAL CONFIGURATION
##
DS_SERVER_IP_ADDR = "127.0.0.1"    # IP address of dialog system backend (for internal communication; should stay localhost)
