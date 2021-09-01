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

"""Handcrafted (i.e. template-based) Natural Language Generation Module"""

import inspect
import os

from services.nlg.templates.templatefile import TemplateFile
from services.service import PublishSubscribe
from services.service import Service
from utils.common import Language
from utils.domain.domain import Domain
from utils.logger import DiasysLogger
from utils.sysact import SysAct
from typing import Dict
import string

class HandcraftedNLG(Service):
    """Handcrafted (i.e. template-based) Natural Language Generation Module

    A rule-based approach on natural language generation.
    The rules have to be specified within a template file using the ADVISER NLG syntax.
    Python methods that are called within a template file must be specified in the
    HandcraftedNLG class by using the prefix "_template_". For example, the method
    "_template_genitive_s" can be accessed in the template file via calling {genitive_s(name)}

    Attributes:
        domain (Domain): the domain
        template_filename (str): the NLG template filename
        templates (TemplateFile): the parsed and ready-to-go NLG template file
        template_english (str): the name of the English NLG template file
        template_german (str): the name of the German NLG template file
        language (Language): the language of the dialogue
    """
    def __init__(self, domain: Domain, template_file: str = None, sub_topic_domains: Dict[str, str] = {},
                 logger: DiasysLogger = DiasysLogger(), template_file_german: str = None,
                 language: Language = None):
        """Constructor mainly extracts methods and rules from the template file"""
        Service.__init__(self, domain=domain, sub_topic_domains=sub_topic_domains)

        self.language = language if language else Language.ENGLISH
        self.template_english = template_file
        # TODO: at some point if we expand languages, maybe make kwargs? --LV
        self.template_german = template_file_german
        self.domain = domain
        self.template_filename = None
        self.templates = None
        self.logger = logger

        self.language = Language.ENGLISH
        self._initialise_language(self.language)

    @PublishSubscribe(sub_topics=["sys_act"], pub_topics=["sys_utterance"])
    def generate_system_utterance(self, user_id: str = "default", sys_act: SysAct = None) -> dict(sys_utterance=str):
        """

        Takes a system act, searches for a fitting rule, applies it
        and returns the message.

        Args:
            sys_act (SysAct): The system act, to check whether the dialogue was finished

        Returns:
            dict: a dict containing the system utterance
        """
        rule_found = True
        message = ""

        try:
            message = self.templates.create_message(sys_act)
        except BaseException as error:
            rule_found = False
            self.logger.error(error)
            raise(error)

        # inform if no applicable rule could be found in the template file
        if not rule_found:
            self.logger.info(f'# USER {user_id} # NLG-ERROR ({self.domain.get_domain_name()}) - Could not find a fitting rule for the given system act!')
            self.logger.info(f"# USER {user_id} # NLG-ERROR ({self.domain.get_domain_name()}) - System Action: {str(sys_act.type)} - Slots: {str(sys_act.slot_values)}")

        self.logger.dialog_turn(f"# USER {user_id} # NLG-MSG ({self.domain.get_domain_name()}) - {message}")
        return {'sys_utterance': message}

    def _initialise_language(self, language: Language):
        """
            Loads the correct template file based on which language has been selected
            this should only be called on the first turn of the dialog

            Args:
                language (Language): Enum representing the language the user has selected
        """
        if language == Language.ENGLISH:
            if self.template_english is None:
                self.template_filename = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '../../resources/nlg_templates/%sMessages.nlg' % self.domain.get_domain_name())
            else:
                self.template_filename = self.template_english
        if language == Language.GERMAN:
            if self.template_german is None:
                self.template_filename = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '../../resources/nlg_templates/{}MessagesGerman.nlg'.format(
                        self.domain.get_domain_name()))
            else:
                self.template_filename = self.template_german

        self.templates = TemplateFile(self.template_filename, self.domain)
        self._add_additional_methods_for_template_file()

    def _add_additional_methods_for_template_file(self):
        """add the function prefixed by "_template_" to the template file interpreter"""
        for (method_name, method) in inspect.getmembers(type(self), inspect.isfunction):
            if method_name.startswith('_template_'):
                self.templates.add_python_function(method_name[10:], method, [self])

    def _template_genitive_s(self, name: str) -> str:
        if name[-1] == 's':
            return f"{name}'"
        else:
            return f"{name}'s"

    def _template_genitive_s_german(self, name: str) -> str:
        if name[-1] in ('s', 'x', 'ß', 'z'):
            return f"{name}'"
        else:
            return f"{name}s"

    def _template_plural_s(self, name: str) -> str:
        if name[-1] in ('m', 'e'): # capturing (repeat) exam = (repeat) exams, requirements modules
            return f"{name}s"
        else:
            return f"{name}"

    def _template_cap_name(self, name: str) -> str:
        return string.capwords(name)