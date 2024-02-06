import os


MOOLDE_SERVER_PROTOCOL = "https" if os.environ['MOODLE_SERVER_SSL'] == 'true' else "http" # change this to HTTP or HTTPS (or set the environemnt variable)
MOODLE_SERVER_WEB_HOST = "webserver" # IP Adress / domain (and port, if not default 80) of moodle webserver, e.g. "myaddress.com", "myaddress:1234" (excluding protocol)

##
## INTERNAL CONFIGURATION
##
DS_SERVER_IP_ADDR = "127.0.0.1"    # IP address of dialog system backend (for internal communication; should stay localhost)
