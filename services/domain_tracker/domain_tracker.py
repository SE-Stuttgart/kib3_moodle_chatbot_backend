###############################################################################
#
# Copyright 2019, University of Stuttgart: Institute for Natural Language Processing (IMS)
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

"""The console module provides ADVISER services for tracking current domain"""

from services.service import PublishSubscribe
from services.service import Service
from utils.domain import Domain
from typing import List


class DomainTracker(Service):
    """Gets the user utterance from the console.

    Waits for the built-in input function to return a non-empty text.
    """

    TURN = 'turn'
    CURRENT_DOMAIN = 'current_domain'

    def __init__(self, domains: List[Domain], greet_on_first_turn: bool = False):
        Service.__init__(self, domain="")
        self.domains = domains
        self.domain_names = [domain.get_domain_name() for domain in domains]
        self.greet_on_first_turn = greet_on_first_turn

    def dialog_start(self, user_id: str):
        self.set_state(user_id, DomainTracker.TURN, 0)
        self.set_state(user_id, DomainTracker.CURRENT_DOMAIN, None)

    @PublishSubscribe(sub_topics=["gen_user_utterance"], pub_topics=["user_utterance", "sys_utterance"])
    def select_domain(self, user_id: str = "default", gen_user_utterance: str = None) -> dict(user_utterance=str):
        """
        """

        current_domain = self.get_state(user_id, DomainTracker.CURRENT_DOMAIN)
        turn = self.get_state(user_id, DomainTracker.TURN)
        turn += 1
        self.set_state(user_id, DomainTracker.TURN, turn)

        # if there is only a single domain, simply route the message forward
        if len(self.domains) == 1:
            current_domain = self.domain_names[0]
            self.set_state(user_id, DomainTracker.CURRENT_DOMAIN, current_domain)

        if turn == 1 and self.greet_on_first_turn and len(self.domains) == 1:
            return {f'user_utterance/{current_domain}': ''}


        # make sure the utterance is lowercase if there is one
        user_utterance = gen_user_utterance
        if user_utterance:
            user_utterance = gen_user_utterance.lower()

        # perform keyword matching to see if any domains are explicitely made active
        active_domains = [d for d in self.domains if d.get_keyword() in user_utterance]

        # Even if no domain has been specified, we should be able to exit
        if "bye" in user_utterance and not current_domain:
            return {"sys_utterance": "Thank you, goodbye."}

        # if there are active domains, use the first one
        elif active_domains:
            out_key = f"user_utterance/{active_domains[0].get_domain_name()}"
            current_domain = active_domains[0].get_domain_name()
            self.set_state(user_id, DomainTracker.CURRENT_DOMAIN, current_domain)
            return {out_key: user_utterance}

        # if no domain is explicitely mentioned, assume the last one is still active
        elif current_domain:
            out_key = f"user_utterance/{current_domain}"
            return {out_key: user_utterance}

        # Otherwise ask the user what domain they want
        else:
            return {"sys_utterance": "Hello, please let me know how I can help you, I can discuss " +
                    f"the following domains: {self.domains_to_str()}."}

    def domains_to_str(self):
        if len(self.domains) == 1:
            return self.domains[0].get_display_name()
        elif len(self.domains) == 2:
            return " and ".join([d.get_display_name() for d in self.domains])
        else:
            return ", ".join([d.get_display_name() for d in self.domains][:-1]) + f", and {self.domains[-1].get_display_name()}"
