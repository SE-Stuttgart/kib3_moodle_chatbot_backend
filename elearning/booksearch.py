import json
import traceback
from typing import Dict
import httplib2
import urllib



def get_book_links(course_id: int, searchTerm: str, word_context_length: int = 3) -> Dict:
    """
    Args:
        word_context_length: how many words before and after the search term should be included in search result
    """
    http_client = httplib2.Http(".cache")
    body={
            "wstoken": "03720a912f518f0c2213b63e949e6dc7",
            "wsfunction": "local_chatbotpdfsearch_get_location",
            "moodlewsrestformat": "json",
            "course_id": course_id,
            "search_string": searchTerm,
            "word_context_length": word_context_length
    }
    try:
        response = http_client.request("http://193.196.53.252/webservice/rest/server.php",
            method="POST",
            headers={'Content-type': 'application/x-www-form-urlencoded'},
            body=urllib.parse.urlencode(body))[1] # result is binary string with escaped quotes -> decode
        data = json.loads(response.decode('unicode_escape').strip('"').replace('\/', '/'))
        """
        Example entry in data (list):
        {'Filename': 'Das Koordinatensystem', 'PDF Pagenum': 1, 'Url': 'http://193.196.53.252:80/mod/book/view.php?id=19&chapterid=34', 'Matched String': 'Koordinatensystem', 'Context': '... das Koordinatensystem was ist wo?foto ...'}
        """
        links = {}
        for search_result in data:
            links[search_result['Url']] = search_result['Filename'] + ": " + search_result['Context']
        return links
    except:
        print(traceback.format_exc())
        return {"http://193.196.53.252": "Fehler bei Suche"}

if __name__ == "__main__":
    # connect to database
    for result in get_book_links(course_id=2, searchTerm="Koordinatensystem", word_context_length=3):
        print(result)
    