from services.nlu.nlu import ELearningNLU

test_sentences = [
    "Wo finde ich Streudiagramme",
    "Wo finde ich was zu Streudiagrammen",
    "Wo finde ich Informationen zu Streudiagrammen",
    "Ich suche Informationen zu Streudiagrammen",
    "Zeig mir Inhalte zu Streudiagrammen",
    "definiere Streudiagramm",
    "Definition von Streudiagrammen",
    "Was sind Streudiagramme",
    "Was ist mit Streudiagrammen gemeint",
    "Wo kann ich Streudiagramme finden",
    "Wo kann ich Infos zu Streudiagrammen finden",
    "Wo kann ich Infos über Streudiagramme finden",
    # "Welche Inhalte über Streudiagramme gibt es",
]

nlu = ELearningNLU("")
nlu.set_state(0, ELearningNLU.LAST_ACT,  [])
for sentence in test_sentences:
    print(nlu.extract_user_acts(0, sentence))