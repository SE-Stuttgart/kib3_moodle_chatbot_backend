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
import random
import json
from datetime import datetime

from services.nlg.templates.templatefile import TemplateFile
from services.service import PublishSubscribe
from services.service import Service
from utils.common import Language
from utils.domain.domain import Domain
from utils.logger import DiasysLogger
from utils.sysact import SysAct, SysActionType
from typing import Dict, List, Union


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

    def request_review_or_next(self):
        msgs = []
        if random.random() < 0.4:
            msgs.append((f"""Regelmäßiges Wiederholen von Lerninhalten führt dazu, dass du dich besser an die Inhalte erinnern kannst.""", []))
        msgs.append(("Willst du etwas Zeit nehmen um die Inhalte zu wiederholen?", ["Wiederholen", "Weitermachen"]))
        return msgs
        
    # TODO what should happen if moduleRequirements == False or moduleRequired == False?
    # seems like that kind of logic should be moved to the policy, or we need to handle output for the other cases
    def inform_new_module_matching_requirements(self, moduleRequirements: bool, moduleRequired: bool, moduleName: str):
        if moduleRequirements == True and moduleRequired == True:
            return [f"""Alles klar. 
            Es gibt neues Material zu {moduleName}, für das du die Voraussetzungen erfüllst.
            Erinnerst du dich noch an das vorherige Modul?"""]


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
            return [f"""Du hast bei {moduleName} nicht alles richtig beantwortet 😬 .
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

    def inform_all_finished(self, all_finished):
        return["""Du hast alle Module abgeschlossen, sehr gut! Vergiss nicht, jede Woche einige Quizzes zu wiederholen!"""]

    def inform_first_module(self, moduleName):
        return[f"""Das erste ist {moduleName}"""]

    def request_learning_time(self, learningTime):
        return["""Wie viel Zeit hast du heute, um etwas zu lernen (bitte gib die Zeit in Minuten an)?"""]

    def inform_content(self, modulContent, link):
        if link == 'None':
            return["""Leider konnte ich keine Ergebnisse zu deiner Eingabe finden. Hast du noch eine andere Frage?"""]
        elif link == 'End':
            return["""Das war alles, was ich zu deiner Frage finden konnte. Hast du noch eine andere Frage?"""]

    def request_content(self, modulContent):
        return["""Könntest du mir bitte nochmal nur den Suchbegriff nennen?"""]

    def inform_not_implemented(self, notImplementedYet):
        return[(f"""Leider ist diese Funktionalität noch nicht implementiert, wir arbeiten dran!""", [])]

    def inform_motivational(self, motivational, taskLeft):
        return[f"""{taskLeft}, du hast schon {motivational} geschafft! Die restlichen Inhalte bauen aufeinander auf, und es wird dir leicht fallen, eines nach dem anderen zu bearbeiten ;-)"""]

    def inform_no_motivational(self, NoMotivational, taskLeft):
        return[f"""{taskLeft}, du hast leider {NoMotivational} geschafft 😩  Du könntest jetzt anfangen! Die Inhalte bauen aufeinander auf, und es wird dir leicht fallen, eines nach dem anderen zu bearbeiten ;-)"""]

    def request_past_module(self, pastModule):
        return["""Erinnerst du dich an das vorherige Thema?"""]

    def inform_past_module_repeat(self, pastModule, repeatContent):
        return[f"""Dann wiederhole am besten das vorherige Thema, bevor du mit dem neuen startest: {repeatContent}"""]

    def inform_next_module(self, moduleName, nextModule):
        return[f"""Dein nächstes Thema ist {moduleName}. Möchtest du damit beginnen?"""]

    def inform_moduleName(self, moduleName, hasModule):
        # this is about time constraints (should be in name of function)
        if hasModule:
            return[f"""Dann kannst du das hier lernen: {moduleName}"""]
        return["""Leider habe ich kein Lernmaterial mit dieser Dauer gefunden :-( Versuche es bitte erneut, wenn du ein bisschen mehr Zeit hast"""]

    def inform_fit_for_test(self, fitForTest, link):
        if fitForTest:
            return[f"""Dann zeig mal! {link}"""]
        return[f"""Dann könntest du die Zeit nutzen, um dir die Quizzes dazu anzuschauen und die Inhalte zu wiederholen, bei denen du unsicher bist! {link}"""]

    def inform_repeat_module_affirm(self, repeat_module_affirm, moduleLink):
        # same as before? (without affirm) and changed module_link into moduleLink as scheme before
        return[f"""Alles klar, du findest die Inhalte zum vorherigen Thema hier: {moduleLink}"""]

    def inform_repeat_module_deny(self, repeat_module_deny):
        return["""Alles klar, dann wenn du bereit bist, könntest du mit einem neuen Thema anfangen!"""]

    def inform_new_module_deny(self, new_module_deny):
        return["""Alles klar, dann würde ich dir empfehlen, einige der bereits abgeschlossenen Inhalte zu wiederholen!"""]

    def inform_offer_help(self, offerHelp):
        return["""Dann mach doch nochmal die Quizzes und sag mir, womit du Schwierigkeiten hast."""]

    def inform_repeat_quiz(self, QuizWiederholen, completedModule):
        # german variable QuizWiederholen
        return[f"""Dann könntest du die Zeit nutzen, um die Quizzes zu {completedModule} zu wiederholen!"""]

    def inform_complete_module_affirm(self, complete_Module_affirm):
        return["""Sehr gut! Dann schau kurz nach, welche Aufgaben bei dem Modul noch offen sind, und schließe sie ab ;-)"""]

    def inform_complete_module_deny(self, complete_Module_deny):
        return["""Dann könntest du die Zeit nutzen, um dir die Quizzes dazu anzuschauen und die Inhalte zu wiederholen, bei denen du unsicher bist!"""]

    def request_fit_for_submission(self, fitForSubmission, newTask):
        # name doesnt fit to sentence
        return["""Super! Willst du dann heute neue Einheiten lernen oder abgeschlossene Inhalte wiederholen?"""]

    def request_offer_help(self, offerHelp, time):
        return[f"""Du bist bereits seit {time} Minuten an diesem Quiz dran, brauchst du Hilfe?"""]

    def reqmore(self, moduleContent):
        return["""Brauchst du mehr Informationen zu dem Modul?"""]
    
    def reqmore(self, end):
        # does this make sense (and what is reqmore)
        return["""Super, du kannst mir einfach nochmal schreiben, falls du meine Hilfe brauchst!"""]

    def inform_content_task_required(self, contentTaskRequired):
        # sentence and name doesnt fit
        return["""Ja, aber sie bauen sich aufeinander und es wird dir leicht fallen, ein Thema nach dem anderen zu bearbeiten ;-)"""]

    def inform_offer_help_suggestion(self, suggestion, offerhelp):
        # should the name be without suggestion and simply overload the other function with diff. args
        if suggestion == 'quiz':
            return["""Du solltest die Quizzes gleich nach dem Lernen der Einheit machen, solange die Inhalte bei dir noch frisch sind!"""]
        elif suggestion == 'learningTime':
            return["""Du solltest dir die Zeit fürs Lernen einer Einheit besser einplanen, damit du dich richtig konzentrieren kannst. Dann wirst du dich an die Inhalte besser erinnern und die Fragen richtig beantworten!"""]
        elif suggestion == 'offerHelp':
            return[""""Wenn etwas beim Lernen nicht klar ist, solltest du mir gleich Fragen stellen, dann helfe ich dir gerne! Mach am besten noch nicht die Quizzes, wenn du mit den Inhalten noch nicht komplett vertraut bist!"""]

    def inform_quiz_link(self, link):
        return[f"""Hier ist ein Link zum Quiz: {link}"""]

    def inform_motivate_quiz(self, link):
        return[f""""Wenn du kurz Zeit hast, würde ich dir empfehlen, die Quizzes trotzdem zu wiederholen: das dauert nur wenige Minuten, und du erhöhst die Chance, eine gute Note zu bekommen :-)!<br>{link}"""]

    def inform_next_step(self, nextStep):
        if nextStep == 'newModule':
            return["""Sehr gut! Du kannst jetzt mit dem neuen Thema anfangen :-D!"""]
        elif nextStep == 'repeatConcepts':
            return["""Sehr gut! Willst du noch einige Inhalte wiederholen, bevor du mit dem neuen Thema anfängst?"""]
        elif nextStep == 'repeatContents':
            return["""Sehr gut! Sollen wir ein paar Begriffe durchgehen und du sagst mir, welche du wiederholen möchtest?"""]

    def request_search_term(self):
        return [
            ("""Entschuldige, aber ich habe deinen Suchbegriff leider nicht aus der Nachricht erkannt.
                Kannst du ihn vielleicht direkt eingeben?
             """,
             [])
        ]

    def inform_help(self):
        return[("""Hier ist eine Liste von Themen, wonach du mich fragen kannst:
               <ul>
                <li>Was du als nächstes lernen kannst <br> (z.B. \"Was kann ich als nächstes lernen?\")</li>
                <li>Weitermachen mit einem offenen Abschnitt <br> (z.B. \"Abschnitt fertig machen\")</li>
                <li>Was du wiederholen kannst <br>(z.B. \"Ich will Quizze wiederholen\")</li>
                <li>Welche Badges du als nächstes bekommen kannst <br>(z.B. \"Was sind die Voraussetzungen für den nächsten Badge?\")</li>
                <li>Wie weit du im Kurs bist <br>(z.B. \"Wie viel fehlt noch im Kurs?\")</li>
                <li>Nach Inhalten suchen <br>(z.B. \"Wo finde ich Informationen zu Regression?\")</li>
               </ul>""", [])]

    def generate_welcomemsg(self, sys_act: SysAct):
        if "first_turn" in sys_act.slot_values:
            return self.welcomemsg_first_turn_ever
        else:
            return self.welcomemsg

    def welcomemsg_first_turn_ever(self, first_turn: bool):
        return  [("""Hallo, ich bin der Moodle Assistent!
        Ich kann dir helfen bei:
        <ul>
            <li>Suche nach Inhalten</li>
            <li>Fortschritt überprüfen</li>
            <li>Navigation zu Lehrinhalten</li>
            <li>usw.</li>
        </ul>""", []),
        ("Du kannst auch auf das Zahnrad oben klicken, um meine Einstellungen ändern.", [])]
    
    def welcomemsg(self):
        day_section = ""
        now = datetime.now()
        if now.hour >= 5 and now.hour < 12:
            day_section = "Guten Morgen! Gut ausgeruht?"
        elif now.hour >= 12 and now.hour < 15:
            day_section = "Einen schönen Mittag! Hoffentlich hast du gut gegessen!"
        elif now.hour >= 15 and now.hour < 17:
            day_section = "Einen schönen Nachmittag 😊"
        elif now.hour >= 17 and now.hour < 21:
            day_section = "Guten Abend 😊"
        else:
            day_section = "Wow, du lernst ja noch spät, Respket 😱"

        options = [
            "Schön dich wieder zu sehen 😊",
            "Hi!",
            "Willkommen zurück 😊",
            "Hallo!",
            day_section
        ]
        return [(random.choice(options), [])]



    def inform_unread_messages(self):
        """ Notify about unread forum messages """
        pass

    def inform_deadline_reminder(self):
        """ Remind about upcoming assignments using calendar """
        pass


    def display_quiz(self, quiz_embed):
        if quiz_embed is None:
            return [("Momentan gibt es keine Quizze die wiederholt werden können.", [])]
        return [(f"$$QUIZ;{json.dumps(quiz_embed)}", [])]

    def display_weekly_summary(self, best_weekly_days: List[str], weekly_completions: Dict[str , list], weekly_completions_prev: Dict[str, list]):
        """ 
        Args:
            weekly: If true, show activity of current and last week at end of current week.
                    If false, show total course progress.
            congratulations: If true, add congratulation message """
        total_completions_this_week = int(weekly_completions["y"][-1])
        total_completions_prev_week = None if isinstance(weekly_completions_prev, type(None)) else int(weekly_completions_prev["y"][-1])

        msgs = [(f"""Diese Woche hast du {total_completions_this_week} Inhalt{"e" if total_completions_this_week != 1 else ""} abgeschlossen {"🎉" if total_completions_this_week > 0 else ""}.""", []),
                (f"""$$LINECHART;Diese Woche;{json.dumps(weekly_completions)};Letzte Woche;{json.dumps(weekly_completions_prev)}""", [])]

        if (not isinstance(weekly_completions_prev, type(None))) and total_completions_this_week > total_completions_prev_week:
            msgs.append(("Damit war diese Woche besser als die Vorherige, weiter so 🔥", []))
        else:
            num_best_days = len(best_weekly_days)
            if num_best_days > 0:
                if num_best_days >= 3:
                    msgs.append((f"Du hast sehr konsistent gelernt, an {num_best_days} Tagen!", []))
                else:
                    if num_best_days == 1:
                        msgs.append((f"Dein bester Tag diese Woche war {best_weekly_days[0]}", []))
                    elif num_best_days == 2:
                        msgs.append((f"Deine besten Tage diese Woche waren {best_weekly_days[0]} und {best_weekly_days[1]}", []))
        return msgs

    def _donut_chart(self, titleOuter: str, percentageOuter: float, titleInner: Union[str, None] = None, percentageInner: Union[float, None] = None):
        inner = f""";{titleInner};{100*percentageInner}""" if not isinstance(titleInner, type(None)) else ""
        return f"""$$DONUT;{titleOuter};{100*percentageOuter}{inner}"""

    def _enumeration(self, items: List[str]) -> str:
        return f""" <ul>
                    {" ".join(['<li>' + item + '</li>' for item in items])}
                </ul>"""

    def display_progress(self, percentage_done: float, percentage_repeated_quizzes: float):
        """ Offer choice to either review previous quizes, or continue with one of the next activities"""
        return [("""In letzter Zeit hast du viel Neues gelernt:""", []),
                (self._donut_chart("Kurs", percentage_done, "Wiederholte Quizze", percentage_repeated_quizzes), [])]

    def display_quiz_improvements(self, improvements: List[bool]):
        percentage_improvements = sum(improvements)/len(improvements)
        msgs = []
        if percentage_improvements > 0.0:
            msgs.append((f"Sehr gut, du hast dich in dieser Wiederholung bei {sum(improvements)} Quizzen verbessert!", []))
            msgs.append((self._donut_chart("Quiz Verbesserungen", percentage_improvements), ["Weitere Quizze Wiederholen", "Etwas neues lernen"]))
        else:
            msgs.append((f"Toll dass du {len(improvements)} Quizze nochmal wiederholt hast! Weiter so!", ["Weitere Quizze Wiederholen"]))
        return msgs 

    def display_badge_progress(self, badge_name, percentage_done: float, missing_activities: List[str]):
        if badge_name == None:
            return [("""Du hast bereits alle gerade verfügbaren Auszeichnungen erhalten 🎉
                     Wenn du neue Lerninhalte ansiehst, werden neue Badges verfügbar.""", [])]
        msgs = []
        if percentage_done >= 0.5:
            msgs.append((f"""Du hast fast die Auszeichnung {badge_name} abgeschlossen!""", []))
        else:
            msgs.append((f"""Als nächsten Badge könntest du {badge_name} erhalten!""", []))
        msgs += [(self._donut_chart("Auszeichnungsfortschritt", percentage_done), []),
                (f"""Wenn du noch
                {self._enumeration(items=missing_activities)}

                fertig machst, kriegst du sie 😊""", [])]
        return msgs
    
    def congratulate_badge(self, badge_name: str, badge_img_url: str):
        return [(f"""Du hast gerade die Auszeichnung <b>{badge_name}</b> erhalten:
                <div style="text-align: center; padding: 0.5em;">
                 {badge_img_url}
                </div>""", []),
                ("Stark 💪", [])]
    
    def congratulate_completion(self, name: str, branch: bool):
        if branch:
            return [(f"Herzlichen Glückwunsch! Du hast alle Themen im Zweig {name.upper()} fertig gemacht! 🎉🎉🎉", [])]
        else:
            return [(f"Super! Du hast den Abschnitt {name} abgeschlossen! 🎉", [])]
    
    def inform_last_viewed_course_module(self, last_viewed_course_module):
        return [(f"Letztes Mal hast du {last_viewed_course_module} abgeschlossen.", [])]

    def request_continue_or_next(self, next_available_modules):
        return [(f"""Folgende Abschntitte hast du angefangen, aber noch nicht abgeschlossen:
                {self._enumeration(next_available_modules)}
                
                Klicke eine der Optionen, oder willst du lieber was Anderes lernen?""", [
                    "Weitermachen", "Was Anderes lernen" 
                ])]
    
    def inform_next_options(self, next_available_sections):
        return [(f"""Du könntest mit einem dieser neuen Abschnitte beginnen:
                {self._enumeration(items=next_available_sections)}
                
                Klicke eine der Optionen, oder willst du lieber was Anderes lernen?""", [
                    "Was Anderes lernen"
                ])]
    
    def inform_starter_module(self, module_link: str):
        return [(f"Klicke einfach {module_link} um mit einem Spiel einzusteigen!", [
            "Einstellungen",
            "Loslegen!"
        ])]
    
    def inform_search_results(self, search_results: Dict[str, List[str]], load_more: bool):
        if len(search_results) == 0:
            return [(
                "Tut mir leid, aber es gibt keine (weiteren) Ergebnisse zu dieser Suche 😞"
            , [])]

        links_by_file = []
        for filename in search_results:
            links_by_file.append(
                f"""<div class="card" style="color: black">
                        <div class="card-header">{filename.replace(".pdf", " (Buch)")}</div>
                        <div class="card-body">
                            <ul class="list-group list-group-flush">
                                {" ".join([f'<li class="list-group-item">{res}</li>' for res in search_results[filename]])}
                            </ul>
                        </div>
                    </div>""")
        return [(
            "".join(links_by_file),
            [
                "Mehr Ergebnisse"
            ] if load_more else []
        )]
   
    def feedback_to_quiz(self, success_percentage: float, next_quiz_link: str):
        msgs = []
        if success_percentage >= 99:
            # all questions correct
            msgs.append((f"Super gemacht, du scheinst dieses Thema echt gut zu verstehen 🤓", []))
        elif success_percentage >= 70:
            msgs.append((f"Gut gemacht, du scheinst dieses Thema zu verstehen 🤓", []))
        else:
            msgs.append((f"Toll dass du ein Quiz gemacht hast - bleib dran!", []))
            if random.random() < 0.5:
                msgs.append((f"Denk dran dass du jederzeit Quizze wiederholen kannst, um dein Verständnis zu verbessern!", []))
        if next_quiz_link:
            msgs.append((f"Bereit für das {next_quiz_link}?", []))
        return msgs
    
    def bad_act(self, **kwargs):
        return [("Das habe ich leider nicht verstanden. Kannst du es vielleicht nochmal anders formulieren?", ["Hilfe"])]

    def you_are_welcome(self):
        return [("Gerne 😊", [])]

    def get_message_fn(self, sys_act: SysAct):
        # delegate system act to specific message generator
        if sys_act.type == SysActionType.Welcome:
            return self.generate_welcomemsg(sys_act)
        elif sys_act.type == SysActionType.RequestContinueOrNext:
            return self.request_continue_or_next
        elif sys_act.type == SysActionType.RequestSearchTerm:
            return self.request_search_term
        elif sys_act.type == SysActionType.InformNextOptions:
            return self.inform_next_options
        elif sys_act.type == SysActionType.InformStarterModule:
            return self.inform_starter_module
        elif sys_act.type == SysActionType.InformLastViewedCourseModule:
            return self.inform_last_viewed_course_module
        elif sys_act.type == SysActionType.InformSearchResults:
            return self.inform_search_results
        elif sys_act.type == SysActionType.DisplayWeeklySummary:
            return self.display_weekly_summary
        elif sys_act.type == SysActionType.DisplayProgress:
            return self.display_progress
        elif sys_act.type == SysActionType.DisplayQuiz:
            return self.display_quiz
        elif sys_act.type == SysActionType.DisplayBadgeProgress:
            return self.display_badge_progress
        elif sys_act.type == SysActionType.DisplayQuizImprovements:
            return self.display_quiz_improvements
        elif sys_act.type == SysActionType.CongratulateBadge:
            return self.congratulate_badge
        elif sys_act.type == SysActionType.CongratulateCompletion:
            return self.congratulate_completion
        elif sys_act.type == SysActionType.RequestReviewOrNext:
            return self.request_review_or_next
        elif sys_act.type == SysActionType.FeedbackToQuiz:
            return self.feedback_to_quiz
        elif sys_act.type == SysActionType.Bad:
            return self.bad_act
        elif sys_act.type == SysActionType.YouAreWelecome:
            return self.you_are_welcome
        elif sys_act.type == SysActionType.InformHelp:
            return self.inform_help
        raise NotImplementedError


    @PublishSubscribe(sub_topics=["moodle_event"])
    def moodle_event(self, user_id: int, moodle_event: dict):
        if moodle_event['eventname'].lower().strip() == "\\core\\event\\user_loggedin":
            self.clear_memory(user_id)

    @PublishSubscribe(sub_topics=["sys_acts"], pub_topics=["sys_utterance"])
    def publish_system_utterance(self, user_id: str, sys_acts: List[SysAct] = None) -> dict(sys_utterance=List[str]):
        """Generates the system utterance and publishes it.

        Args:
            sys_act (SysAct): The system act published by the policy

        Returns:
            dict: a dict containing the system utterance
        """
        messages = []
        for sys_act in sys_acts:
            message_fn = self.get_message_fn(sys_act)
            messages += message_fn(**sys_act.slot_values)
        for message in messages:
            self.logger.dialog_turn(f"# USER {user_id} # NLG - {message}")
        
        if len(messages) == 0:
            messages += self.bad_act()
        return {'sys_utterance': messages}

