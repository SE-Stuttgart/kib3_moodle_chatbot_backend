# adviser_kib3

This repository contains the code for the chatbot server backend.

## Installation

1. Clone code
2. Create a virtual environment and install the requirements into it: `pip install -r requirements_server.txt`
3. Open the file `config.py` in the main folder. 
  1. Change the IP addresses and ports to match your Moodle webserver and database server configurations.
     E.g., if everything is running on the same machine, the IP addresses should all be the host address of that machine.
     For testing on your local machine, you could set all of these to `127.0.0.1`.
     The default web server port should be `8080` if not changed during the Moodle configuration process.
     The default database port is set to `3306`, which only applies to MySQL - so change that if you selected a different database during the Moodle installation.
 
 ## Running the Server
 1. Activate your virtual environment
 2. Run `python run_server.py` to start the chatbot backend. This should log to the console. You may adapt the logging levels as required.
