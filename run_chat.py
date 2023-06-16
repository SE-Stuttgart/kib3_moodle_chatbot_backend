###############################################################################
#
# Copyright 2020, University of Stuttgart: Institute for Natural Language Processing (IMS)
#
# This file is part of Adviser.
# Adviser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3.
#
# Adviser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Adviser.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################

"""
This module allows to chat with the dialog system.
"""

import argparse
import os

from services.domain_tracker.domain_tracker import DomainTracker
from services.service import DialogSystem
from utils.logger import DiasysLogger, LogLevel

def load_console():
    from services.hci.console import ConsoleInput, ConsoleOutput
    user_in = ConsoleInput(domain="")
    user_out = ConsoleOutput(domain="")
    return [user_in, user_out]

def load_nlg(domain=None):
    from services.nlg.nlg import ELearningNLG
    nlg = ELearningNLG(domain=domain)
    return nlg

def load_elearning_domain():
    from utils.domain.jsonlookupdomain import JSONLookupDomain
    from elearning.policy_ELearning import ELearningPolicy
    from elearning.eLearningBst import ELearningBST
    from services.nlu.nluOld import ELearningNLU
    domain = JSONLookupDomain('ELearning', display_name="ELearning")
    e_learning_nlu = ELearningNLU(domain=domain)
    e_learning_policy = ELearningPolicy(domain=domain)
    e_learning_bst = ELearningBST(domain=domain)
    e_learning_nlg = load_nlg(domain=domain)
    return domain, [e_learning_nlu, e_learning_bst, e_learning_policy, e_learning_nlg]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ADVISER 2.0 Dialog System')
    parser.add_argument('domains', nargs='+', choices=['lecturers', 'weather', 'mensa', 'qa', 'e_learning'],
                        help="Chat domain(s). For multidomain type as list: domain1 domain2 .. \n",
                        default="ImsLecturers")
    parser.add_argument('--debug', action='store_true',
                        help="enable debug mode")
    parser.add_argument('--log_file', choices=['dialogs', 'results', 'info', 'errors', 'none'], default="none",
                        help="specify file log level")
    parser.add_argument('--log', choices=['dialogs', 'results', 'info', 'errors', 'none'], default="results",
                        help="specify console log level")
    
    args = parser.parse_args()

    num_dialogs = 1
    domains = []
    services = []

    # setup logger
    file_log_lvl = LogLevel[args.log_file.upper()]
    log_lvl = LogLevel[args.log.upper()]
    conversation_log_dir = './conversation_logs'
    speech_log_dir = None
    if file_log_lvl == LogLevel.DIALOGS:
        # log user audio, system audio and complete conversation
        import time
        from math import floor

        print("This Adviser call will log all your interactions to files.\n")
        if not os.path.exists(f"./{conversation_log_dir}"):
            os.mkdir(f"./{conversation_log_dir}/")
        conversation_log_dir = "./" + conversation_log_dir + \
            "/{}/".format(floor(time.time()))
        os.mkdir(conversation_log_dir)
        speech_log_dir = conversation_log_dir
    logger = DiasysLogger(file_log_lvl=file_log_lvl,
                          console_log_lvl=log_lvl,
                          logfile_folder=conversation_log_dir,
                          logfile_basename="full_log")

    # load domain specific services
    if 'e_learning' in args.domains:
        e_learning_domain, e_learning_services = load_elearning_domain()
        domains.append(e_learning_domain)
        services.extend(e_learning_services)

    services.extend(load_console())

    # setup dialog system
    services.append(DomainTracker(domains=domains))
    debug_logger = logger if args.debug else None
    ds = DialogSystem(services=services, debug_logger=debug_logger)
    error_free = ds.is_error_free_messaging_pipeline()
    if not error_free:
        ds.print_inconsistencies()
    if args.debug:
        ds.draw_system_graph()

    # run dialog(s)
    for _ in range(num_dialogs):
        ds.run_dialog({'gen_user_utterance': "", "sys_state/ELearning": {}})
    # free resources
    ds.shutdown()
