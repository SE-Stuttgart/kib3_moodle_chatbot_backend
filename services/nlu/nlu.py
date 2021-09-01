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

import json
import os
import re
from typing import List

from services.service import PublishSubscribe
from services.service import Service
from utils import UserAct, UserActionType
from utils.common import Language
from utils.domain.jsonlookupdomain import JSONLookupDomain
from utils.logger import DiasysLogger
from utils.sysact import SysActionType, SysAct
from utils.sysstate import SysState


def get_root_dir():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class HandcraftedNLU(Service):
    """
    Class for Handcrafted Natural Language Understanding Module (HDC-NLU).

    HDC-NLU is a rule-based approach to recognize the user acts as well as
    their respective slots and values from the user input (i.e. text)
    by means of regular expressions.

    HDC-NLU is domain-independet. The regular expressions of are read
    from JSON files.

    There exist a JSON file that stores general rules (GeneralRules.json),
    i.e. rules that apply to any domain, e.g. rules to detect salutation (Hello, Hi).

    There are two more files per domain that contain the domain-specific rules
    for request and inform user acts, e.g. ImsCoursesInformRules.json and
    ImsCoursesRequestRules.json.

    The output during dialog interaction of this module is a semantic
    representation of the user input.

    "I am looking for pizza" --> inform(slot=food,value=italian)

    See the regex_generator under tools, if the existing regular expressions
    need to be changed or a new domain should be added.


    """

    SYS_ACT_INFO = "sys_act_info"

    def __init__(self, domain: JSONLookupDomain, logger: DiasysLogger = DiasysLogger()):
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

        # Getting domain information
        self.domain_name = domain.get_domain_name()
        self.domain_key = domain.get_primary_key()

        # Getting lists of informable and requestable slots
        self.USER_INFORMABLE = domain.get_informable_slots()
        self.USER_REQUESTABLE = domain.get_requestable_slots()

        # Getting the relative path where regexes are stored
        self.base_folder = os.path.join(get_root_dir(), 'resources', 'nlu_regexes')

        self.language = Language.ENGLISH
        self._initialize()

    @PublishSubscribe(sub_topics=["user_utterance"], pub_topics=["user_acts"])
    def extract_user_acts(self, user_id: str = "default", user_utterance: str = None) \
            -> dict(user_acts=List[UserAct]):

        """
        Responsible for detecting user acts with their respective slot-values from the user
        utterance through regular expressions.

        Args:
            user_utterance 
            sys_act (list) - a list of UserAct objects mapped from the user's last utterance

        Returns:
            dict of str: UserAct - a dictionary with the key "user_acts" and the value
                                            containing a list of user actions
        """
        sys_act_info = self.get_state(user_id, HandcraftedNLU.SYS_ACT_INFO)        
        # Setting request everything to False at every turn
        req_everything = False
        user_acts = []

        # slots_requested & slots_informed store slots requested and informed in this turn
        # they are used later for later disambiguation
        slots_requested, slots_informed = set(), set()
        if user_utterance is not None:
            user_utterance = user_utterance.strip()
            req_everything = self._match_general_act(user_utterance, user_acts, sys_act_info, slots_informed, req_everything)
            self._match_domain_specific_act(user_utterance, user_acts, slots_informed, req_everything, slots_requested)
            user_acts.extend(self._match_hard_coded_regexes(user_utterance))

        # Solving ambiguities from regexes, especially with requests and informs happening
        # simultaneously on the same slot and two slots taking the same value
        # NOTE: function is unused (beliefstate was always set to None)
        # self._disambiguate_co_occurrence(beliefstate, user_acts, slots_requested, slots_informed, sys_act_info)
        self._solve_informable_values(user_acts)

        # If nothing else has been matched, see if the user chose a domain; otherwise if it's
        # not the first turn, it's a bad act
        if len(user_acts) == 0:
            if self.domain.get_keyword() in user_utterance:
                user_acts.append(UserAct(text=user_utterance if user_utterance else "",
                                              act_type=UserActionType.SelectDomain))
            elif sys_act_info.last_act is not None:
                # start of dialogue or no regex matched
                user_acts.append(UserAct(text=user_utterance if user_utterance else "",
                                              act_type=UserActionType.Bad))
        self._assign_scores(user_acts)
        self.logger.dialog_turn(f"# USER {user_id} # NLU-ACTS ({self.domain.get_domain_name()}) - {user_acts}")

        return {'user_acts': user_acts}

    @PublishSubscribe(sub_topics=["sys_state"])
    def _update_sys_act_info(self, user_id: str, sys_state: SysState):
        self.set_state(user_id, HandcraftedNLU.SYS_ACT_INFO, sys_state)


    def _match_general_act(self, user_utterance: str, user_acts, sys_act_info, slots_informed, req_everything):
        """
        Finds general acts (e.g. Hello, Bye) in the user input

        Args:
            user_utterance {str} --  text input from user

        Returns:

        """

        # Iteration over all general acts
        for act in self.general_regex:
            # Check if the regular expression and the user utterance match
            if re.search(self.general_regex[act], user_utterance, re.I):
                # Mapping the act to User Act
                if act != 'dontcare' and act != 'req_everything':
                    user_act_type = UserActionType(act)
                else:
                    user_act_type = act
                # Check if the found user act is affirm or deny
                if sys_act_info.last_act and (user_act_type == UserActionType.Affirm or
                                                      user_act_type == UserActionType.Deny):
                    # Conditions to check the history in order to assign affirm or deny
                    # slots mentioned in the previous system act

                    # Check if the preceeding system act was confirm
                    if sys_act_info.last_act.type == SysActionType.Confirm:
                        # Iterate over all slots in the system confimation
                        # and make a list of Affirm/Deny(slot=value)
                        # where value is taken from the previous sys act
                        for slot in sys_act_info.last_act.slot_values:
                            # New user act -- Affirm/Deny(slot=value)
                            user_act = UserAct(act_type=UserActionType(act),
                                               text=user_utterance,
                                               slot=slot,
                                               value=sys_act_info.last_act.slot_values[slot])
                            user_acts.append(user_act)

                    # Check if the preceeding system act was request
                    # This covers the binary requests, e.g. 'Is the course related to Math?'
                    elif sys_act_info.last_act.type == SysActionType.Request:
                        # Iterate over all slots in the system request
                        # and make a list of Inform(slot={True|False})
                        for slot in sys_act_info.last_act.slot_values:
                            # Assign value for the slot mapping from Affirm or Request to Logical,
                            # True if user affirms, False if user denies
                            value = 'true' if user_act_type == UserActionType.Affirm else 'false'
                            # Adding user inform act
                            self._add_inform(user_utterance, slot, value, user_acts, slots_informed)

                    # Check if Deny happens after System Request more, then trigger bye
                    elif sys_act_info.last_act.type == SysActionType.RequestMore \
                            and user_act_type == UserActionType.Deny:
                        user_act = UserAct(text=user_utterance, act_type=UserActionType.Bye)
                        user_acts.append(user_act)

                # Check if Request or Select is the previous system act
                elif user_act_type == 'dontcare':
                    if sys_act_info.last_act.type == SysActionType.Request or \
                            sys_act_info.last_act.type == SysActionType.Select:
                        # Iteration over all slots mentioned in the last system act
                        for slot in sys_act_info.last_act.slot_values:
                            # Adding user inform act
                            self._add_inform(user_utterance, slot, user_act_type, user_acts, slots_informed)

                # Check if the user wants to get all information about a particular entity
                elif user_act_type == 'req_everything':
                    req_everything = True

                else:
                    # This section covers all general user acts that do not depend on
                    # the dialog history
                    # New user act -- UserAct()
                    user_act = UserAct(act_type=user_act_type, text=user_utterance)
                    user_acts.append(user_act)
        
        return req_everything

    def _match_domain_specific_act(self, user_utterance: str, user_acts, slots_informed, req_everything, slots_requested):
        """
        Matches in-domain user acts
        Calls functions to find user requests and informs

        Args:
            user_utterance {str} --  text input from user

        Returns:

        """
        # Find Requests
        self._match_request(user_utterance, user_acts, slots_requested)
        # Find Informs
        self._match_inform(user_utterance, user_acts, slots_informed, req_everything, slots_requested)

    def _match_request(self, user_utterance: str, user_acts, slots_requested):
        """
        Iterates over all user request regexes and find matches with the user utterance

        Args:
            user_utterance {str} --  text input from user

        Returns:

        """
        # Iteration over all user requestable slots
        for slot in self.USER_REQUESTABLE:
            if self._check(re.search(self.request_regex[slot], user_utterance, re.I)):
                self._add_request(user_utterance, slot, user_acts, slots_requested)

    def _add_request(self, user_utterance: str, slot: str, user_acts, slots_requested):
        """
        Creates the user request act and adds it to the user act list
        Args:
            user_utterance {str} --  text input from user
            slot {str} -- requested slot

        Returns:

        """
        # New user act -- Request(slot)
        user_act = UserAct(text=user_utterance, act_type=UserActionType.Request, slot=slot)
        user_acts.append(user_act)
        # Storing user requested slots during the whole dialog
        slots_requested.add(slot)

    def _match_inform(self, user_utterance: str, user_acts, slots_informed, req_everything, slots_requested):
        """
        Iterates over all user inform slot-value regexes and find matches with the user utterance

        Args:
            user_utterance {str} --  text input from user

        Returns:

        """

        # Iteration over all user informable slots and their slots
        for slot in self.USER_INFORMABLE:
            for value in self.inform_regex[slot]:
                if self._check(re.search(self.inform_regex[slot][value], user_utterance, re.I)):
                    if slot == self.domain_key and req_everything:
                        # Adding all requestable slots because of the req_everything
                        for req_slot in self.USER_REQUESTABLE:
                            # skipping the domain key slot
                            if req_slot != self.domain_key:
                                # Adding user request act
                                self._add_request(user_utterance, req_slot, user_acts, slots_requested)
                    # Adding user inform act
                    self._add_inform(user_utterance, slot, value, user_acts, slots_informed)

    def _add_inform(self, user_utterance: str, slot: str, value: str, user_acts, slots_informed):
        """
        Creates the user request act and adds it to the user act list

        Args:
            user_utterance {str} --  text input from user
            slot {str} -- informed slot
            value {str} -- value for the informed slot

        Returns:

        """
        user_act = UserAct(text=user_utterance, act_type=UserActionType.Inform,
                           slot=slot, value=value)
        user_acts.append(user_act)
        # Storing user informed slots in this turn
        slots_informed.add(slot)

    @staticmethod
    def _exact_match(phrases: List[str], user_utterance: str) -> bool:
        """
        Checks if the user utterance is exactly like one in the

        Args:
            phrases List[str] --  list of contextual don't cares
            user_utterance {str} --  text input from user

        Returns:

        """

        # apostrophes are removed
        if user_utterance.lstrip().lower().replace("'", "") in phrases:
            return True
        return False

    def _match_affirm(self, user_utterance: str):
        """TO BE DEFINED AT A LATER POINT"""
        pass

    def _match_negative_inform(self, user_utterance: str):
        """TO BE DEFINED AT A LATER POINT"""
        pass

    @staticmethod
    def _check(re_object) -> bool:
        """
        Checks if the regular expression and the user utterance matched

        Args:
            re_object: output from re.search(...)

        Returns:
            True/False if match happened

        """

        if re_object is None:
            return False
        for o in re_object.groups():
            if o is not None:
                return True
        return False

    def _assign_scores(self, user_acts):
        """
        Goes over the user act list, checks concurrencies and assign scores

        Returns:

        """

        for i in range(len(user_acts)):
            # TODO: Create a clever and meaningful mechanism to assign scores
            # Since the user acts are matched, they get 1.0 as score
            user_acts[i].score = 1.0

    def dialog_start(self, user_id: str) -> dict:
        """
        Sets the previous system act as None.
        This function is called when the dialog starts

        Returns:
            Empty dictionary

        """
        self.set_state(user_id, HandcraftedNLU.SYS_ACT_INFO, SysState())

    # def _disambiguate_co_occurrence(self, beliefstate: BeliefState, user_acts, slots_requested, slots_informed, sys_act_info):
    #     # Check if there is user inform and request occur simultaneously for a binary slot
    #     # E.g. request(applied_nlp) & inform(applied_nlp=true)
    #     # Difficult to disambiguate using regexes
    #     if slots_requested.intersection(slots_informed):
    #         if beliefstate is None:
    #             act_to_del = UserActionType.Request
    #         elif sys_act_info['lastInformedPrimKeyVal'] in [None, '**NONE**', 'none']:
    #             act_to_del = UserActionType.Request
    #         else:
    #             act_to_del = UserActionType.Inform

    #         acts_to_del = []
    #         for slot in slots_requested.intersection(slots_informed):
    #             for i, user_act in enumerate(user_acts):
    #                 if user_act.type == act_to_del and user_act.slot == slot:
    #                     acts_to_del.append(i)

    #         user_acts = [user_act for i, user_act in enumerate(user_acts)
    #                           if i not in acts_to_del]

    def _solve_informable_values(self, user_acts):
        # Verify if two or more informable slots with the same value were caught
        # Cases:
        # If a system request precedes and the slot is the on of the two informable, keep that one.
        # If there is no preceding request, take
        informed_values = {}
        for i, user_act in enumerate(user_acts):
            if user_act.type == UserActionType.Inform:
                if user_act.value != "true" and user_act.value != "false":
                    if user_act.value not in informed_values:
                        informed_values[user_act.value] = [(i, user_act.slot)]
                    else:
                        informed_values[user_act.value].append((i, user_act.slot))

        informed_values = {value: informed_values[value] for value in informed_values if
                           len(informed_values[value]) > 1}
        if "6" in informed_values:
            user_acts = []

        # # Check if there is at least one informed value that matches more than one slot
        # if len(informed_values)>0:
        #     if beliefstate['system']['lastRequestSlot'] is not None:
        #         for value in informed_values:
        #             req_slots = [i for i, slot in informed_values[value]
        #                          if beliefstate['system']['lastRequestSlot']==slot]
        #             if len(req_slots)==1:
        #                 for i, slot in informed_values[value]:
        #                     if beliefstate['system']['lastRequestSlot']!=slot:
        #                         del user_acts[i]
        #             # elif len(req_slots)==0:
        #             #     # it keeps the first slot matched
        #             #     # This is not the most clever solution
        #             #     for i, slot in informed_values[value][1:]:
        #             #             del user_acts[i]
        #     else:
        #         # If no system requested slot, then a Bad act is forced
        #         user_acts = []

    def _initialize(self):
        """
            Loads the correct regex files based on which language has been selected
            this should only be called on the first turn of the dialog

            Args:
                language (Language): Enum representing the language the user has selected
        """
        if self.language == Language.ENGLISH:
            # Loading regular expression from JSON files
            # as dictionaries {act:regex, ...} or {slot:{value:regex, ...}, ...}
            self.general_regex = json.load(open(self.base_folder + '/GeneralRules.json'))
            self.request_regex = json.load(open(self.base_folder + '/' + self.domain_name
                                                + 'RequestRules.json'))
            self.inform_regex = json.load(open(self.base_folder + '/' + self.domain_name
                                               + 'InformRules.json'))
        elif self.language == Language.GERMAN:
            # TODO: Change this once
            # Loading regular expression from JSON files
            # as dictionaries {act:regex, ...} or {slot:{value:regex, ...}, ...}
            self.general_regex = json.load(open(self.base_folder + '/GeneralRulesGerman.json'))
            self.request_regex = json.load(open(self.base_folder + '/' + self.domain_name
                                                + 'GermanRequestRules.json'))
            self.inform_regex = json.load(open(self.base_folder + '/' + self.domain_name
                                               + 'GermanInformRules.json'))
        else:
            print('No language')

    def _match_hard_coded_regexes(self, user_utterance: str):

        user_acts = []
        if self.language == Language.ENGLISH:
            domains = {
                'ImsCourses': '(lecture|course)(s)?',
                       'ImsLecturers': '(lecturer|teacher|instructor|professor)(s)?',
                       'MensaAPI': '(mensa|meal|meals|dish|dishes)',
                'WeatherAPI': '(weather|sunny|rain|snow)',
                'ImsExams': '((exam(s|ination)?|test(s)?)|(failed|repeat) (exam(s)?|test(s)?)|requirement(s)? module(s)?|bachelor(\'*s?) thesis|master(\'*s?) thesis)',
                '_ImsExams_ESFeelJ_': '((exam(s|ination)?|test(s)?)|(failed|repeat) (exam(s)?|test(s)?)|requirement(s)? module(s)?|bachelor(\'*s?) thesis|master(\'*s?) thesis)',
                '_ImsExams_ESThinkJ_': '((exam(s|ination)?|test(s)?)|(failed|repeat) (exam(s)?|test(s)?)|requirement(s)? module(s)?|bachelor(\'*s?) thesis|master(\'*s?) thesis)'
                       }
        elif self.language == Language.GERMAN:
            domains = {'ImsCourses': '(kurs(e)?|vorlesung(en)?)',
                       'ImsLecturers': '(dozent|lehrbeauftragter|lehrperson)(en)?'}
        regex_alterantives = "(what|which|welche) " + domains[self.domain_name]

        if re.search(regex_alterantives, user_utterance, re.I):
            user_act_type = UserActionType.RequestAlternatives
            user_act = UserAct(act_type=user_act_type, text=user_utterance)
            user_acts.append(user_act)
        
        return user_acts
