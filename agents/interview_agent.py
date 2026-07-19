from langchain_core.prompts import ChatPromptTemplate

from backend.llm import llm


interview_prompt = ChatPromptTemplate.from_template(
"""
You are an experienced Technical Interviewer.

Based on the resume and job description generate:

- 5 Technical Questions

- 2 HR Questions

Resume

{resume}

Job Description

{jd}
"""
)

interview_chain = interview_prompt | llm


def generate_questions(
    resume,
    jd
):

    response = interview_chain.invoke(
        {
            "resume": resume,
            "jd": jd
        }
    )

    return response.content