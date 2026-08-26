from langchain_core.prompts import ChatPromptTemplate

from backend.llm import llm

from models.schemas import (
    ResumeData,
    JobDescriptionData,
    MatchResult
)

from rag.skill_matcher import find_semantic_matches


# Structured output
structured_llm = llm.with_structured_output(MatchResult, method="json_schema", strict=True)


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
    matched_required = set(
        resume_skills.intersection(required_skills)
    )

    missing_required = set(
        required_skills.difference(resume_skills)
    )

    # -----------------------------
    # Preferred Skills (20%) — exact match
    # -----------------------------
    matched_preferred = set(
        resume_skills.intersection(preferred_skills)
    )

    missing_preferred = set(
        preferred_skills.difference(resume_skills)
    )

    # -----------------------------
    # Semantic pass (FAISS) — catch near-matches that exact
    # string matching missed, e.g. "ml" vs "machine learning".
    # Only run against skills still missing after exact matching.
    # -----------------------------
    exact_matched_count = len(matched_required) + len(matched_preferred)

    semantic_matches_required = find_semantic_matches(
        resume_skills=list(resume_skills),
        jd_skills=list(missing_required),
    )

    semantic_matches_preferred = find_semantic_matches(
        resume_skills=list(resume_skills),
        jd_skills=list(missing_preferred),
    )

    for skill in semantic_matches_required:
        missing_required.discard(skill)
        matched_required.add(skill)

    for skill in semantic_matches_preferred:
        missing_preferred.discard(skill)
        matched_preferred.add(skill)

    semantic_matched_count = (
        len(semantic_matches_required) + len(semantic_matches_preferred)
    )

    matched_required = list(matched_required)
    missing_required = list(missing_required)
    matched_preferred = list(matched_preferred)
    missing_preferred = list(missing_preferred)

    required_score = 0

    if required_skills:
        required_score = (
            len(matched_required)
            / len(required_skills)
        ) * 80

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
        "missing_skills": missing_required + missing_preferred,
        "experience_match": experience_match,
    }
)

    return {
        "match_percentage": percentage,
        "matched_skills": matched_required + matched_preferred,
        "missing_skills": missing_required + missing_preferred,
        "experience_match": experience_match,
        "summary": llm_result.summary,
        "recommendation": llm_result.recommendation,
        # Benchmarking / interview evidence: how many additional matches
        # semantic (FAISS) matching found beyond exact string matching.
        "exact_matched_count": exact_matched_count,
        "semantic_matched_count": semantic_matched_count,
        "semantic_matches_detail": {
            **semantic_matches_required,
            **semantic_matches_preferred,
        },
    }