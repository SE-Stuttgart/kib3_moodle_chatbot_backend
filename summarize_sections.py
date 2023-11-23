import time
import traceback
from elearning.moodledb import Base, MCourseSection, connect_to_moodle_db
from sqlalchemy.orm import sessionmaker
import re
import html
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
for section in session.query(MCourseSection).all():
    if section.is_quiz_section():
        # only look at summaries for content sections, not quiz sections
        continue

    name = section.name
    long_summary_html = section.summary
    textonly_long_summary = html.unescape(re.sub(RE_REMOVE_TAGS, '', long_summary_html)) # remove all HMTL tags, replace escapted tokens like &nbsp;
    
    # debugging output: check that we actually get what we expect :)
    print(f"""========== Section {name} ==========
          {textonly_long_summary}
          """)
    
    # TODO summarize/shorten textonly_long_summary using the ChatGPT API, and save it to a json file with the mapping:
    # section.name -> shortened summary
    # (we can't rely on ID's here, because they will be different across moodle installations)
   
# 3. disconnect
session.close()
    

