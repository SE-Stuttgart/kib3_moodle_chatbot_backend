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

"""Handcrafted (i.e. template-based) Natural Language Generation Module"""

import inspect
import os

from services.nlg.templates.templatefile import TemplateFile
from services.service import PublishSubscribe
from services.service import Service
from utils.common import Language
from utils.domain.domain import Domain
from utils.logger import DiasysLogger
from utils.sysact import SysAct, SysActionType
from typing import Dict, List


class ELearningNLG(Service):
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
                 logger: DiasysLogger = DiasysLogger()):
        """Constructor mainly extracts methods and rules from the template file"""
        Service.__init__(self, domain=domain, sub_topic_domains=sub_topic_domains)
        self.logger = logger

    def join_values(self, values: List[str], interior_join: str = ", ", final_join: str="oder"):
        return f"{interior_join.join(values[:-1])} {final_join} {values[-1]}"
    
    def _template_genitive_s_german(self, name: str) -> str:
        if name[-1] in ('s', 'x', 'ß', 'z'):
            return f"{name}'"
        else:
            return f"{name}s"



    def request_initial_goal(self, goal):
        return ["""Willst du heute neue Inhalte lernen, oder abgeschlossene Inhalte wiederholen?"""]

    # TODO is insufficient = 'none' a string, or of type(None)?
    def request_repeat_quiz(self, quiz_link, module, insufficient):
        if insufficient == True:
            return [f"""Bei {module} hast du leider noch nicht ausreichend Punkte 🙁.
                    Möchtest du die Quizzes dazu wiederholen?"""]
        elif insufficient == False:
            return [f""""Du hast überall ausreichend Punkte erzielt, gut gemacht!
                    Möchtest du einige Quizzes wiederholen, um die Inhalte aufzufrischen?"""]
        elif insufficient == "none":
            return ["""Frag mich nochmal, wenn du ein Quiz abgeschlossen hast 😁"""]


    # TODO what should happen if moduleRequirements == False or moduleRequired == False?
    # seems like that kind of logic should be moved to the policy, or we need to handle output for the other cases
    def inform_new_module_matching_requirements(self, moduleRequirements: bool, moduleRequired: bool, moduleName: str):
        if moduleRequirements == True and moduleRequired == True:
            return [f"""Alles klar. 
            Es gibt neues Material zu {moduleName}, für das du die Voraussetzungen erfüllst.
            Erinnerst du dich noch an das vorherige Modul?"""]

    def inform_positive_feedback_test(self, positiveFeedback: bool, test):
        return ["""Cool! Ich kann dir helfen, das Gelernte zu überprüfen.
                Wenn du bereit bist, stelle ich dir Fragen dazu."""]
    
    def inform_positive_feedback_repeat_quiz(self, positiveFeedback: bool, repeatQuiz: bool):
        return ["""Cool! Du könntest die Quizzes regelmäßig wiederholen, damit du die Inhalte bis zur Prüfung nicht vergisst!"""]

    def inform_repeat_content_finished(self, moduleName, repeatContent, link, contentType):
        if contentType == "resource":
            return [f"""Du hast {moduleName} seit einiger Zeit abgeschlossen. 
                    Wie wäre es, wenn Du es nochmal durchgehst?
                    {link}"""]
        elif contentType == "book":
            return [f"""Du hast das Buch {moduleName} seit einiger Zeit abgeschlossen.
                    Hast Du Lust, es nochmal anzusehen?
                    {link}"""]
        elif contentType == "quiz":
            return [f"""Du hast das Quiz {moduleName} seit einiger Zeit abgeschlossen.
                    Wiederhole dann bitte die Quizzes:
                    {link}"""]
        elif contentType == "hvs":
            return [f"""Du hast das Quiz {moduleName} seit einiger Zeit abgeschlossen.
                    Wiederhole dann bitte die Quizzes:
                    {link}"""]
        else:
            return [f"""Du hast {moduleName} seit einiger Zeit abgeschlossen. Schau es Dir nochmal an: {link}"""]

    # TODO is 'hvs' the correct activity name? or should it be hvp?
    # TODO repeatContent = 'noContent': we should suggest a few concrete alternatives here!
    def inform_repeat_content(self, moduleName, repeatContent, link, contentType):
        if repeatContent == "finished":
            return self.inform_repeat_content_finished(moduleName, repeatContent, link, contentType)
        elif repeatContent == "module":
            return [f"""u hast bei {moduleName} nicht alles richtig beantwortet 😬 .
                    Es wäre bestimmt gut, wenn du das wiederholst, diesmal klappt es bestimmt besser!
                    {link}"""]
        elif repeatContent == "oldcontent":
            return [f"""Du hast {moduleName} seit einiger Zeit nicht mehr angeklickt.
                    Du könntest die Inhalte nochmal auffrischen, ansonsten vergiss du sie!
                    {link}"""]
        elif repeatContent == "noContent":
            return [f"""Es gibt keine Inhalte, die du wiederholen solltest.
                    Du könntest mit einem neuen Thema anfangen!"""]

    # TODO: add links to all of these messages!
    def inform_finish_module(self, moduleName, finishContent):
        if finishContent == "video":
            return [f"""Es gibt ein Video zu {moduleName}, das Du noch nicht gesehen hast.
                    Das könntest du heute noch schnell abschließen :-) """]
        elif finishContent == "frage":
            return ["""Du hast die Fragen zu einem Video nicht zu Ende beantwortet.
                    Das könntest du schnell noch erledigen!"""]
        elif finishContent == "module":
            return ["""Du solltest am besten das Modul von gestern abschließen, es fehlt dir nicht mehr viel!"""]
        elif finishContent == "doku":
            return ["""Letztes Mal hast du angefangen, die Dokumentation deines Projekts auszufüllen.
                    Du solltest sie am besten heute fertig machen 🙂"""]

    def inform_remind_subission_deadline(self, moduleName, submission):
        if submission == "-":
            return [f"""Es gibt im Moment keine Abgaben."""]
        return [f"""Am {submission} für {moduleName}"""]




    def welcomemsg_first(self):
        return  ["""Hallo, ich bin der Moodle Assistent!
        Ich kann dir helfen bei:
        <ul>
            <li>Suche nach Inhalten</li>
            <li>Fortschritt überprüfen</li>
            <li>Navigation zu Lehrinhalten</li>
            <li>usw.</li>
        </ul>""",
        "Du kannst auch auf das Zahnrad oben klicken, um meine Einstellungen ändern."]

    def welcomemsg_continue_unfinished(self, last_activity):
        return [f"""Schön dich wieder zu sehen!
        Letztes Mal hast du bei {last_activity} aufgehört, willst du es heute abschließen?"""]

    # TODO figure out how to offer a summary of options
    def welcomemsg_continue_next(self, last_activity, followup_activity_list):
        return [f"Schön dich wieder zu sehen!",
        f"""Letztes Mal hast du {last_activity} abgeschlossen, willst du heute weitermachen mit {self.join_values(followup_activity_list)}"""]

    def welcomemsg_goal_badge(self, badge_name, missing_activities):
        return [f"""Hi! Du hast fast den Badge {badge_name} abgeschlossen! Wenn du heute {self.join_values(values=missing_activities, final_join='und')}
        fertig machst, kriegst du ihn 😊"""]

    def welcomemsg_forgotten_module(self, module_name, activity_name, next_module_name):
        return [f"""Schön dich wieder zu sehen! Du hast Thema {module_name} schon angefangen aber noch nicht abgeschlossen, vergiss nicht ihn weiter zu machen"""]

    # TODO figure out how to offer a summary of options
    def welcomemsg_review_or_next(self, review: bool, followup_activity_list: List[str], percentage_done_quizzes: float, percentage_repeated_quizzes: float):
        """ Offer choice to either review previous quizes, or continue with one of the next activities"""
        return ["""Hi!""",
                f"""$DONUT,{100*percentage_done_quizzes},{100*percentage_repeated_quizzes}"""]

    def welcomemsg_unread_messages(self):
        """ Notify about unread forum messages """
        pass

    def welcomemsg_deadline_reminder(self):
        """ Remind about upcoming assignments using calendar """
        pass

    def welcomemsg_stats(self, weekly: bool, congratualations: bool):
        """ 
        Args:
            weekly: If true, show activity of current and last week at end of current week.
                    If false, show total course progress.
            congratulations: If true, add congratulation message """
        pass



    def generate_welcomemsg(self, sys_act: SysAct):
        if "badge_name" in sys_act.slot_values and "missing_activities" in sys_act.slot_values:
            return self.welcomemsg_goal_badge
        elif "module_name" in sys_act.slot_values and "activity_name" in sys_act.slot_values and "next_module_name" in sys_act.slot_values:
            return self.welcomemsg_forgotten_module
        elif "review" in sys_act.slot_values and "followup_activity_list" in sys_act.slot_values and "percentage_done_quizzes" in sys_act.slot_values and "percentage_repeated_quizzes" in sys_act.slot_values:
            return self.welcomemsg_review_or_next
        elif "followup_activity_list" in sys_act.slot_values:
            return self.welcomemsg_continue_next
        elif "last_activity" in sys_act.slot_values:
            return self.welcomemsg_continue_unfinished
        elif len(sys_act.slot_values) == 0:
            return self.welcomemsg_first
        raise Exception(f"Sysact Welcome called with invalid slot combination: {list(sys_act.slot_values.keys())}")

    def generate_request(self, sys_act: SysAct):
        if "goal" in sys_act.slot_values:
            return self.request_initial_goal
        elif "quiz_link" in sys_act.slot_values and "module" in sys_act.slot_values and "insufficient" in sys_act.slot_values:
            return self.request_repeat_quiz
        raise Exception(f"Sysact Request called with invalid slot combination: {list(sys_act.slot_values.keys())}")

    def generate_inform(self, sys_act: SysAct):
        if "moduleRequirements" in sys_act.slot_values and "moduleName" in sys_act.slot_values and "moduleRequired" in sys_act.slot_values:
            return self.inform_new_module_matching_requirements
        elif "positiveFeedback" in sys_act.slot_values and "test" in sys_act.slot_values:
            return self.inform_positive_feedback_test
        elif "positiveFeedback" in sys_act.slot_values and "repeatQuiz" in sys_act.slot_values:
            return self.inform_positive_feedback_repeat_quiz
        elif "moduleName" in sys_act.slot_values and "repeatContent" in sys_act.slot_values and "link" in sys_act.slot_values and "contentType" in sys_act.slot_values:
            return self.inform_repeat_content
        elif "moduleName" in sys_act.slot_values and "finishContent" in sys_act.slot_values:
            return self.inform_finish_module
        elif "moduleName" in sys_act.slot_values and "submission" in sys_act.slot_values:
            return self.inform_remind_subission_deadline
        raise Exception(f"Sysact Inform called with invalid slot combination: {list(sys_act.slot_values.keys())}")



    def get_message_fn(self, sys_act: SysAct):
        # delegate system act to specific message generator
        if sys_act.type == SysActionType.Welcome:
            return self.generate_welcomemsg(sys_act)
        elif sys_act.type == SysActionType.Request:
            return self.generate_request(sys_act)
        elif sys_act.type == SysActionType.Inform:
            return self.generate_inform(sys_act)
        raise NotImplementedError




    @PublishSubscribe(sub_topics=["sys_act"], pub_topics=["sys_utterance"])
    def publish_system_utterance(self, user_id: str, sys_act: SysAct = None) -> dict(sys_utterance=List[str]):
        """Generates the system utterance and publishes it.

        Args:
            sys_act (SysAct): The system act published by the policy

        Returns:
            dict: a dict containing the system utterance
        """
        message_fn = self.get_message_fn(sys_act)
        messages = message_fn(**sys_act.slot_values)
        for message in messages:
            self.logger.dialog_turn(f"# USER {user_id} # NLG - {message}")
        return {'sys_utterance': messages}
