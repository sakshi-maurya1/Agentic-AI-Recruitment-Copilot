from langchain_core.prompts import ChatPromptTemplate

from backend.llm import llm

from models.schemas import (
    ResumeData,
    JobDescriptionData,
    MatchResult
)


# Structured output
structured_llm = llm.with_structured_output(MatchResult)


# Prompt
match_prompt = ChatPromptTemplate.from_template(
    """
You are an expert Technical Recruiter.

You are given the extracted Resume information and Job Description information.

DO NOT calculate the match percentage.
The score has already been calculated by the system.

Generate:

1. A concise candidate summary.
2. A hiring recommendation.
3. Mention the matched skills.
4. Mention the missing required skills.
5. Mention whether the candidate satisfies the experience requirement.

Resume Information:
{resume}

Job Description Information:
{jd}

Match Percentage:
{match_percentage}

Candidate Level:
{candidate_level}

Matched Skills:
{matched_skills}

Missing Skills:
{missing_skills}

Experience Match:
{experience_match}
"""
)

match_chain = match_prompt | structured_llm


def calculate_match(
    resume: ResumeData,
    jd: JobDescriptionData
):

    # -----------------------------
    # Normalize Skills
    # -----------------------------
    resume_skills = {
        skill.lower().strip()
        for skill in resume.skills
    }

    required_skills = {
        skill.lower().strip()
        for skill in jd.required_skills
    }

    preferred_skills = {
        skill.lower().strip()
        for skill in jd.preferred_skills
    }

    # -----------------------------
    # Required Skills (80%)
    # -----------------------------
    matched_required = list(
        resume_skills.intersection(required_skills)
    )

    missing_required = list(
        required_skills.difference(resume_skills)
    )

    required_score = 0

    if required_skills:
        required_score = (
            len(matched_required)
            / len(required_skills)
        ) * 80

    # -----------------------------
    # Preferred Skills (20%)
    # -----------------------------
    matched_preferred = list(
        resume_skills.intersection(preferred_skills)
    )

    preferred_score = 0

    if preferred_skills:
        preferred_score = (
            len(matched_preferred)
            / len(preferred_skills)
        ) * 20

    # -----------------------------
    # Final Match Percentage
    # -----------------------------
    percentage = round(
        required_score + preferred_score,
        2
    )

    # -----------------------------
    # Experience Match
    # -----------------------------
    experience_match = (
        resume.experience_years
        >= jd.minimum_experience
    )

    # -----------------------------
    # Candidate Level
    # -----------------------------
    if percentage >= 85:
        candidate_level = "Excellent Match"

    elif percentage >= 70:
        candidate_level = "Good Match"

    elif percentage >= 50:
        candidate_level = "Average Match"

    else:
        candidate_level = "Poor Match"

    # -----------------------------
    # Call Gemini
    # -----------------------------
    llm_result = match_chain.invoke(
    {
        "resume": resume,
        "jd": jd,
        "match_percentage": percentage,
        "candidate_level": candidate_level,
        "matched_skills": matched_required + matched_preferred,
        "missing_skills": missing_required,
        "experience_match": experience_match,
    }
)

    return {
        "match_percentage": percentage,
        "matched_skills": matched_required + matched_preferred,
        "missing_skills": missing_required,
        "experience_match": experience_match,
        "summary": llm_result.summary,
        "recommendation": llm_result.recommendation,
    }