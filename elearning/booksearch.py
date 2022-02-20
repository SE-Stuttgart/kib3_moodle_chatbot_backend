import os
from pathlib import Path
from typing import Dict, List
import fitz
import re
from collections import namedtuple


from sqlalchemy.orm.session import sessionmaker
from elearning.moodledb import MCourseModule, MModule
from elearning.moodledb import MBookChapter, MBook, Base, connect_to_moodle_db, Session, MFile

# TODO maybe pre-extract text or multi-thread for better performance
PdfSearchResult = namedtuple("PdfSearchResult", ('pdfFilename', 'pageNumber', 'pageText'))


def get_all_pdf_files(session: Session) -> Dict[str, str]:
    """ get list of all pdf files from moodle database.
    Returns: Dict with
        * filename (without .pdf ending)
        * filepath (to access file on disk)
    """
    file_path_map = {}
    pdf_file_list = session.query(MFile).filter(MFile.mimetype=='application/pdf').all()
    for file in pdf_file_list:
        file_path_map[file.filename.rstrip(".pdf").lower()] = file.get_server_file_path()
    return file_path_map

def search_text_in_pdf(searchTerm: str, pdfFilename: str) -> List[PdfSearchResult]:
    """ search specific pdf file for search term """
    results = []
    pdfdoc = fitz.open(pdfFilename)
    for page in pdfdoc:
        text = page.get_text() # extract page text
        if len(re.findall(searchTerm, text, re.IGNORECASE)):
            # TODO: later add fuzzy matching
            results.append(PdfSearchResult(pdfFilename=pdfFilename, pageNumber=page.number+1, pageText=text))
    return results

def _delete_non_pdf_files(session: Session):
    """ cleanup for local adviser copies, do not use on server """
    file_path_map = get_all_pdf_files()
    pdf_file_list = set([file_path_map[filename].split("/")[-1] for filename in file_path_map])
    # remove non-pdf files
    for file in Path("resources/moodledata/").rglob("*"):
        if not file.is_file():
            continue
        if not file.name in pdf_file_list:
            os.remove(file.absolute()) # file.name
    # remove empty subdirectories
    for directory in Path("resources/moodledata/").rglob("*"):
        if not directory.is_dir():
            continue
        if len(os.listdir(directory)) == 0:
            os.rmdir(directory)
    # remove empty directories
    for directory in Path("resources/moodledata/").rglob("*"):
        if not directory.is_dir():
            continue
        if len(os.listdir(directory)) == 0:
            os.rmdir(directory)



def get_book_links(session: Session, searchTerm: str) -> Dict:
    """
    This is probably the only function you care about from this file.
    Returns:
        Links to moodle book chapters matching the search term by looking through the accompanying PDF and matching page numbers between both
    """
    # session.expire_all()
    links = {}
    
    # get a list of all pdf names and their locations
    file_path_map = get_all_pdf_files(session)
    file_names = set(file_path_map.keys())

    # get a list of all books
    books = session.query(MBook).all()
    
    # get the book module type id
    book_type_id = session.query(MModule).filter(MModule.name=="book").first().id

    for book in books:
        # see if we have a PDF matching the book's name
        normalized_book_name = book.name.lower().replace("der", "").replace("die", "").replace("das", "").replace("(buch)", "").strip()
        if normalized_book_name in file_names:
            # look for searchTerm in the PDF associated with the current book
            search_results = search_text_in_pdf(searchTerm, file_path_map[normalized_book_name]) 
            if len(search_results) == 0:
                continue # no results
            
            # find corresponding course module
            course_module = session.query(MCourseModule).filter(MCourseModule._type_id==book_type_id, MCourseModule.instance==book.id).first()

            # generate links for the search results pointing to corresponding book chapter
            for result in search_results:
                # find book chapter with page number of search result in PDF
                chapter = session.query(MBookChapter).filter(MBookChapter._bookid==book.id, MBookChapter.pagenum==result.pageNumber).first()
                # create link to chapter
                links[f"http://localhost/moodle/mod/book/view.php?id={course_module.id}&chapterid={chapter.id}"] = chapter.title
    return links

if __name__ == "__main__":
    # connect to database
    engine, conn = connect_to_moodle_db()
    Session = sessionmaker()
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)
    with Session() as session:
        _delete_non_pdf_files(session) # cleanup
        get_book_links(session, "Zusammenhang")
    conn.close()
    