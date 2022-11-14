

MOODLE_SERVER_IP_ADDR = "193.196.53.252"    # IP address of moodle server
MOODLE_SERVER_PORT = "3000"     # Port of moodle webserver (default: 8080, or set to None)
MOODLE_SERVER_DB_ADDR = "193.196.53.252"  # IP address of moodle database (e.g. same as web server IP if running on the same server)
MOODLE_SERVER_DB_PORT = "3306"  # Port of moodle database (default for mysql: 3306)

DS_SERVER_IP_ADDR = "193.196.53.252"    # IP address of dialog system

def MOODLE_SERVER_ADDR():
    if MOODLE_SERVER_PORT:
        return f"{MOODLE_SERVER_IP_ADDR}:{MOODLE_SERVER_PORT}"
    return MOODLE_SERVER_IP_ADDR