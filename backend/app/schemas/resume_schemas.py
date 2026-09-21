"""Resume request/response schemas."""
from typing import List, Optional

from pydantic import BaseModel


class ProjectExtract(BaseModel):
    name: str
    description: str = ""
    technologies: List[str] = []


class EducationExtract(BaseModel):
    degree: str
    institution: str = ""
    year: Optional[int] = None


class ParsedResume(BaseModel):
    skills: List[str] = []
    projects: List[ProjectExtract] = []
    experience_years: Optional[float] = None
    certifications: List[str] = []
    education: List[EducationExtract] = []


class ResumeUploadResponse(BaseModel):
    resume_id: str
    file_name: str
    parsed: ParsedResume
