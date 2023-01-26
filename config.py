

MOODLE_SERVER_IP_ADDR = "localhost:80/moodle"    # IP address of moodle server
MOODLE_SERVER_PORT = None    # Port of moodle webserver (default: 8080, or set to None)
MOODLE_SERVER_DB_ADDR = "127.0.0.1"  # IP address of moodle database (e.g. same as web server IP if running on the same server)
MOODLE_SERVER_DB_PORT = "3306"  # Port of moodle database (default for mysql: 3306)
MOODLE_SERVER_DB_TALBE_PREFIX = "mdl_" # Prefix in Moodle Database Tables (e.g. m_, mdl_, ...)
MOODLE_WSTOKEN = "13c3113a17b0d45a0016aec1216eaf34" # Token for Moodle web services

DS_SERVER_IP_ADDR = "127.0.0.1"    # IP address of dialog system

def MOODLE_SERVER_ADDR():
    if MOODLE_SERVER_PORT:
        return f"{MOODLE_SERVER_IP_ADDR}:{MOODLE_SERVER_PORT}"
    return MOODLE_SERVER_IP_ADDR