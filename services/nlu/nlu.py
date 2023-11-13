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

import json
import os
import re
import time
from typing import List
from utils.utterance_mapper import Utterance_Mapper
from services.service import PublishSubscribe
from services.service import Service
from utils import UserAct, UserActionType
from utils.beliefstate import BeliefState
from utils.common import Language
from utils.domain.jsonlookupdomain import JSONLookupDomain
from utils.logger import DiasysLogger
from utils.sysact import SysAct, SysActionType

class ELearningNLU(Service):
    """
    Class for Handcrafted Natural Language Understanding Module (HDC-NLU).

    It is responsible for detecting user acts with their respective slot-values from the user
    utterance through cosine similarity.

   

    """
    # Variables for the state (can be used to get info from previous turns)
    DIALOG_STARTED = 'dialog_started'
    LAST_ACT = "last_act"
    LAST_OFFER = 'last_offer'
    LAST_REQUESTED_SLOT = 'last_requested_slot'
    SLOTS_REQUESTED = 'slots_requested'
    SLOTS_INFORMED = 'slots_informed'
    SEARCH_COUNTER = 'search_counter'


    def __init__(self, domain: JSONLookupDomain, logger: DiasysLogger = DiasysLogger(),
                 language: Language = Language.GERMAN):
        """
        Loads
            - domain key
            - informable slots
            - requestable slots
            - domain-independent regular expressions
            - domain-specific regualer espressions

        It sets the previous system act to None

        Args:
            domain {domain.jsonlookupdomain.JSONLookupDomain} -- Domain
        """
        Service.__init__(self, domain=domain)
        self.logger = logger

        self.language = language if language else Language.ENGLISH

        # Getting domain information
        self.domain_name = domain.get_domain_name()
        self.domain_key = domain.get_primary_key()


        self.uttance_mapper = Utterance_Mapper('PM-AI/bi-encoder_msmarco_bert-base_german') # domain hinzugüfen
        
        # Getting lists of informable and requestable slots
        # In utterance_mapper.py the same for now
        self.USER_INFORMABLE = self.uttance_mapper.get_informable_slots()
        self.USER_REQUESTABLE = self.uttance_mapper.get_requestable_slots()

        self.language = language
        

    def dialog_start(self, user_id: str):
        started = self.get_state(user_id, self.DIALOG_STARTED) # check if user started new dialog or continues existing one
        if not started:
            self.set_state(user_id, self.DIALOG_STARTED, True)
            self.set_state(user_id, self.LAST_ACT, None)
            self.set_state(user_id, self.LAST_OFFER, None)
            self.set_state(user_id, self.SEARCH_COUNTER, 0)
            self.set_state(user_id, self.LAST_REQUESTED_SLOT, None)
            self.set_state(user_id, self.SLOTS_REQUESTED, set())
            self.set_state(user_id, self.SLOTS_INFORMED, set())


    @PublishSubscribe(sub_topics=["moodle_event"])
    def moodle_event(self, user_id: int, moodle_event: dict):
        if moodle_event['eventname'].lower().strip() == "\\core\\event\\user_loggedin":
            self.clear_memory(user_id)

    @PublishSubscribe(sub_topics=["user_utterance"], pub_topics=["user_acts"])
    def extract_user_acts(self, user_id: str, user_utterance: str = None) -> dict(user_acts=List[UserAct]):
        print("extract_user_acts")

        """
        Responsible for detecting user acts with their respective slot-values from the user
        utterance through regular expressions.

        Args:
            user_utterance (BeliefState) - a BeliefState obejct representing current system
                                           knowledge

        Returns:
            dict of str: UserAct - a dictionary with the key "user_acts" and the value
                                            containing a list of user actions
        """
        start = time.time()
        result = {}
        #print(self.uttance_mapper.get_labels())
        if user_utterance is not None:
            user_utterance = user_utterance.strip()
            user_act = self.uttance_mapper.get_most_similar_label("\"" +user_utterance + "\"")
            
            # user_requestable selber erstellen und abfragen
            last_act = self.get_state(user_id, self.LAST_ACT)

            if last_act and "modulContent" in last_act.slot_values and last_act.type == SysActionType.Request:
                # if last was search but search term was not found -> last sysact asked for search term -> now user gives search term
                user_act = UserAct(text=user_utterance, act_type=UserActionType.Inform, slot="SearchTerm")
                self.set_state(user_id, self.SEARCH_COUNTER, 3)
                
            elif user_act == "Bye":

                user_act = UserAct(text=user_utterance, act_type=UserActionType.Bye)
            elif user_act == "Thanks":
                user_act = UserAct(text=user_utterance, act_type=UserActionType.Thanks)
            elif user_act == "LoadMoreSearchResults" or user_act == "Yes":
                # if last act was SearchForDefinition or SearchForContent then get more results
                
                if 'modulContent' in last_act.slot_values and last_act.type == SysActionType.Inform:
                
                #if last_act and (last_act == "SearchForDefinition" or last_act == "SearchForContent"):
                    # increase search counter
                    search_counter = self.get_state(user_id, self.SEARCH_COUNTER)
                    user_act = UserAct(text=user_utterance, act_type=UserActionType.Inform, slot="LoadMoreSearchResults: " + str(search_counter))
                    
                    search_counter += 3
                    self.set_state(user_id, self.SEARCH_COUNTER, search_counter)
                else:
                    user_act = UserAct(text=user_utterance, act_type=UserActionType.Inform,
                           slot=user_act)
                    self._add_inform(user_id, user_act.slot)
            elif user_act == "SearchForDefinition" or user_act == "SearchForContent":
                # set search counter to 3
                self.set_state(user_id, self.SEARCH_COUNTER, 3)
                user_act = UserAct(text=user_utterance, act_type=UserActionType.Inform, slot=user_act)
            
            # im moment alle requestable slots
            elif user_act in self.USER_REQUESTABLE:
                user_act = UserAct(text=user_utterance, act_type=UserActionType.Request,
                           slot=user_act)
                self._add_request(user_id, user_act.slot)
 
            elif user_act in self.USER_INFORMABLE:
                user_act = UserAct(text=user_utterance, act_type=UserActionType.Inform,
                           slot=user_act)
                self._add_inform(user_id, user_act.slot)
            else:
                user_act = UserAct(text=user_utterance, act_type=UserActionType.Bad)
            result["user_acts"] = [user_act]
            end = time.time()
            print("extract_user_acts took: ", end-start)
        return result

    @PublishSubscribe(sub_topics=["sys_state"])
    def _update_sys_act_info(self, user_id: str, sys_state):
        if "lastInformedPrimKeyVal" in sys_state:
            self.set_state(user_id, self.LAST_OFFER, sys_state['lastInformedPrimKeyVal'])
        if "lastRequestSlot" in sys_state:
            self.set_state(user_id, self.LAST_REQUESTED_SLOT, sys_state['lastRequestSlot'])
        if "last_act" in sys_state:
            self.set_state(user_id, self.LAST_ACT, sys_state['last_act'])

       
    def _add_request(self, user_id, slot: str):
        """
        Creates the user request act and adds it to the user act list
        Args:
            slot {str} -- requested slot

        Returns:

        """
        # Storing user requested slots during the whole dialog
        slots_requested = self.get_state(user_id, self.SLOTS_REQUESTED)
        slots_requested.add(slot)
        self.set_state(user_id, self.SLOTS_REQUESTED, slots_requested)

       
    def _add_inform(self, user_id: str, slot: str):
        """
        Creates the user request act and adds it to the user act list

        Args:
            slot {str} -- informed slot

        Returns:

        """
        # Storing user informed slots in this turn
        slots_informed = self.get_state(user_id, self.SLOTS_INFORMED)
        slots_informed.add(slot)
        self.set_state(user_id, self.SLOTS_INFORMED, slots_informed)

