import os
import fitz
from pathlib import Path
import openai as oai

current_dir = Path(__file__).parent
DATA_DIR = current_dir.parent / "data"

def read_pdf_from_directory(pdf_name: str) -> str:
	pdf_path = os.path.join(DATA_DIR, pdf_name)

	if not os.path.isfile(pdf_path):
		raise FileNotFoundError(f"PDF not found in directory: {pdf_path}")

	text = ""
	doc = fitz.open(pdf_path)
	for page in doc:
		text += page.get_text()
	doc.close()

	return text

def get_promise_vector(company_id: str):
	report_text = read_pdf_from_directory(company_id)
	oai.find_promises(report_text)
