import os


MOOLDE_SERVER_PROTOCOL = "https" if os.environ['MOODLE_SERVER_SSL'] == 'true' else "http" # change this to HTTP or HTTPS (or set the environemnt variable)
MOODLE_SERVER_WEB_HOST = "webserver" # IP Adress / domain (and port, if not default 80) of moodle webserver, e.g. "myaddress.com", "myaddress:1234" (excluding protocol)
DS_SERVER_PORT = 44123 # Port under which the chatbot should accept websocket connections / http requests

# SSL OPTIONS
if MOOLDE_SERVER_PROTOCOL == "https":
    SSL_CERT_FILE = "/etc/ssl/certs/" + os.environ['MOODLE_SERVER_SSL_CERTIFICATE_FILE'] # Full path to SSL certificate file, e.g. "/etc/ssl/certs/mycertificate.crt"
    SSL_PRIVATE_KEY_FILE = "/etc/ssl/private/" + os.environ['MOODLE_SERVER_SSL_PRIVATE_KEY_FILE'] # Full path to SSL key file, e.g. "/etc/ssl/private/mykey.key"

##
## INTERNAL CONFIGURATION
##
DS_SERVER_IP_ADDR = "127.0.0.1"    # IP address of dialog system backend (for internal communication; should stay localhost)
