from collections import defaultdict
import json
import logging
import traceback
from typing import Dict, List, Tuple
import httplib2
import urllib
import config


def get_book_links(webserviceuserid: int, wstoken: str, course_id: int, searchTerm: str, word_context_length: int = 3, start=-1, end=-1) -> Tuple[Dict[str, List[str]], bool]:
    """
    Args:
        word_context_length: how many words before and after the search term should be included in search result
    """
    http_client = httplib2.Http(".cache")
    body={
            "wstoken": wstoken,
            "wsfunction": "block_slidefinder_get_searched_locations",
            "moodlewsrestformat": "json",
            "searchstring": searchTerm,
            "courseid": course_id,
            "contextlength": word_context_length,
            "userid": webserviceuserid
    }
    try:
        response = http_client.request(f"{config.MOOLDE_SERVER_PROTOCOL}://{config.MOODLE_SERVER_WEB_HOST}/webservice/rest/server.php",
            method="POST",
            headers={'Content-type': 'application/x-www-form-urlencoded'},
            body=urllib.parse.urlencode(body))[1] # result is binary string with escaped quotes -> decode
        print("response: ", response)
        start_pos = response.find(b"[")
        end_pos = response.rfind(b"]")

        # Extract the JSON part
        json_part = response[start_pos:end_pos + 1]

        # Decode the JSON part and parse it

        data = json.loads(json_part.decode('unicode_escape').strip('"').replace('\/', '/'))
        
        """
        Example entry in data (list):
        {'Filename': 'Das Koordinatensystem', 'PDF Pagenum': 1, 'Url': 'http://193.196.53.252:80/mod/book/view.php?id=19&chapterid=34', 'Matched String': 'Koordinatensystem', 'Context': '... das Koordinatensystem was ist wo?foto ...'}
        """
        
        """
        {'book_chapter_url': 'http://localhost:8081/mod/book/view.php?id=15&chapterid=1',
            'context_snippet': '... Lizenzhinweise auf der letzten SeiteRegressionZahlen '
                                'vorhersagenFoto:Mika BaumeisteraufUnsplash ...',
            'filename': 'Regression.pdf',
            'page_number': 1},
        """
        files = defaultdict(lambda: [])
        counter = 0
        has_more_results = len(data) >= end if end > 0 else False

        # bundle the results by filename (filename and the context snippets)
        for entry in data:
            if counter < 0 or start <= counter < end:
                files[entry['filename']].append(
                    f"""<a href="{entry['book_chapter_url']}" style="color: black">{entry['context_snippet']}</a>"""
                )
            counter += 1
        return files, has_more_results
    except:
        logging.getLogger("error_log").error(traceback.format_exc())
        return {"FEHLER": ["Fehler bei der Suche"]}, False

if __name__ == "__main__":
    # connect to database
    for result in get_book_links("testtoken", course_id=4, searchTerm="Koordinatensystem", word_context_length=3):
        print(result)
    