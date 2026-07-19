from langchain_core.prompts import ChatPromptTemplate

from backend.llm import llm
from models.schemas import JobDescriptionData


structured_llm = llm.with_structured_output(JobDescriptionData)


jd_prompt = ChatPromptTemplate.from_template(
    """
You are an HR expert.

Analyze this Job Description.

Extract:

- Required Skills
- Preferred Skills
- Experience Required
- Responsibilities

Job Description:

{jd}
"""
)


jd_chain = jd_prompt | structured_llm


def analyze_job_description(jd_text: str):

    return jd_chain.invoke(
        {
            "jd": jd_text
        }
    )