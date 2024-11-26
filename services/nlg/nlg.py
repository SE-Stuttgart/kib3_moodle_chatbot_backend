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

import random
import json
import re
from datetime import datetime

from services.service import PublishSubscribe
from services.service import Service
from utils.domain.domain import Domain
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
    def __init__(self, domain: Domain, template_file: str = None, sub_topic_domains: Dict[str, str] = {}):
        """Constructor mainly extracts methods and rules from the template file"""
        Service.__init__(self, domain=domain, sub_topic_domains=sub_topic_domains)

    ###
    ### Helper functions
    ###
    def join_values(self, values: List[str], interior_join: str = ", ", final_join: str="oder"):
        return f"{interior_join.join(values[:-1])} {final_join} {values[-1]}"
    
    def _template_genitive_s_german(self, name: str) -> str:
        if name[-1] in ('s', 'x', 'ß', 'z'):
            return f"{name}'"
        else:
            return f"{name}s"
        
    def _enumeration(self, items: List[str]) -> str:
        return f""" <ul>
                    {" ".join(['<li>' + item + '</li>' for item in items])}
                </ul>"""

    def to_href(self, url: str, displaytext: str) -> str:
        return f"""<a href="{url}">{displaytext}</a>"""
    
    def to_pdf_popup(self, url: str, displaytext: str) -> str:
        return f'<button class="block-chatbot-content-link" data-toggle="modal" data-target="#block_chatbot_coursemoduleview" data-src="{url}" data-displaytext="{displaytext}">{displaytext}</button>'

    def to_content_link(self, url: str, displaytext: str, typename: str, **kwargs) -> str:
        if typename == "resource":
            return self.to_pdf_popup(url=url, displaytext=displaytext)
        else:
            return self.to_href(url=url, displaytext=displaytext)

    ###
    ### Templates
    ###

    # TODO is insufficient = 'none' a string, or of type(None)?
    def request_repeat_quiz(self, user_id, quiz_link, module, insufficient):
        if insufficient == True:
            return [f"""Bei {module} hast du leider noch nicht ausreichend Punkte 🙁.
                    Möchtest du die Quizze dazu wiederholen?"""]
        elif insufficient == False:
            return [f""""Du hast überall ausreichend Punkte erzielt, gut gemacht!
                    Möchtest du einige Quizze wiederholen, um die Inhalte aufzufrischen?"""]
        elif insufficient == "none":
            return ["""Frag mich nochmal, wenn du ein Quiz abgeschlossen hast 😁"""]

    def request_review_or_next(self, user_id):
        msgs = []
        if random.random() < 0.4:
            msgs.append((f"""Regelmäßiges Wiederholen von Lerninhalten führt dazu, dass du dich besser an die Inhalte erinnern kannst.""", []))
        msgs.append(random.choice([
            ("Willst du dir etwas Zeit nehmen, um die Inhalte zu wiederholen?", ["Wiederholen", "Weitermachen"]),
            ("Möchtest du dein Wissen nochmal testen?", ["Wiederholen", "Weitermachen"]),
            ("Wie wäre eine kleine Quiz-Runde, um deine Erinnerung aufzufrischen?", ["Wiederholen", "Weitermachen"])
        ]))
        return msgs
        
    def inform_not_implemented(self, user_id, notImplementedYet):
        return[(f"""Leider ist diese Funktionalität noch nicht implementiert, wir arbeiten dran!""", [])]

    def request_search_term(self, user_id):
        return [random.choice([
            ("""Entschuldige, aber ich habe deinen Suchbegriff leider nicht erkannt.
                Kannst du ihn vielleicht direkt eingeben (ohne zusätzlichen Text)?
            """, []),
            ("""Leider habe ich nicht verstanden, wonach du suchst."
                Könntest du bitte nur den Suchbegriff eingeben?""", []),
            ("""Könntest du bitte nur den Suchbegriff nochmals eingeben?
                Ich habe ihn leider nicht aus der Anfrage erkennen können.""", []),
        ]) ]

    def inform_help(self, user_id):
        return[("""Hier ist eine Liste von Dingen, nach denen du mich fragen kannst:
               <ul>
                <li><b>Was du als nächstes lernen kannst </b><br> (z.B. \"Was kann ich als nächstes lernen?\")</li>
                <li><b>Weitermachen mit einem offenen Abschnitt </b><br> (z.B. \"Abschnitt fertig machen\")</li>
                <li><b>Was du wiederholen willst </b><br>(z.B. \"Ich will Quizze wiederholen\")</li>
                <li><b>Welche Badges du als nächstes bekommen kannst </b><br>(z.B. \"Was sind die Voraussetzungen für den nächsten Badge?\")</li>
                <li><b>Wie weit du im Kurs bist </b><br>(z.B. \"Wie viel fehlt noch im Kurs?\")</li>
                <li><b>Nach Inhalten suchen </b><br>(z.B. \"Wo finde ich Informationen zu Regression?\")</li>
               </ul>""", [])]

    def generate_welcomemsg(self, sys_act: SysAct):
        if "first_turn" in sys_act.slot_values:
            return self.welcomemsg_first_turn_ever
        else:
            return self.welcomemsg

    def welcomemsg_first_turn_ever(self, user_id, first_turn: bool):
        return  [("""Hallo, ich bin Kibi, der Moodle Assistent!<br>
                Ich kann dir zum Beispiel helfen, Inhalte zu suchen, dich durch den Kurs leiten, oder dir Quizze zum üben geben.
                Klicke auf das Fragezeichen, wenn du wissen willst, wobei ich dich genau unterstützen kann.
                Falls Du meine Einstellungen ändern willst, klicke auf das Zahnrad.
                <br><br>
                <b>Achtung, ich bin kein ChatGPT</b>: ich kann leider keine richtigen Unterhaltungen führen oder inhaltliche Fragen beantworten - ich kann Dir nur zeigen, wo Du Antworten findest.""", [])
        ]
    
    def welcomemsg(self, user_id):
        day_section = ""
        now = datetime.now()
        username = self.get_state(user_id, "USERNAME")
        if now.hour >= 5 and now.hour < 12:
            day_section = f"Guten Morgen, {username}! Gut ausgeruht?"
        elif now.hour >= 12 and now.hour < 15:
            day_section = f"Einen schönen Mittag dir, {username}! Hoffentlich hast du gut gegessen!"
        elif now.hour >= 15 and now.hour < 17:
            day_section = f"Einen schönen Nachmittag dir, {username} 😊"
        elif now.hour >= 17 and now.hour < 21:
            day_section = f"Guten Abend, {username} 😊"
        else:
            day_section = f"Wow {username}, du lernst ja noch spät! Respekt 😱"

        options = [
            f"Schön dich wieder zu sehen, {username} 😊",
            f"Hi {username}!",
            f"Willkommen zurück, {username} 😊",
            f"Hallo {username}!",
            day_section
        ]
        return [(random.choice(options), [])]


    def inform_unread_messages(self, user_id):
        """ Notify about unread forum messages """
        pass

    def inform_deadline_reminder(self):
        """ Remind about upcoming assignments using calendar """
        pass


    def display_quiz(self, user_id, quiz_embed):
        if quiz_embed is None:
            return [random.choice([
                ("Momentan gibt es keine Quizze, die wiederholt werden können.", []),
                ("""Du hast noch keine Quizze gemacht.
                    Ich lasse dich gerne wiederholen, sobald sich das ändert!""", []),
                ("Frage mich einfach nochmal, sobald du ein Quiz gemacht hast 🙂", []),
            ])]
        return [(f"$$QUIZ;{json.dumps(quiz_embed)}", [])]

    def display_weekly_summary(self, user_id, best_weekly_days: List[str], weekly_completions: Dict[str , list], weekly_completions_prev: Dict[str, list]):
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
            msgs.append(("Damit war diese Woche besser als die vorherige, weiter so 🔥", []))
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

    def display_progress(self, user_id, percentage_done: float, percentage_repeated_quizzes: float):
        """ Offer choice to either review previous quizes, or continue with one of the next activities"""
        return [random.choice([
                    ("""So sieht dein aktueller Stand aus:""", []),
                    ("""Sieh mal, wie viel du gelernt hast:""", []),
                    ("""Ich zeige dir mal, wie weit du bist:""", [])
                ]),
                (self._donut_chart("Kurs", percentage_done, "Wiederholte Quizze", percentage_repeated_quizzes), [])
            ]

    def display_quiz_improvements(self, user_id, improvements: List[bool]):
        percentage_improvements = sum(improvements)/len(improvements)
        msgs = []
        if percentage_improvements > 0.0:
            num_quizzes = sum(improvements)
            counter = "einem Quiz" if num_quizzes == 1 else f"{sum(improvements)} Quizzen"
            msgs.append((self._donut_chart("Quiz Verbesserungen", percentage_improvements), []))
            msgs.append(random.choice([
                (f"Sehr gut, du hast dich in dieser Runde bei {counter} verbessert!", ["Weitere Quizze Wiederholen", "Etwas Neues lernen"]),
                (f"Wow, du hast dich diesmal bei {counter} verbessert!", ["Weitere Quizze Wiederholen", "Etwas Neues lernen"]),
                (f"Super, bei {counter} hast du dich gerade verbessert!", ["Weitere Quizze Wiederholen", "Etwas Neues lernen"]),
            ]))
        else:
            num_quizzes = len(improvements)
            counter = "ein weiteres Quiz" if num_quizzes == 1 else f"{len(improvements)} Quizze"
            msgs.append(random.choice([
                (f"Toll, dass du {counter} nochmal wiederholt hast! Weiter so!", ["Weitere Quizze Wiederholen"]),
                (f"Du hast {counter} wiederholt - du bist auf dem richtigen Weg.", ["Weitere Quizze Wiederholen"]),
                (f"{counter} wiederholt - wenn du so weiter machst, bist du gut für die Prüfung vorbereitet!", ["Weitere Quizze wiederholen"])
            ]))
        return msgs 

    def display_badge_progress(self, user_id, badge_name, percentage_done: float, missing_activities: List[Dict[str, str]]):
        if badge_name == None:
            return [random.choice([
                        ("""Du hast bereits alle gerade verfügbaren Auszeichnungen erhalten 🎉
                            Wenn du neue Lerninhalte ansiehst, werden neue Badges verfügbar.""", []),
                        ("""Du hast so gut gearbeitet, dass du schon alle verfügbaren Auszeichnungen erhalten hast 🎉
                        Sieh dir neue Themen an, um weitere freizuschalten.""", []),
                        ("""Alle gerade verfügbaren Auszeichnungen hast du schon gesammelt 🎉
                            Um mehr bekommen zu können, musst du nur mit einem neuen Thema beginnen.""", []),
                ])]
        msgs = []
        if percentage_done >= 0.5:
            msgs.append(random.choice([
                (f"""Du hast fast die Auszeichnung {badge_name} abgeschlossen!""", []),
                (f"""Du bist ganz nah dran, die Auszeichnung {badge_name} zu bekommen!""", []),
                (f"""Mach noch ein kleines bisschen weiter, und du kannst den Badge {badge_name} bekommen!""", []),
            ]))
        else:
            msgs.append(random.choice([
                (f"""Als nächsten Badge könntest du {badge_name} erhalten.""", []),
                (f"""Als nächste Auszeichnung könntest du {badge_name} bekommen.""", []),
                (f"""{badge_name} ist der nächste Erfolg für dich.""", []),
            ]))
        noun = "die Auszeichnung" if "Auszeichnung" in msgs[0][0] else "den Badge"
        msgs += [(self._donut_chart("Auszeichnungsfortschritt", percentage_done), []),
                (f"""Wenn du noch
                {self._enumeration(items=[self.to_content_link(**activtity_link_info) for activtity_link_info in missing_activities])}

                fertig machst, kriegst du {noun} 😊""", [])]
        return msgs
    
    def congratulate_badge(self, user_id, badge_name: str, badge_img_url: str):
        return [(f"""Du hast gerade die Auszeichnung <b>{badge_name}</b> erhalten:
                <div style="text-align: center; padding: 0.5em;">
                 {badge_img_url}
                </div>""", []),
                ("Stark 💪", [])]
    
    def congratulate_completion(self, user_id, name: str, branch: bool):
        if branch:
            return [(f"Herzlichen Glückwunsch! Du hast alle Themen im Zweig {name.upper()} fertig gemacht! 🎉🎉🎉", [])]
        else:
            return [random.choice([
                (f"Super, du hast den Abschnitt {name} abgeschlossen! 🎉", []),
                (f"Tolle Leistung, du bist gerade mit Abschnitt '{name}' fertig geworden! 🎉", []),
                (f"Herzlichen Glückwunsch, du hast den Abschnitt {name} abgeschlossen! 🎉", []),
            ])]
    
    def inform_last_viewed_course_module(self, user_id, last_viewed_course_module: Dict[str, str]):
        last_viewed_course_module_link = self.to_content_link(**last_viewed_course_module)
        return [random.choice([
                    (f"Letztes Mal hast du {last_viewed_course_module_link} angesehen.", []),
                    (f"{last_viewed_course_module_link} war der letzte Inhalt, den du angeschaut hast.", []),
                    (f"Beim letzten Mal hast du hier aufgehört: {last_viewed_course_module_link}.", []),
                ])]
    
    def _vertical_stack(self, items: List[str]) -> str:
        return f"""<div class="flex-column">
                    {" ".join(items)}
                </div>"""

    def request_continue_or_next(self, user_id, next_available_modules: List[Dict[str, str]]):
        cards = []
        for module in next_available_modules:
            cards.append(self.to_card(header=f"{module['topic']} - {module['sectionname']}", body=self.to_content_link(**module)))

        return [(f"""Folgende Abschnitte hast du angefangen, aber noch nicht abgeschlossen:
                {self._vertical_stack(cards)}
                
                Klicke eine der Optionen, oder willst du lieber etwas anderes lernen?""", [
                    "Etwas anderes lernen" 
                ])]
    
    def _get_url(self, html_link_element: str):
        url_pattern = re.compile(r'<a\s+.*?href=["\'](.*?)["\'].*?>')
        match = url_pattern.search(html_link_element)
        url = match.group(1)
        return url

    def inform_next_options(self, user_id, next_available_sections, has_more: bool):
        if len(next_available_sections) == 0:
            return [(f"""Du hast bereits alle Abschnitte abgeschlossen! 🎉🎉🎉""", [])]
        
        cards = []
        for module in next_available_sections:
            cards.append(self.to_card(header=f"{module['topic']} - {module['sectionname']}", body=self.to_content_link(**module)))
        
        text = f"""Du könntest mit einem dieser neuen Abschnitte beginnen:
                {self._vertical_stack(cards)}"""
        if has_more:
            text += "\nKlicke eine der Optionen, oder willst du lieber etwas anderes lernen?"
        else:
            text += "\nWähle einfach eine der Optionen aus."

        answer_options = []
        if has_more:
            answer_options.append("Etwas anderes lernen")

        return [(text, answer_options)]
    
    def inform_starter_module(self, user_id, module_link: str):
        return [(f"Klicke einfach {module_link}, um direkt einzusteigen!", [
            "Einstellungen",
        ])]
    
    def to_card(self, header: str, body: str) -> str:
        return f"""<div class="card" style="color: black">
                        <div class="card-header">{header}</div>
                        <div class="card-body">
                            {body}
                        </div>
                    </div>"""

    
    def inform_search_results(self, user_id, search_results: Dict[str, List[str]], load_more: bool):
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
   

    def feedback_to_quiz(self, user_id, success_percentage: float, url: str, displaytext: str, typename: str, **kwargs):
        msgs = []
        if success_percentage >= 99:
            # all questions correct
            msgs.append(random.choice([
                (f"Super gemacht, du scheinst dieses Thema echt gut zu verstehen 🤓", []),
                (f"Sehr gut! Dieses Quiz war ja fast zu leicht für dich 😉", []),
                (f"Beeindruckend!", []),
            ]))
        elif success_percentage >= 70:
            msgs.append(random.choice([
                (f"Gut gemacht, du scheinst dieses Thema zu verstehen 🤓", []),
                (f"Nicht schlecht!", []),
                (f"{success_percentage}% - nicht übel!", []),
            ]))
        else:
            msgs.append(random.choice([
                (f"Toll, dass du ein Quiz gemacht hast - bleib dran!", []),
                (f"Super, ein weiteres Quiz abgeschlossen! Jeder Versuch bereitet dich besser auf die Prüfung vor.", []),
            ]))
            if random.random() < 0.5:
                msgs.append((f"Denk dran, dass du jederzeit Quizze wiederholen kannst, um dein Verständnis zu verbessern!", []))
        if url:
            msgs.append((f"Bereit für das {self.to_href(url=url, displaytext=displaytext)}?", []))
        return msgs
    
    def bad_act(self, **kwargs):
        return [random.choice([
            ("Das habe ich leider nicht verstanden. Kannst du es vielleicht nochmal anders formulieren?", ["Hilfe"]),
            ("Leider habe ich das nicht verstanden. Willst du es mit einer anderen Formulierung probieren?", ["Hilfe"]),
            ("Tut mir leid, das konnte ich nicht verstehen. Vielleicht kann ich dir besser helfen, wenn du deine Eingabe nochmal umformulierst.", ["Hilfe"]),
        ])]

    def you_are_welcome(self, user_id):
        return [("Gerne 😊", [])]

    def get_message_fn(self, sys_act: SysAct):
        # delegate system act to specific message generator
        if sys_act.type == SysActionType.Welcome:
            return self.generate_welcomemsg(sys_act=sys_act)
        elif sys_act.type == SysActionType.RequestContinueOrNext:
            return self.request_continue_or_next
        elif sys_act.type == SysActionType.RequestSearchTerm:
            return self.request_search_term
        elif sys_act.type == SysActionType.InformNextOptions:
            return self.inform_next_options
        elif sys_act.type == SysActionType.InformStarterModule:
            # skip message, if no more modules are available
            if sys_act.slot_values['module_link'] != None:
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
            messages += message_fn(user_id=user_id, **sys_act.slot_values)
        
        if len(messages) == 0:
            messages += self.bad_act()
        return {'sys_utterance': messages}

