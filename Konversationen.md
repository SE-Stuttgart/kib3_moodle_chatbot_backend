<table border = true ; border-collapse= collapse>
  <thead bgcolor=#00688b>
    <tr>
      <th>Anfrage (Bsp.)</th>
      <th>UserAct</th>
      <th>SysAct</th>
      <th>Antwort</th>
      <th>Korrekt</th>
      <th>Edge Cases</th>
      <th>Bemerkung</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Start</td>
      <td>-</td>
      <td>inform(welcomeMsg, daysToSubmission, moduleName); inform(welcomeMsg, daysToSubmission)</td>
      <td>"Hallo, willkommen zu deinem E-Learning-Bot! Willst du neue Einheiten lernen oder alte wiederholen?" oder Antworten mit Kommentar zur nächsten Abgabe</td>
      <td>❓</td>
      <td>3,2,1 Tage?</td>
      <td>Formulierung "zu deinem Bot?" passend? und "Morgen" nur für 1 Tag korrekt</td>
    </tr>
    <tr>
      <th bgcolor=#00688b colspan="7">Suche</th>
    </tr>	
    <tr>
      <td>"Wo finde ich Infos zu Regression?"</td>
      <td>request(infoContent)</td>
      <td>inform(modulContent, link)</td>
      <td>"Gut, dass du fragst! Du kannst hier mehr Informationen finden:" + Aufzählungen mit Links</td>
      <td>✔️</td>
      <td> - Nichts gefunden -> "Leider konnte ich keine Ergebnisse zu deiner Eingabe finden :( Versuche es mal anders auszudrücken!"</td>
      <td>- Wenn context mit gegeben wird dann sieht dieser nicht gut aus! -> Foliennummern besser?
      - Was passiert bei edge anzahl von ergebnissen 0, 1, 2-5, >5 ?
      - schreib fehler(module)</td>
    </tr>
    <tr>
      <td>"Worum geht es?"</td>
      <td>request(content)</td>
      <td>inform(modulContent, link)</td>
      <td>-</td>
      <td>❌</td>
      <td>In welcher Umgebung wird gefragt?!</td>
      <td>In Course site gibt es keine antwort -> in mehreren Umgebungen fragen! wahrscheinlich ersetzt durch request(infoContent) von oben!</td>
    </tr>
    <tr>
      <th bgcolor=#00688b colspan="7">Request</th>
    </tr>
    <tr>
      <td>"Was soll ich machen?"</td>
      <td>request(goal)</td>
      <td>request(goal)</td>
      <td>"Willst du heute neue Inhalte lernen, oder abgeschlossene Inhalte wiederholen?"</td>
      <td>✔️</td>
      <td>-</td>
      <td>-</td>
    </tr>
    <tr>
      <td>"Welche Einheit kann ich wiederholen?"</td>
      <td>request(repeatableModul)</td>
      <td>inform(moduleName, repeatContent, link, contentType)</td>
      <td>"Du hast ... seit einiger Zeit abgeschlossen. Wiederhole dann bitte ... + Link"</td>
      <td>❌</td>
      <td>Verschieden Arten vorschlagen; None link</td>
      <td>- None links!
		      - Line 257: geht dieser inform? anscheinend fehlt contentType
		      - Antwort an Cotent Type angepasst
		      - Wird passender Content vorgeschlagen?</td>
    </tr>
    <tr>
      <td>"Welche Einheit kann ich heute lernen?"</td>
      <td>request(learnableModul)</td>
      <td>request(learningTime)</td>
      <td>"Wie viel Zeit hast du heute, um etwas zu lernen (bitte gib die Zeit in Minuten an)?"</td>
      <td>✔️</td>
      <td>-</td>
      <td>Ähnlichkeit zu request(goal)</td>
    </tr>
    <tr>
      <td>"Wann ist meine nächste Abgabe?"</td>
      <td>request(submission)</td>
      <td>inform(moduleName, submission)</td>
      <td>"Es gibt im Moment keine Abgaben"; "Am {submission} für {moduleName}"</td>
      <td>❓</td>
      <td>Verpasste Abgabe oder keine</td>
      <td>Werden richtige assignments gefunden?</td>
    </tr>
    <tr>
      <td>"Was soll ich noch tun?"</td>
      <td>request(goalAlternative)</td>
      <td>inform(moduleName, finishContent)</td>
      <td>"Du hast die Fragen zu einem Video nicht zu Ende beantwortet. Das könntest du schnell noch erledigen!"</td>
      <td>❓</td>
      <td>Keine open Tasks</td>
      <td>Werden die Tasks richtig rausgesucht?</td>
    </tr>
    <tr>
      <td>"Welche Ziele habe ich?"</td>
      <td>request(toReachGoal)</td>
      <td>inform(moduleName, finishContent)</td>
      <td>"Du hast die Fragen zu einem Video nicht zu Ende beantwortet. Das könntest du schnell noch erledigen!"</td>
      <td>❓</td>
      <td>Keine open Tasks</td>
      <td>Selbe antwort wie oben -> zu einem user act zusammen oder andere bessere antwort geben?</td>
    </tr>
    <tr>
      <td>"Kann ich etwas neues lernen?"</td>
      <td>inform(goal)</td>
      <td>inform(moduleRequirements, moduleName, moduleRequired); inform(all_finished)</td>
      <td>"Alles klar. Es gibt neues Material zu ..., für das du die Voraussetzungen erfüllst. Erinnerst du dich noch an das vorherige Modul?";" Du hast alle Module 		abgeschlossen, sehr gut! Vergiss nicht, jede Woche einige Quizzes zu wiederholen!"</td>
      <td>❓</td>
      <td>Alle Module geschafft</td>
      <td>Bei falscher Reihenfolge (bzw manueller ab-/anwählen) werden falsche Module vorgeschlagen -> wichtig?</td>
    </tr>
    <tr>
      <td>"Wie viele Einheiten fehlen noch?"</td>
      <td>request(finishTask)</td>
      <td>inform(motivational, taskLeft); inform(NoMotivational, taskLeft)</td>
      <td>"43, du hast schon 73 von 116 geschafft! Die restlichen Inhalte bauen aufeinander auf, und es wird dir leicht fallen, eines nach dem anderen zu bearbeiten ;-)"</td>
      <td>❓</td>
      <td>0, alle fertig </td>
      <td>Zwei informs zu einem zusammenfassen!</td>
    </tr>
    <tr>
      <td>"Mit welcher Einheit soll ich anfangen?"</td>
      <td>request(firstGoal)</td>
      <td>inform(moduleName)</td>
      <td>"Das erste ist ...[als Link]"</td>
      <td>❓</td>
      <td>Alle abgeschlossen</td>
      <td>Bei falscher Reihenfolge (bzw manueller ab-/anwählen) werden falsche Module vorgeschlagen -> wichtig?</td>
    </tr>
    <tr>
      <td>"Was mache ich falsch?"</td>
      <td>request(needHelp)</td>
      <td>inform(suggestion, offerhelp)</td>
      <td>"Du solltest die Quizzes gleich nach dem Lernen der Einheit machen, solange die Inhalte bei dir noch frisch sind!"</td>
      <td>✔️</td>
      <td>-</td>
      <td>-</td>
    </tr>
    <tr>
      <td>"Bei welcher Einheit bin ich nicht ausreichend?"</td>
      <td>request(insufficient)</td>
      <td>request(quiz_link, module, insufficient)</td>
      <td>"Bei {module} hast du leider noch nicht ausreichend Punkte 🙁 Möchtest du die Quizzes dazu wiederholen?"</td>
      <td>❓</td>
      <td>Keine/alle gemacht</td>
      <td>Bei der Frage wird mit ja oder nein geantwortet -> klappt das?; passt die antwort zu den Punkten?</td>
    </tr>
    <tr>
      <td>-</td>
      <td>inform/request(quiz_link)</td>
      <td>template inform(quiz_link); template inform(motivateForQuiz, quiz_link)</td>
      <td>"Hier ist ein Link zum Quiz: {quiz_link}"</td>
      <td>❓</td>
      <td>-</td>
      <td>Wie genau wird das erreicht? (vllt nlu.py) Wir zum Beispiel bei request(insufficient) (oben) und dann ja getriggert</td>
    </tr>
	<tr>
      <td>"Sind sie alle verpflichtend?"</td>
      <td>request(dueContent)</td>
      <td>inform(contentTaskRequired)</td>
      <td>"Ja, aber sie bauen sich aufeinander und es wird dir leicht fallen, ein Thema nach dem anderen zu bearbeiten ;-)"</td>
      <td>❌</td>
      <td></td>
      <td>Was genau ist hiermit gemeint? Sie = alle Module/Quizzes?</td>
    </tr>
	<tr>
      <td>"Wie kann ich ein Quiz zum vorherigen Modul finden?"</td>
      <td>request(pastModule)</td>
      <td>inform(repeat_module_affirm, module_link)</td>
      <td>"Alles klar, du findest die Inhalte zum vorherigen Thema hier: + Link"</td>
      <td>❌</td>
      <td>Quiz schon bearbeitet; Quiz existiert nicht</td>
      <td>Es werden nicht spezifisch Quizze vorgeschlagen! Falsch bei falscher Reihenfolge</td>
    </tr>
    <tr>
      <th bgcolor=#00688b colspan="7">Inform</th>
    </tr>
    <tr>
      <td>"Ich habe ... Minuten Zeit"</td>
      <td>inform(learningTime)</td>
      <td>inform(moduleName, hasModule)</td>
      <td>"Leider habe ich kein Lernmaterial mit dieser Dauer gefunden :-( Versuche es bitte erneut, wenn du ein bisschen mehr Zeit hast"; "Dann kannst du das hier lernen"</td>
      <td>❓</td>
      <td>Gibt es den Fall bad, Verschiedene Zeiten(0,  -1, 10000)</td>
      <td>act type bad falls keine regex nichts zurück gibt (line 366)
		      ; Zu testen: Edge Cases + werden richtige Module gewählt</td>
    </tr>
    <tr>
      <td>"Ich bin mit der Einheit fertig"</td>
      <td>inform(finishedGoal)</td>
      <td>inform(positiveFeedback, test), inform(positiveFeedback, repeatQuiz)</td>
      <td>"Cool! Ich kann dir helfen, das Gelernte zu überprüfen. Wenn du bereit bist, stelle ich dir Fragen dazu."; "Cool! Du könntest die Quizzes regelmäßig wiederholen, damit du die Inhalte bis zur Prüfung nicht vergisst!"</td>
      <td>✔️</td>
      <td>-</td>
      <td>Ist hier die Aussage "stelle dir Fragen dazu" korrekt?; Besser nächste Einheit finden/vorschlagen</td>
    </tr>
	<tr>
      <td>"Ich will etwas wiederholen"</td>
      <td>inform(goal)</td>
      <td>inform(moduleName, repeatContent, link, contentType)</td>
      <td>"Du hast Quizzes zum Thema ... seit einiger Zeit nicht mehr angeklickt. Du könntest die Inhalte nochmal auffrischen, ansonsten vergiss du sie! + Link"</td>
      <td>❓</td>
      <td>Nichts zu wiederholen</td>
      <td>Bei falscher Reihenfolge (bzw manueller ab-/anwählen) werden falsche Module vorgeschlagen -> wichtig?</td>
    </tr>
    <tr>
      <td>"Ich bin fertig"</td>
      <td>inform(finishTask)</td>
      <td>inform(nextStep)</td>
      <td>"Sehr gut! Du kannst jetzt mit dem neuen Thema anfangen :-D!"; Antworten zu wiederholen</td>
      <td>❌</td>
      <td>Komplett fertig</td>
      <td>zufälliges Auswählen ob wiederholen oder neues sinnvoll?; Sollen wir ein paar Begriffe durchgehen und du sagst mir, welche du wiederholen möchtest? -> geht das?;  Ähnlich zu "nextModule"</td>
    </tr>
    <tr>
      <td>"Was kann ich als nächstes lernen?"</td>
      <td>request(nextModule)</td>
      <td>inform(moduleName, nextModule)</td>
      <td>"Dein nächstes Thema ist ...[als Link]. Möchtest du damit beginnen?"</td>
      <td>❓</td>
      <td>Alle abgeschlossen</td>
      <td>Bei falscher Reihenfolge (bzw manueller ab-/anwählen) werden falsche Module vorgeschlagen -> wichtig?</td>
    </tr>
    <tr>
      <th bgcolor=#00688b colspan="7">General</th>
    </tr>
    <tr>
      <td>"danke"</td>
      <td>Thanks</td>
      <td>reqmore(moduleContent)</td>
      <td>"Brauchst du mehr Informationen zu dem Modul?"</td>
      <td>❓</td>
      <td></td>
      <td>Vllt "Bitte davor" -> was passiert bei folge fragen?</td>
    </tr>
    <tr>
      <td>Antwort mit "Ja"</td>
      <td>RequestMore</td>
      <td>reqmore(end); inform(all_finished);inform(moduleRequirements, moduleName, moduleRequired)</td>
      <td>"Super, du kannst mir einfach nochmal schreiben, falls du meine Hilfe brauchst!"</td>
      <td>❓</td>
      <td></td>
      <td>Sollte hier nicht irgendwas als antwort kommen? Wann wird was aufgerufen?</td>
    </tr>
	<tr>
      <td>"nein"</td>
      <td>Deny</td>
      <td>-</td>
      <td>-</td>
      <td>❌</td>
      <td></td>
      <td>Erkennt es als bad. Funktioniert in "Nähe" von anderen (antwort auf sysact 2 weiter oben)</td>
    </tr>
	<tr>
      <td>"tschüss"</td>
      <td>Bye</td>
      <td>Bye</td>
      <td>"Danke schön, bis zum nächsten Mal."</td>
      <td>✔️</td>
      <td>-</td>
      <td>-</td>
    </tr>
    <tr>
      <td>"Hilfe"</td>
      <td>request(help)</td>
      <td>inform(help)</td>
      <td>"Du kommst nicht weiter? Kein Problem! Hier ist eine Liste von Themen, wonach du mich fragen kannst: -   Was du als nächstes lernen solltest  (z.B. "Was kann ich als nächstes lernen?")-   Was du wiederholen kannst  
    (z.B. "Bei welchem Modul bin ich nicht ausreichend?")"</td>
      <td>✔️</td>
      <td>-</td>
      <td>-</td>
    </tr>
    <tr>
      <th bgcolor=#00688b colspan="7">Nicht implementiert</th>
    </tr>
    <tr>
      <td>-</td>
      <td>request(moduleRequired) (existiert aber nicht)</td>
      <td>inform(positiveFeedback,newModule); inform(pastModule, repeatContent)</td>
      <td>"Sehr gut! Du kannst jetzt mit dem neuen Thema anfangen :-D: {newModule}"; "Dann wiederhole am besten das vorherige Thema, bevor du mit dem neuen startest: {repeatContent}"</td>
      <td>❌</td>
      <td>-</td>
      <td>Keine ensprechender UserAct; vllt anderer Trigger?</td>
    </tr>
    <tr>
      <td>-</td>
      <td>...(finishGoal) (existiert aber nicht)</td>
      <td>inform(positiveFeedback, repeatQuiz)</td>
      <td>""Cool! Du könntest die Quizzes regelmäßig wiederholen, damit du die Inhalte bis zur Prüfung nicht vergisst!""</td>
      <td>❌</td>
      <td>-</td>
      <td>SysAct wird bei inform(finishedGoal) benutzt -> das hier überflüssig</td>
    </tr>
    <tr>
      <td>"Anfrage"</td>
      <td>UserAct</td>
      <td>SysAct</td>
      <td>"Antwort"</td>
      <td>Korrekt</td>
      <td>Edge Cases</td>
      <td>Bemerkung</td>
    </tr>
  </tbody>
</table>


korrekt: ✔️
noch nicht getestet: ❓
Fehler: ❌

