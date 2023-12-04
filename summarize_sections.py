import time
import traceback
from elearning.moodledb import Base, MCourseSection, connect_to_moodle_db
from sqlalchemy.orm import sessionmaker
import re
import html
from dotenv import load_dotenv
from openai import OpenAI
import json

# 1. Connect to DB
session = None
def _init_db():
    global session
    success = False
    while not success:
        try:
            engine, conn = connect_to_moodle_db()
            Session = sessionmaker()
            Session.configure(bind=engine)
            session = Session()
            Base.metadata.create_all(engine)
            success = True
            print("====== SUCCESS ======")
        except:
            print("===== ERROR CONNECTING TO DB (Potentially have to wait for moodle setup to finish), RETRY IN 10 SECONDS ===== ")
            traceback.print_exc()
            time.sleep(10)
_init_db()

# 2. Loop over all sections, shortening their (long form) summaries

RE_REMOVE_TAGS = re.compile('<.*?>') # summaries are in HTML format - remoe the tags to get only user-readable text

# Load environment variables from .env file
load_dotenv()
client = OpenAI()
# json file with the mapping: section.name -> shortened summary
# create json file if it doesn't exist yet

data = {}

for i, section in enumerate(session.query(MCourseSection).all()):
    if section.is_quiz_section():
        # only look at summaries for content sections, not quiz sections
        continue

    name = section.name
    long_summary_html = section.summary
    textonly_long_summary = html.unescape(re.sub(RE_REMOVE_TAGS, '', long_summary_html)) # remove all HMTL tags, replace escapted tokens like &nbsp;
    
    # debugging output: check that we actually get what we expect :)
    #print(f"""========== Section {name} ==========
    #      {textonly_long_summary}
    #      """)
    
    # summarize textonly_long_summary using the ChatGPT API
    # (we can't rely on ID's here, because they will be different across moodle installations)
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Du bist ein Lehrer und hilfst eine Texte zu schreiben. Der Text soll kurz sein, aber trotzdem alle wichtigen Informationen enthalten."},
            {"role": "user", "content": "Fasse den Abschnitt " + name + " kurz zusammen: " + textonly_long_summary}
        ]
    )
    
    #print(f"""========== Section {name} ==========
    #{textonly_long_summary}
    #""")
    #print(completion.choices[0].message.content)
        
    data[name] = completion.choices[0].message.content
print(len(data))
# save data to a json file with the mapping:
# section.name -> shortened summary
with open('summarized.json', 'w') as outfile:
    json.dump(data, outfile, indent=4)
print(len(data))
        
        

   
# 3. disconnect
session.close()
    

