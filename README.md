# KIB3 Moodle Assistant Backend

This repository contains the code for the Moodle Assistang Server backend.

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
`MOOLDE_SERVER_PROTOCOL = "https"`, **if your Moodle instance uses SSL**. Otherwise leave at default.
3.  Replace the value `webserver` in line `MOODLE_SERVER_WEB_HOST = 'webserver'` with the IP address or URL (and port, if not on default `80` port) of your Moodle server, e.g. `"yourmoodle.com"` or `"127.0.0.1:8081".`
4. Make sure to open the port specified in the variable `DS_SERVER_PORT` (default: `44123`, adapt if already in use). This port should be enabled for tcp and websocket communication.
5. If you use SSL, change the value for `SSL_CERT_FILE` to the path pointing to your SSL certificate (`*.crt` file). Also change the value of `SSL_PRIVATE_KEY_FILE` to point to your SSL private key file.

## Running the Server
1. Activate your virtual environment, e.g.
`source .env/bin/activate`
2. Execute `python run_server.py` to start the chatbot backend. For keeping the server alive after ending the terminal session, you might use e.g. `nohup` /  `screen` / etc. or create a system service.
