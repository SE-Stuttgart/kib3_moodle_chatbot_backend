import os

MOODLE_SERVER_WEB_HOST = "webserver" # IP Adress of moodle webserver 
MOODLE_SERVER_WEB_PORT = os.environ['MOODLE_DOCKER_WEB_PORT']    # Port of moodle webserver (default: 8080, or set to None)
MOODLE_SERVER_IP_ADDR = f"{MOODLE_SERVER_WEB_HOST}:{MOODLE_SERVER_WEB_PORT}" # base adress of moodle website

MOODLE_SERVER_DB_ADDR = "db"  # IP address of moodle database (e.g. same as web server IP if running on the same server)
MOODLE_SERVER_DB_PORT = os.environ['MOODLE_DOCKER_DB_PORT']  # Port of moodle database (default for mysql: 3306)
MOODLE_SERVER_DB_TALBE_PREFIX = "mdl_" # Prefix in Moodle Database Tables (e.g. m_, mdl_, ...)
MOODLE_SERVER_DB_NAME = os.environ["MOODLE_DOCKER_DBNAME"]
MOODLE_SERVER_DB_USER = os.environ["MOODLE_DOCKER_DBUSER"]
MOODLE_SERVER_DB_PWD = os.environ["MOODLE_DOCKER_DBPASS"]

DS_SERVER_IP_ADDR = "127.0.0.1"    # IP address of dialog system

def MOODLE_SERVER_ADDR():
    return MOODLE_SERVER_WEB_HOST