# KIB3 Moodle Chatbot Backend

This repository contains the code for the chatbot server backend.

## Installation
1. Clone the code (or download): `git clone https://github.com/SE-Stuttgart/kib3_moodle_chatbot_backend.git`
2. Create a virtual environment, e.g.
`python -m venv .env`
3. Activate the environment, e.g.
`source .env/bin/activate`
4. Install the python requirements into the virtual environment: `pip install -r requirements_server.txt`

## Configuration
1. Open the file `config.py` in the main folder.
2. Change the line starting with `MOOLDE_SERVER_PROTOCOL` to 
`MOOLDE_SERVER_PROTOCOL = "https"`, if your Moodle instance uses SSL.
3.  Replace the value `webserver` in line `MOODLE_SERVER_WEB_HOST = 'webserver'` with the IP address (and port, if not on default `80` port) of your Moodle server, e.g. `"127.0.0.1"` or `"127.0.0.1:8081"`
 ## Running the Server
 1. Activate your virtual environment, e.g.
`source .env/bin/activate`
 2. Execute `python run_server.py` to start the chatbot backend. For keeping the server alive after ending the terminal session, you might use e.g. `nohup` /  `screen` / etc. or create a system service.
