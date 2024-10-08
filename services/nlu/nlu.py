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

import re
import time
from typing import List
from utils.utterance_mapper import Utterance_Mapper
from services.service import PublishSubscribe
from services.service import Service
from utils import UserAct, UserActionType
from utils.common import Language
from utils.domain.jsonlookupdomain import JSONLookupDomain
from utils.sysact import SysActionType

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


    def __init__(self, domain: JSONLookupDomain, 
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

        self.language = language if language else Language.ENGLISH
       
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
        if user_utterance is not None and len(user_utterance) > 0:
            user_utterance = user_utterance.strip()
            user_act = self.uttance_mapper.get_most_similar_label("\"" +user_utterance + "\"")
            user_act_type = UserActionType(user_act)        
            user_act = UserAct(text=user_utterance, act_type=user_act_type)

            last_acts = self.get_state(user_id, self.LAST_ACT)
            if len(last_acts) > 0 and last_acts[0].type == SysActionType.RequestSearchTerm:
                # check if system requested a new search term
                user_act.type = UserActionType.Search
                user_act.value = user_utterance
            else:
                if user_act_type in [UserActionType.Search, UserActionType.LoadMoreSearchResults]:
                    # if we have a search trigger, try to extract the search term(s) using rules
                    #reg = (
                    #    r"(Wo\s*(kann ich|finde ich|steht|ist)|Zeig mir|Welche|Ich *(suche|brauche|will))?\s*(mehr\s*)?(Material(ien)?|nach|Inhalte|erfahren, wie man|spezifische Anwendungen|Beispiele|Ressourcen|(die )?Grundlagen|Tutorials|eine Einführung|eine einfache Erklärung für den Begriff|Übungen|Bücher(?: oder Artikel)?|Artikel|Info(s?( zum Thema)?|rmation(en|squellen)?)|Videos|(Lern)?material(ien)?|was)\s*(in|von|zu|für|über|eine|, die)?\s*(?P<content>.*?)\s*(finden|durchführt|lernen|erfahren|erklären)?(\?|$)|(Kannst|Könntest) du mir (?P<content1>.*?)? (erlären(,)?|eine\s*(kurze|einfache|präzise))?\s*(Erklärung|Definition)?\s*(was( der Begriff| mit)?|von|für( den Begriff)?)?\s*(?P<content2>.*?)\s*(bedeutet|geben|gemeint ist)?(\?|$)|Was (ist|sind|bezeichnet man als)\s*(der|die|das)?\s*(Ziel|Bedeutung|mit|Definition|grundlegenden Konzepte hinter)?\s*(der|von|als)?\s*(?P<content3>.*?)\s*(gemeint)?(\?|$)"
                    #)
                    reg = (
                        r"(Wo\s*(kann ich|finde ich|steht)|Zeig mir|Welche|Ich\s*(suche|brauche|will))\s*"
                        r"((Inhalte|erfahren, wie man|spezifische Anwendungen|Beispiele|Ressourcen|mehr|(die )?Grundlagen|Tutorials|"
                        r"eine Einführung|eine einfache Erklärung für den Begriff|Übungen|Bücher(?: oder Artikel)?|Artikel|"
                        r"Info(s( zum Thema)?|rmation(en|squellen))|Videos|Lernmaterialien|was)?\s*)?"
                        r"(in|von|zu|für|über|eine|, die)?\s*(?P<content>.*?)\s*"
                        r"(finden|durchführt|lernen|erfahren|erklären)?(\?|$)|"
                        r"(Kannst|Könntest) du mir (?P<content1>.*?)? (erlären(,)?|eine\s*(kurze|einfache|präzise))?\s*"
                        r"(Erklärung|Definition)?\s*(was( der Begriff| mit)?|von|für( den Begriff)?)?\s*(?P<content2>.*?)\s*"
                        r"(bedeutet|geben|gemeint ist)?(\?|$)|"
                        r"Was (ist|sind|bezeichnet man als)\s*(der|die|das)?\s*"
                        r"(Ziel|Bedeutung|mit|Definition|grundlegenden Konzepte hinter)?\s*(der|von|als)?\s*"
                        r"(?P<content3>.*?)\s*(gemeint)?(\?|$)|"
                        r"(definiere|Definition von)\s*(?P<content4>.*?)\s*(\?|$)"
                    )
                    matches = re.match(reg, user_act.text, re.I)
                    if matches:
                        matches = matches.groupdict()
                        for key in matches.keys():
                            if key.startswith("content") and matches.get(key):
                                user_act.value = matches.get(key)
        
            result["user_acts"] = [user_act]
            end = time.time()
            print("extract_user_acts took: ", end-start)
        else:
            result = {"user_acts": []}
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

