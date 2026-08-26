from langchain_core.prompts import ChatPromptTemplate

from backend.llm import llm
from models.schemas import ResumeData


structured_llm = llm.with_structured_output(ResumeData, method="json_schema", strict=True)


resume_prompt = ChatPromptTemplate.from_template(
"""
You are an expert HR Resume Analyzer.

Extract the following information from the resume.

Return ONLY the structured data.

Rules:
- candidate_name must be a string.
- education must be a string.
- experience_years MUST be a NUMBER.
- Do NOT return "1 year", "2 years", or "Fresher".
- Return only values like:
  0
  1
  2.5
  5

- skills must be a list of strings.
- projects must be a list of strings.

Resume:
{resume}
"""
)

resume_chain = resume_prompt | structured_llm


def analyze_resume(resume_text: str):

    return resume_chain.invoke(
        {
            "resume": resume_text
        }
    )