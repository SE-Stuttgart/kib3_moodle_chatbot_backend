import json
import traceback
from typing import Dict
import httplib2
import urllib
import config



def get_book_links(wstoken: str, course_id: int, searchTerm: str, word_context_length: int = 3, start=-1, end=-1) -> Dict:
    """
    Args:
        word_context_length: how many words before and after the search term should be included in search result
    """
    print("course_id", course_id)
    print("searchTerm", searchTerm)
    print("Adress: ", f"http://{config.MOODLE_SERVER_ADDR()}/webservice/rest/server.php")
    http_client = httplib2.Http(".cache")
    body={
            "wstoken": wstoken,
            "wsfunction": "block_slidefinder_get_searched_locations",
            "moodlewsrestformat": "json",
            "search_string": searchTerm,
            "course_id": course_id,
            "context_length": word_context_length
    }
    try:
        response = http_client.request(f"http://{config.MOODLE_SERVER_ADDR()}/webservice/rest/server.php",
            method="POST",
            headers={'Content-type': 'application/x-www-form-urlencoded'},
            body=urllib.parse.urlencode(body))[1] # result is binary string with escaped quotes -> decode
        data = json.loads(response.decode('unicode_escape').strip('"').replace('\/', '/'))
        
        """
        Example entry in data (list):
        {'Filename': 'Das Koordinatensystem', 'PDF Pagenum': 1, 'Url': 'http://193.196.53.252:80/mod/book/view.php?id=19&chapterid=34', 'Matched String': 'Koordinatensystem', 'Context': '... das Koordinatensystem was ist wo?foto ...'}
        """
        links = {}
        files = {}
        for search_result in data:
            if search_result['filename'] in files:
                files[search_result['filename']] += 1
            else: 
                files[search_result['filename']] = 0

        for search_result in data:
            
            context = search_result['context_snippet']
            if "?universität" in context:
                context = context.split("?universität")[0]
            if "universität stuttgart" in context:
                context = context.split("universität stuttgart")[0]
            if  0 < files[search_result['filename']] < 3:
                links[search_result['book_chapter_url']] = [search_result['filename'] + ": ", context]
            elif files[search_result['filename']] == -1:
                None
            else:
                links[search_result['book_chapter_url']] = [search_result['filename'], ""]
                files[search_result['filename']] = -1
              

        # only give back the specified number of results, if start -1 give back all results
        # if start out of range, give back empty dict, if end out of range, give back all results
        
        if start!=-1:
            if start < len(links) and end < len(links):
                links = dict(list(links.items())[start:end])
            elif start < len(links) and end >= len(links):
                links = dict(list(links.items())[start:])
            else:
                return {}
        print(links)
        
        return links
    except:
        print(traceback.format_exc())
        return {f"http://{config.MOODLE_SERVER_ADDR()}": "Fehler bei Suche"}

if __name__ == "__main__":
    # connect to database
    for result in get_book_links("testtoken", course_id=4, searchTerm="Koordinatensystem", word_context_length=3):
        print(result)
    