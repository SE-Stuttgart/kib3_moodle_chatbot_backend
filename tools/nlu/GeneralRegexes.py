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

def _get_root_dir() -> str:
    """
    returns the relative path of adviser2.0/resources/nlu_regexes

    Returns {str} - relative path foe

    """
    head_location = os.path.realpath(os.curdir)
    end = head_location.find('adviser2.0')
    return os.path.join(head_location[:end], 'adviser2.0')
sys.path.append(_get_root_dir())

from utils import UserActionType

class GeneralRegexes(object):
    """
    Class for generating domain dependent regular expressions for Handcrafted Natural Language
    Understanding Module
    """

    def __init__(self):
        self.base_folder = os.path.join(_get_root_dir(), 'resources', 'nlu_regexes')
        self.general_regex = {}
        self._set_general_regex()
        self._compile_general_regexes()
        self.save_general_regexes()

    def _hello(self) -> str: # ADJUSTED BY GIANNA
        """
        It builds and returns a regular expression for the user act Hello

        Returns:
            regex {str} - regular expression
        """
        synonyms = ['hi', 'hi there', 'hello', 'howdy', 'hey', 'good morning', 'good day', 'good afternoon', 'good evening']
        regex = '(\\b|^| )' + '(' + '|'.join(synonyms) + ')' + '(\\b|$| )'
        return regex

    def _bye(self) -> str: # ADJUSTED BY GIANNA
        """
        It builds and returns a regular expression for the user act Bye

        Returns:
            regex {str} - regular expression
        """
        regex = "(\\b|^| )(bye|that'?s? (is )*(it|all)|that'?s? (is )*(about it)|(see|c) (you|u)(( later| l8er| soon)?)" \
                "|talk (to|2) (you|u)(( later| l8er| soon)?)|farwell|ciao|adieu|au revoir)(\\s|$| |\\.)"
        return regex

    def _restart(self) -> str:
        """
        It builds and returns a regular expression for the user act Restart

        Returns:
            regex {str} - regular expression
        """
        regex = "(\\b|^| )(restart)"
        return regex

    def _deny(self) -> str: # ADJUSTED BY GIANNA
        """
        It builds and returns a regular expression for the user act Deny

        Returns:
            regex {str} - regular expression
        """
        negate_list = ['n(o)?', 'wrong', 'incorrect', 'error', 'nope', 'nay', 'nah', 'false']
        affirm_list = ['true', 'correct', 'right']
        regex = "((\\b|^| )(" + '|'.join(negate_list) + ")|(not (" + '|'.join(affirm_list) + ")))(\\s)?$"
        return regex

    @staticmethod
    def _affirm() -> str: # ADJUSTED BY GIANNA
        """
        It builds and returns a regular expression for the user act Affirm

        Returns:
            regex {str} - regular expression
        """
        regex = "((yes|yeah|(\\b|^)ok\\b|(\\b|^)OK|okay|sure|indeed|^y$|(\\b|^)yep(\\b|$)" \
                "|(that('?s| is) )?(?<!not )(?<!no )(right|correct|confirm)))(\\s)?$"
        return regex

    @staticmethod
    def _thanks() -> str: # ADJUSTED BY GIANNA
        """
        It builds and returns a regular expression for the user act Thanks

        Returns:
            regex {str} - regular expression
        """
        good_synonyms = ['alright', 'allright', 'all right', 'well', 'okay','great', 'good', 'awesome', 'nice', 'cool', 'amazing', 'splendid', 'gorgeous', 'fantastic', 'excellent']
        good = '((oh\s|ah\s|uh\s)?(' + '|'.join(good_synonyms) + '))'
        bad_synonyms = ['damn','fuck', 'shit(ty)?', 'man', 'bloody']
        bad = '((oh\s|ah\s|uh\s)?(' + '|'.join(bad_synonyms) + '))'
        helpful = "(that(\')?s| (is|was)) (very )?(helpful|supportive|encouraging|caring|sympathetic|great|good|awesome|nice|cool|amazing|splendid|gorgeous|fantastic|excellent)"
        thank = "((thank|thank(s| you)( (very|so) much)?)|(I (understand|see|get it)))"
        thanks = "(^( )?)((" + good + " )?(" + helpful + " )?" \
                + "(" + good + " )?(" + thank + " )?" \
                + thank + "( " + helpful + ")?|(" + good + " )?" \
                + helpful + "|" + good + "|" + bad + ")(( )*)"
        # Bye should not appear
        regex = "(?=.*" + thanks + ")(?=^(?:(?!bye).)*$).*$"
        return regex

    def _repeat(self) -> str:
        """
        It builds and returns a regular expression for the user act Repeat

        Returns:
            regex {str} - regular expression
        """
        regex = "(\\b|^| )(repeat( that| it)?|say( that | it) again|(again))"
        return regex

    def _request_alternatives(self) -> str:
        """
        It builds and returns a regular expression for the user act Request Alternatives

        Returns:
            regex {str} - regular expression
        """
        regex = "(\\b|^| )((something|anything) else)|(different( one)*)|(another one)" \
                "|(alternatives*)|(other options*)" \
                "|((don\'*t|do not) (want|like) (that|this)( one)*)"
        return regex

    def _dontcare(self) -> str:
        """
        It builds and returns a regular expression for the user act "Contextual Don't Care"

        Returns:
            regex {str} - regular expression
        """
        regex = "(anything(?! else)|((any$|any kind)|(i )*(don\'?t|do not) (care|know|mind))" \
                "($|(?! (a?bout|of|what))|( (a?bout|of|what) (type|kind)(?! of))| a?bout " \
                "(that|this))|(any(thing)? (is )*(fine|ok\\b|okay|will do))" \
                "($| and| but)|(it )?(doesn\'?t|does not) matter)+"
        return regex

    def _req_everything(self):
        """
        It builds and returns a regular expression to find user intent of getting all information
        related to an entity, for instance:
        - Say everything about...
        - I want to know about...

        Returns:
            regex {str} - regular expression
        """
        regex = '(\\b|^| )(((say|tell( me)?)|(want|need) to know)( everything)? about)'
        return regex

    def init_request_constants(self): # GIANNA

        """
        It defines constants that are inherited by classes building user requests

        Returns:

        """
        # REQUESTS:
        self.HOW = "(how (does|do I(\shave to|\sneed to)?))"
        self.CAN = "((how )?(can|shall|must) I(\s)?(still\s|also\s)?|is (it possible to|there a way to))"
        self.WHAT = "((what (do I (have to\s|need to\s)?|happens|(must|shall) I\s|am I supposed to\s)do)(\snow|\sif I)?)" 
        self.WHEN = "((when (does|will|is)?|(during|within) which ((time(frame|\sframe|\speriod)?)|period)(\sis)?))"
        
        self.REQUEST_HOW = "(\\b|^| )" + self.HOW
        self.REQUEST_CAN = "(\\b|^| )" + self.CAN
        self.REQUEST_WHAT = "(\\b|^| )" + self.WHAT 
        self.REQUEST_WHAT_WANT = "(\\b|^| )" + self.WHAT + " " + "(to|want to|have to|need to|must)?"
        self.REQUEST_WHAT_DONTWANT = "(\\b|^| )" + self.WHAT + " " + "((do not|don\'*t) want (to\s)?)?"
        self.REQUEST_WHEN = "(\\b|^| )" + self.WHEN

    def init_inform_constants(self): # GIANNA

        """
        It defines constants that are inherited by classes building user requests

        Returns:

        """
        # INFORMS:
        self.WANT = "(to|want to|have to|need to|must)"
        self.WANT_INFO = "((((I have|I\'*ve)( got)?( a)? question(s)? about)|(I (need|want) information(s)? about)) (the|my|a(n)?|\s)?\s?)"
        self.DONTWANT = "((do not|don\'*t) want (to\s)?)"

        self.rINFORM_WANT = "(\\b|^| )" + self.WANT
        self.rINFORM_WANT_INFO = "(\\b|^| )" + self.WANT_INFO 
        self.rINFORM_DONTWANT = "(\\b|^| )" + self.DONTWANT

    def init_article_constants(self): # GIANNA

        """
        It defines article and preposition constants that are inherited by classes building user ínforms and request

        Returns:

        """
        self.ARTICLES = "(the|my|a(n)?)?"
        self.PREPOSITIONS = "(during|within)?"

        self.ARTICLES_FOR = "(for)?(\s)?" + self.ARTICLES 
        self.rPREPOSITIONS = "(\\b|^| )" + self.PREPOSITIONS

    def init_adjective_constants(self): # GIANNA

        """
        It defines adjective constants that are inherited by classes building user ínforms and request

        Returns:

        """
        self.ADJECTIVES_PRE = "(respective|current|last|recent|latest)?"
        self.ADJECTIVES_POST = "(after(wards|\sthat)?|later(\son)?|outside)?"

    def _set_general_regex(self):
        """
        Sets all regular expressions that cover general user acts.

        Returns:

        """
        # Hello
        self.general_regex[UserActionType.Hello.value] = self._hello()

        # Bye
        self.general_regex[UserActionType.Bye.value] = self._bye()

        # Restart
        # self.general_regex[UserActionType.Restart.value] = self._restart()

        # Deny
        self.general_regex[UserActionType.Deny.value] = self._deny()

        # Affirm
        self.general_regex[UserActionType.Affirm.value] = self._affirm()

        # Thanks
        self.general_regex[UserActionType.Thanks.value] = self._thanks()

        # Repeat
        #self.general_regex[UserActionType.Repeat.value] = self._repeat()

        # Request Alternatives
        self.general_regex[UserActionType.RequestAlternatives.value] = self._request_alternatives()

        # Contextual dontcares: i.e things that should be labelled inform(=dontcare)
        self.general_regex['dontcare'] = self._dontcare()

        self.general_regex['req_everything'] = self._req_everything()

    def _compile_general_regexes(self):
        """
        Compiling all regular expression in order to find syntactic errors
        It triggers and shows the error if found

        Returns:

        """
        test_passed = True

        for act, regex in self.general_regex.items():
            try:
                re.compile(regex)
            except re.error as err:
                print("Regex error in General_Act(%s): %s" % (act, err))
                test_passed = False

        if test_passed:
            print('No regex errors found in general regexes!')
        else:
            exit()

    def match_regexes(self, text: str):
        """
        Tests regular expressions in offline mode given the user input (text)

        Args:
            text {str} - string to be matched against all regexes

        Returns:

        """
        for act, regex in self.general_regex.items():
            if re.search(regex, text, re.I):
                print('\nAct: %s' % act)

    def save_general_regexes(self):
        """
        Saves general regular expressions in JSON files.

        Returns:

        """
        with open(self.base_folder + '/GeneralRules.json', 'w') as fp:
            json.dump(self.general_regex, fp, indent=4)


if __name__ == '__main__':
    pass
    gen_regexes = GeneralRegexes()

    while True:
        gen_regexes.match_regexes(input('\n\nType a text to be matched: '))
