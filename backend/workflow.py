from typing import TypedDict

from langgraph.graph import StateGraph, END

from agents.resume_agent import analyze_resume
from agents.jd_agent import analyze_job_description
from agents.matching_agent import calculate_match
from agents.interview_agent import generate_questions


class RecruitmentState(TypedDict):

    resume_text: str

    jd_text: str

    resume_data: object

    jd_data: object

    match_result: object

    interview_questions: str

def resume_node(state):

    resume = analyze_resume(
        state["resume_text"]
    )

    return {

        "resume_data": resume

    }

def jd_node(state):

    jd = analyze_job_description(

        state["jd_text"]

    )

    return {

        "jd_data": jd

    }

def matching_node(state):

    result = calculate_match(

        state["resume_data"],

        state["jd_data"]

    )

    return {

        "match_result": result

    }

def interview_node(state):

    questions = generate_questions(

        state["resume_data"],

        state["jd_data"]

    )

    return {

        "interview_questions": questions

    }

builder = StateGraph(
    RecruitmentState
)

builder.add_node(
    "resume",
    resume_node
)

builder.add_node(
    "jd",
    jd_node
)

builder.add_node(
    "match",
    matching_node
)

builder.add_node(
    "interview",
    interview_node
)

builder.set_entry_point(
    "resume"
)

builder.add_edge(
    "resume",
    "jd"
)

builder.add_edge(
    "jd",
    "match"
)

builder.add_edge(
    "match",
    "interview"
)

builder.add_edge(
    "interview",
    END
)

workflow = builder.compile()