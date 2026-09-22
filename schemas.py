from pydantic import BaseModel, Field
from typing import List

class Project(BaseModel):
    name: str = Field(description="The title or name of the project")
    description: str = Field(description="A concise summary of what the project does and the candidate's role")
    technologies: List[str] = Field(description="Technologies, languages, and frameworks used in this project")

class ExtractedResumeData(BaseModel):
    skills: List[str] = Field(description="A flat list of all technical skills, languages, and frameworks mentioned")
    projects: List[Project] = Field(description="A list of technical projects or internships listed on the resume")