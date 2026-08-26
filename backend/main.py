from fastapi import FastAPI, UploadFile, File
import os
import shutil
import pytesseract

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
    return {
        "message": "AI Recruitment Copilot API Running 🚀"
    }


@app.post("/analyze")
async def analyze(
    resume: UploadFile = File(...),
    jd: UploadFile = File(...)
):

    resume_path = os.path.join(
        RESUME_FOLDER,
        resume.filename
    )

    jd_path = os.path.join(
        JD_FOLDER,
        jd.filename
    )

    with open(resume_path, "wb") as buffer:
        shutil.copyfileobj(
            resume.file,
            buffer
        )

    with open(jd_path, "wb") as buffer:
        shutil.copyfileobj(
            jd.file,
            buffer
        )

    resume_documents = load_pdf(
        resume_path
    )

    jd_documents = load_pdf(
        jd_path
    )

    create_vector_store(
        resume_documents, 
        "resume"
    )

    create_vector_store(
        jd_documents,
        "jd"
    )

    resume_text = "\n".join(
        doc.page_content
        for doc in resume_documents
    )

    jd_text = "\n".join(
        doc.page_content
        for doc in jd_documents
    )

    result = workflow.invoke(
        {
            "resume_text": resume_text,
            "jd_text": jd_text
        }
    )

    from pprint import pprint

    pprint(result)

    return {
        "resume_analysis": result["resume_data"],
        "job_description": result["jd_data"],
        "match_result": result["match_result"],
        "interview_questions": result["interview_questions"]
    }