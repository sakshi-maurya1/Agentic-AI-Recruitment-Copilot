from pydantic import BaseModel
from typing import List


from pydantic import BaseModel, field_validator

class ResumeData(BaseModel):
    candidate_name: str
    education: str
    experience_years: float
    skills: list[str]
    projects: list[str]

    @field_validator("experience_years", mode="before")
    @classmethod
    def convert_experience(cls, value):
        if isinstance(value, str):
            value = value.replace("years", "").replace("year", "").strip()
        return float(value)


class JobDescriptionData(BaseModel):
    required_skills: List[str]
    preferred_skills: List[str]
    minimum_experience: float
    responsibilities: List[str]


class MatchResult(BaseModel):
    summary: str
    recommendation: str