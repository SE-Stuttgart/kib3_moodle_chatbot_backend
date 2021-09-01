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
import sys

def get_root_dir():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(get_root_dir())

from utils.domain.jsonlookupdomain import JSONLookupDomain
from tools.nlu.GeneralRegexes import GeneralRegexes


class ImsExamsRegexes(GeneralRegexes):
    """
    Class for generating domain specific regular expressions for Handcrafted Natural Language
    Understanding Module.
    Domain: ImsExams
    """
    def __init__(self):
        """
        Loads:
            - ontology
            - domain key
        Creates:
            - domain-independent regular expressions
            - domain-specific regular expressions
        """
        GeneralRegexes.__init__(self)

        super(ImsExamsRegexes, self).__init__()

        # self.domain = JSONLookupDomain('ImsExams',
        #                                sqllite_db_file=os.path.join('resources', 'databases', 'ImsExams.db'),
        #                                json_ontology_file=os.path.join('resources', 'ontologies', 'ImsExams.json'))

        # self.domain = JSONLookupDomain('ImsExams_ESFeelJ_',
        #                        sqllite_db_file=os.path.join('resources', 'databases', 'ImsExams_ESFeelJ_.db'),
        #                        json_ontology_file=os.path.join('resources', 'ontologies', 'ImsExams_ESFeelJ_.json'))

        self.domain = JSONLookupDomain('ImsExams_ESThinkJ_',
                                       sqllite_db_file=os.path.join('resources', 'databases', 'ImsExams_ESThinkJ_.db'),
                                       json_ontology_file=os.path.join('resources', 'ontologies', 'ImsExams_ESThinkJ_.json'))
        # load ontology
        self.ontology = self.domain.ontology_json
        self.domain_key = self.ontology['key']

        self._set_indomain_regexes()
        self._compile_regexes()
        self._save_indomain_regexes()

    def _set_indomain_regexes(self):
        """
        Creates indomain regular expression

        Returns:

        """

        # Get constants needed for indomain regular expressions from class GeneralRegexes
        self.init_request_constants()
        self.init_inform_constants()
        self.init_article_constants()
        self.init_adjective_constants()

        # *** User requests ***
        # Generating complete regular expressions for requests
        self._set_request_regexes()

        # *** User informs ***
        # Generating complete regular expressions for informs
        self._set_inform_regexes()

    def _set_slot_regex(self):
        """
        Defines all vocabulary/synonyms linked to slots and the regular expression related to them.

        Returns:

        """

        # Getting user requestable slot and creating a dic with empty string values
        self.user_requestable_slots = self.ontology["requestable"]
        self.slot_regex = dict.fromkeys(self.user_requestable_slots, '')
        
        self.slot_regex["registration"] = "(?=(registration" 
        self.slot_regex["registration"] += "|register(ing)?|enroll(ing)?|sign(ing)? up|subscribe|subscribing))"

        self.slot_regex["registration_period_sose"] = "(?=((summer|\\bsose\\b)+(\s)?(semester\s|term\s)?(registration (phase|period|deadline))?))(?=(?:(?!((miss(ed)? (the )?)?registration (phase|period|deadline)))))"

        self.slot_regex["registration_period_wise"] = "(?=((winter|\\bwise\\b)+(\s)?(semester\s|term\s)?(registration (phase|period|deadline))?))(?=(?:(?!((miss(ed)? (the )?)?registration (phase|period|deadline)))))"

        self.slot_regex["acceptance_belated_registration"] = "(?=(miss(ed)? the (registration (phase|period|deadline))))(?=(?:(?!((summer\s|\bsose\b\s|winter|\bwise\b)(semester\s|term\s)?(registration (phase|period|deadline))))))"
        self.slot_regex["acceptance_belated_registration"] += "|(?=(((have\s|\'*ve\s)?(forgot(ten)?(\sto\s)?|missed(\sto\s)?|failed(\sto\s)?))|(did not\s|did\'*nt\s)|(have not\s|haven\'*t\s|\'*ve not\s))(register(ed|ing)?|enroll(ed|ing)?|sign(ed|ing)? up|subscribing|subscribe(d)?))(?=(?:(?!((registration|register(ing)?|enroll(ing)?|sign(ing)? up|subscribe|subscribing)))))"

        self.slot_regex["registration_withdrawal"] = "(?=(withdrawal|deregistration"
        self.slot_regex["registration_withdrawal"] += "|deregister(ing)?(\s)?(from)?|withdraw(ing)?(\s)?from|drop(ping)?|change|changing|return(ing)?))"

        self.slot_regex["acceptance_missed_withdrawal"] = "(?=(miss(ed)? the (withdrawal|deregistration) (phase|period|deadline)))(?=(?:(?!((summer\s|\bsose\b\s|winter|\bwise\b)(semester\s|term\s)?(registration (phase|period|deadline))))))"
        self.slot_regex["acceptance_missed_withdrawal"] += "|(?=((have|\'*ve)? (forgot(ten)?|missed|failed)|(did not|did\'*nt)|(have not|haven\'*t|\'*ve not)).*(deregister(ed|ing)?(\s)?(from)?|withdraw(ed|ing)?(\s)?(from)?|drop(ped|ping)?|change(d)?|changing|return(ed|ing)?))(?=(?:(?!((withdrawal|deregistration|deregister(ing)?(\s)?(from)?|withdraw(ing)?(\s)?from|drop(ping)?|change|changing|return(ing)?)))))"
      
        self.slot_regex["acceptance_illness_withdrawal"] = "(?=((case of\s)?(sick(ness)?|ill(ness)?)|(feeling)?(\s)?unwell|not feeling well))"
        
        self.slot_regex["contact_registration_problem"] = "(?=((registration\s|deregistration\s|withdrawal\s)?(problems|issues|difficulties|trouble|strain)))" 


    def _set_value_regex(self):
        """
        Defines a dictionary with simple regular expressions, one per value, ie. '(\\b value
        \\b)', given a particular slot. Values are obtained from the ontology.

        Returns:

        """

        self.user_informable_slots = self.ontology["informable"]
        self.slot_values_regex = dict.fromkeys(self.user_informable_slots)

        # Iteration over all slots and all values, resulting on dic{slot:{value:regex}}
        for slot in self.slot_values_regex.keys():
            slot_values = self.user_informable_slots[slot]
            self.slot_values_regex[slot] = {value: "(?=(\\b" + str(value) + "\\b"
                                            for value in slot_values}

    def _set_request_regexes(self):
        """
        Creates final regular expressions for user requests

        Returns:

        """

        # uses all vocabulary/synonyms linked to slots and the regular expression related to them
        self._set_slot_regex()
        # necessary for domain-specific regexes
        self._set_value_regex()
        # necessary for domain-specific regexes
        self._set_synonyms() 

        self.request_regex = dict.fromkeys(self.user_requestable_slots)
        for slot in self.request_regex.keys():

            self.request_regex["registration"] = self.REQUEST_HOW + " " + self.slot_regex["registration"]
            self.request_regex["registration"] += "|" + self.rINFORM_WANT + " " + self.slot_regex["registration"]
            self.request_regex["registration"] += "|" + self.REQUEST_CAN + " " + self.slot_regex["registration"]
            self.request_regex["registration"] += "|" + self.REQUEST_WHAT_WANT + " " + self.slot_regex["registration"]
            

            self.request_regex["registration_period_sose"] = self.REQUEST_WHEN + ".*" \
                                                            + self.slot_regex["registration_period_sose"] + "(\s)?(take place|start)?"
            self.request_regex["registration_period_sose"] += "|" + self.rINFORM_WANT + " " + self.slot_regex["registration"] + ".*" + self.slot_regex["registration_period_sose"]

            self.request_regex["registration_period_wise"] = self.REQUEST_WHEN + ".*" \
                                                            + self.slot_regex["registration_period_wise"] + "(\s)?(take place|start)?"
            self.request_regex["registration_period_wise"] += "|" + self.rINFORM_WANT + " " + self.slot_regex["registration"] + ".*" + self.slot_regex["registration_period_wise"]


            self.request_regex["acceptance_belated_registration"] = "(\\b|^| )" + ".*" + self.slot_regex["acceptance_belated_registration"]
            self.request_regex["acceptance_belated_registration"] += "|" + self.REQUEST_WHAT + ".*" + self.slot_regex["acceptance_belated_registration"]
            self.request_regex["acceptance_belated_registration"] += "|" + ".*" + self.ADJECTIVES_POST + "the (registration (phase|period|deadline))"
            # self.request_regex["acceptance_belated_registration"] += "|" + self.REQUEST_CAN + ".*" + self.slot_regex["registration"] + self.ADJECTIVES_POST


            self.request_regex["registration_withdrawal"] = self.REQUEST_HOW + " " + self.slot_regex["registration_withdrawal"]
            self.request_regex["registration_withdrawal"] += "|" + self.rINFORM_WANT + " " + self.slot_regex["registration_withdrawal"]
            self.request_regex["registration_withdrawal"] += "|" + ".*" + self.slot_regex["registration_withdrawal"]
            # self.request_regex["registration_withdrawal"] += "|" + self.REQUEST_CAN + " " + self.slot_regex["registration_withdrawal"]
            self.request_regex["registration_withdrawal"] += "|" + self.REQUEST_WHAT_WANT + " " + self.slot_regex["registration_withdrawal"]
            self.request_regex["registration_withdrawal"] += "|" + "(\\b|^| )(I (do not|don(\'*t)) think that I(\'*m|\sam)? well prepared)" 
            self.request_regex["registration_withdrawal"] += "|" + "(\\b|^| )" + self.DONTWANT


            self.request_regex["acceptance_missed_withdrawal"] = "(\\b|^| )" + ".*" + self.slot_regex["acceptance_missed_withdrawal"]
            self.request_regex["acceptance_missed_withdrawal"] += "|" + self.REQUEST_WHAT + " " + self.slot_regex["acceptance_missed_withdrawal"]
            self.request_regex["acceptance_missed_withdrawal"] += "|" + self.REQUEST_CAN + ".*" + self.ADJECTIVES_POST + "(withdrawal|deregistration) (phase|period|deadline)"
            # self.request_regex["acceptance_missed_withdrawal"] += "|" + self.REQUEST_CAN + ".*" + self.slot_regex["registration_withdrawal"] + self.ADJECTIVES_POST 
        
            self.request_regex["acceptance_illness_withdrawal"] = ".*" + self.slot_regex["acceptance_illness_withdrawal"]
            self.request_regex["acceptance_illness_withdrawal"] += "|" + self.rINFORM_WANT + " " + self.slot_regex["registration_withdrawal"] + ".*" \
                                                                + "((because I(\'*m|\sam)?)|in)? " + self.slot_regex["acceptance_illness_withdrawal"]
            self.request_regex["acceptance_illness_withdrawal"] += "|" + self.REQUEST_CAN + ".*" + "(interrupt|pause|postpone|move|shift|defer|delay|reschedule|relocate|remit|change|switch|rearrange|push|displace|dislocate)" \
                                                                + self.ARTICLES + ".*" \
                                                                + "(deadline|submission date|date of submission)?" + "(\s)?((because I(\'*m|\sam)?)|in)? " \
                                                                + self.slot_regex["acceptance_illness_withdrawal"]
            self.request_regex["acceptance_illness_withdrawal"] += "|(\\b|^| )" + "((have to|\'*ve to|want to|need to|must) (interrupt|pause|postpone|move|shift|defer|delay|reschedule|relocate|remit|change|switch|rearrange|push|displace|dislocate))" \
                                                                + ".*" + "(deadline|submission date|date of submission)?" + "(\s)?(because I(\'*m|\sam)?)? " \
                                                                + self.slot_regex["acceptance_illness_withdrawal"]      
                                    

            self.request_regex["contact_registration_problem"] = self.REQUEST_WHAT + ".*" + self.slot_regex["contact_registration_problem"]                                                       

            self.request_regex["contact_registration_problem"] += "|(\\b|^| )(I have(\s)?(got\s)?|I\'*ve(\s)?(got\s)?)?" + self.slot_regex["contact_registration_problem"]
            
            self.request_regex["contact_registration_problem"] += "|(\\b|^| )(I )?(cannot|can\'*t) (gather|obtain|download|get|find)(\sthe)?" \
                                                                + ".*" + "(application (form|sheet))(\s)?(stored in Campus(\s)?(under the tab (\"|\')?\bmy application\b(\"|\')?)?)?"

    def _set_inform_regexes(self):
        """
        Creates final regular expressions for user informs

        Returns:

        """

        # Setting partial regexes to detect mentioned slots
        self._set_slot_regex()
        # Setting partial regexes to detect mentioned values
        self._set_value_regex()
        # Setting value synonyms
        self._set_synonyms()

        self.inform_regex = dict.fromkeys(self.user_informable_slots) # self.user_informable_slots = self.ontology["informable"]
        for slot in self.inform_regex.keys():
            self.inform_regex[slot] = {}
            for value in self.slot_values_regex[slot].keys():
                #if value != "na":
                self.inform_regex[slot][value] = self.slot_values_regex[slot][value]
                self.inform_regex[slot][value] += "|" + self.rINFORM_WANT_INFO + "(" + self.slot_values_regex[slot][value] + ")"


    def _set_synonyms(self):
        """
        Defines the regular expressions that include synonyms. This can grow easily.

        Returns:

        """

        slot = "name" 

        #'|(repeat (exam(s|ination)?|test(s)?))|(((have(\s)?|\'*ve(\s)?)?failed|(did not|did\'*nt) pass|(have not|haven\'*t|\'*ve not) passed)(\smy|\san)? (exam(s)?|test(s)?))'
                                                        
        self.slot_values_regex[slot]['repeat exam'] += '|repeat (exam(s|ination)?|test(s)?)))' #(?=(?:(?!(\bexam\b|exam(s|ination)?|test(s)?))))
        self.slot_values_regex[slot]['exam'] += '|exam(s|ination)?|test(s)?))' #(?=(?:(?!(\brepeat exam\b|repeat (exam(s|ination)?|test(s)?)))))'
        self.slot_values_regex[slot]['requirements module'] += '|requirement(s)? module(s)?))'
        self.slot_values_regex[slot]['bachelor thesis'] += '|bachelor thesis(\s)?(topic)?|(bachelor(\'*s?) thesis(\s)?(topic)?)))'
        self.slot_values_regex[slot]['master thesis'] += '|master thesis(\s)?(topic)?|(master(\'*s?) thesis(\s)?(topic)?)))'
        
    def _save_indomain_regexes(self):
        """
        Saves indomain regular expressions (requests and informs) in JSON files.

        Returns:

        """

        # Saving Requests
        with open(self.base_folder + "/" + self.domain.name + "RequestRules.json", 'w') as fp:
            json.dump(self.request_regex, fp, indent=4)

        # Saving Informs
        with open(self.base_folder + "/" + self.domain.name + "InformRules.json", 'w') as fp:
            json.dump(self.inform_regex, fp, indent=4)

    def _save_all_regexes(self):
        """
        Saves out- and in-domain regular expressions (requests and informs) in JSON files.

        Returns:

        """
        self.save_general_regexes()
        self._save_indomain_regexes()

    def _compile_regexes(self):
        """
        Compiling  out- and in-domain regular expression in order to find syntactic errors
        It triggers and shows the error, if found

        Returns:

        """

        test_passed = True

        # General regexes
        for act, regex in self.general_regex.items():
            try:
                re.compile(regex)
            except re.error as err:
                print("Regex error in General_Act(%s): %s" % (act, err))
                test_passed = False

        # Requests
        for slot, regex in self.request_regex.items():
            try:
                re.compile(regex)
            except re.error as err:
                print("Regex error in Request(%s): %s" % (slot, err))
                test_passed = False

        # Informs
        for slot, values in self.inform_regex.items():
            for value, regex in values.items():
                try:
                    re.compile(regex)
                except re.error as err:
                    print("Regex error in Inform(%s='%s'): %s" % (slot, value, err))
                    test_passed = False

        if test_passed:
            print('No regex errors found in %s!' % self.domain.name)
        else:
            exit()

    def match_regexes(self, text):
        """
        Tests regular expressions in offline mode given the user input (text)

        Args:
            text {str} - string to be matched against all regexes

        Returns:

        """

        for act, regex in self.general_regex.items():
            if re.search(regex, text, re.I):
                print('\nAct: %s' % act)

        for slot, regex in self.request_regex.items():
            if re.search(regex, text, re.I):
                print('\nType: Request, Slot: %s' % slot)

        for slot, values in self.inform_regex.items():
            for value, regex in values.items():
                if re.search(regex, text, re.I):
                    print('\nType: Inform, Slot: %s, Value: %s' % (slot, value))


if __name__ == '__main__':
    pass
    rest_regexes = ImsExamsRegexes()

    while True:
        rest_regexes.match_regexes(input('\n\nType a text to be matched: '))