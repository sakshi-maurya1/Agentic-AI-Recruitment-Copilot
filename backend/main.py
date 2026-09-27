from fastapi import FastAPI, UploadFile, File
import os
import shutil
import platform
import pytesseract
from pdf2image import convert_from_path
from typing import List

# Only set tesseract_cmd explicitly on Windows (local dev).
# On Linux (Railway), tesseract is on PATH after nixpacks installs it —
# pytesseract finds it automatically, no override needed.
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

from utils.pdf_loader import load_pdf
from rag.vector_store import create_vector_store
from backend.workflow import workflow

app = FastAPI()

RESUME_FOLDER = "data/resumes"
JD_FOLDER = "data/job_descriptions"

os.makedirs(RESUME_FOLDER, exist_ok=True)
os.makedirs(JD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {"message": "AI Recruitment Copilot API Running 🚀"}


def extract_text_with_ocr_fallback(file_path, documents):
    """
    Uses load_pdf's extracted text if it looks real.
    Falls back to OCR if the PDF has no text layer (i.e. it's a scan).
    """
    text = "\n".join(doc.page_content for doc in documents).strip()

    if len(text) > 50:
        return text

    images = convert_from_path(file_path)
    ocr_text = "\n".join(pytesseract.image_to_string(img) for img in images)
    return ocr_text


@app.post("/analyze")
async def analyze(
    resumes: List[UploadFile] = File(...),
    jd: UploadFile = File(...)
):
    # --- JD: processed once, shared across all resumes ---
    jd_path = os.path.join(JD_FOLDER, jd.filename)
    with open(jd_path, "wb") as buffer:
        shutil.copyfileobj(jd.file, buffer)

    jd_documents = load_pdf(jd_path)
    create_vector_store(jd_documents, "jd")
    jd_text = extract_text_with_ocr_fallback(jd_path, jd_documents)

    results = []

    for resume in resumes:
        run_id = os.urandom(4).hex()  # avoids filename collisions between resumes
        resume_filename = f"{run_id}_{resume.filename}"
        resume_path = os.path.join(RESUME_FOLDER, resume_filename)

        with open(resume_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)

        resume_documents = load_pdf(resume_path)
        create_vector_store(resume_documents, f"resume_{run_id}")

        resume_text = extract_text_with_ocr_fallback(resume_path, resume_documents)

        result = workflow.invoke({
            "resume_text": resume_text,
            "jd_text": jd_text
        })

        results.append({
            "filename": resume.filename,
            "resume_analysis": result["resume_data"],
            "job_description": result["jd_data"],
            "match_result": result["match_result"],
            "interview_questions": result["interview_questions"]
        })

    return {"results": results}
