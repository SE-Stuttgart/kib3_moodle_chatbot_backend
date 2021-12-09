from typing import List

import fitz
import re
from collections import namedtuple
from moodledb import Session, MFile

PdfSearchResult = namedtuple("PdfSearchResult", ('pdfFilename', 'pageNumber', 'pageText'))

# TODO search through all pdfs (maybe multi-threaded)

def get_all_pdf_files(session: Session) -> List[str]:
    pdf_file_list = session.query(MFile).filter(MFile.mimetype=='application/pdf').all()
    return [pdf_file.get_server_file_path() for pdf_file in pdf_file_list]

def search_text_in_pdf(searchTerm: str, pdfFilename: str) -> List[PdfSearchResult]:
    results = []
    pdfdoc = fitz.open(pdfFilename)
    for page in pdfdoc:
        text = page.get_text() # extract page text
        if len(re.findall(searchTerm, text)):
            # TODO: later add fuzzy matching
            results.append(PdfSearchResult(pdfFilename=pdfFilename, pageNumber=page.number, pageText=text))
    return results

if __name__ == "__main__":
    with Session() as session:
        pdf_files = get_all_pdf_files(session)
        print("PDF FILES")
        print(pdf_files)

        for file in pdf_files:
            print("===========")
            print(file)
            print(search_text_in_pdf("Zusammenhang", file))