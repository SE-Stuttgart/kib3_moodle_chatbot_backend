from collections import defaultdict
import json
import logging
import traceback
from typing import Dict, List, Tuple
import config
import requests

sess = requests.Session()
BOOKSEARCH_ENDPOINT = f"{config.MOOLDE_SERVER_PROTOCOL}://{config.MOODLE_SERVER_WEB_HOST}/webservice/rest/server.php"

# if config.MOOLDE_SERVER_PROTOCOL == "https":
    # TODO add certificate
    # http_client.add_certificate(key=config.SSL_PRIVATE_KEY_FILE, cert=config.SSL_CERT_FILE, domain=#TODO)

def get_book_links(webserviceuserid: int, wstoken: str, course_id: int, searchTerm: str, word_context_length: int = 3, start=-1, end=-1) -> Tuple[Dict[str, List[str]], bool]:
    """
    Args:
        word_context_length: how many words before and after the search term should be included in search result
    """
    try:
        body={
            "wstoken": wstoken,
            "wsfunction": "block_booksearch_get_searched_locations",
            "moodlewsrestformat": "json",
            "searchstring": searchTerm,
            "courseid": course_id,
            "contextlength": word_context_length,
            "userid": webserviceuserid
        }
        response = sess.post(url=BOOKSEARCH_ENDPOINT, data=body, verify=False)
        data = json.loads(response.json())
   
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
            if end < 0 or start <= counter < end:
                context = entry['context_snippet']
                if len(context) == 0:
                    context = searchTerm
                files[entry['filename']].append(
                    f"""<a href="{entry['book_chapter_url']}" style="color: black">{context}</a>"""
                )
            counter += 1
        return files, has_more_results
    except:
        logging.getLogger("error_log").error(traceback.format_exc())
        return {"FEHLER": ["Fehler bei der Suche"]}, False


# Stress Test for booksearch
# if __name__ == "__main__":
#     from concurrent.futures import ThreadPoolExecutor
#     import requests
#     from functools import partial


#     results = []

#     # do some other stuff in the main process
#     params = (5, "0d5ff023174b6e8d6dc70e803ce2373a", 2, "Regression") # tuple of args for foo
#     fn = partial(get_book_links, )
#     with ThreadPoolExecutor(max_workers=50) as executor:
#         results = list(executor.map(lambda i: get_book_links(*params), [i for i in range(0,200)]))

#     for result in results:
#         results = len(result[0]['Regression (Buch)'])
#         assert results == 8
#     print("Done")