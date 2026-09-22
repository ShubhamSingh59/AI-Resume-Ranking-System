import logging
from pydantic import BaseModel, Field
from typing import List
from config import SCORING_WEIGHTS
from extractor import get_llm
from schemas import ExtractedResumeData
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

logger = logging.getLogger(__name__)

# Define the scoring schema directly here to keep things simple
class LLMScoreBreakdown(BaseModel):
    ai_project_depth: int = Field(description="Score from 0 to 40 for AI/RAG/Agentic projects. Deduct 5-15 points if the project is a shallow API wrapper.")
    python_backend: int = Field(description="Score from 0 to 30 for Python, FastAPI, DBs, and async logic.")
    cloud_fullstack: int = Field(description="Score from 0 to 15 for GCP, Docker, deployment, and React.")
    engineering_depth: int = Field(description="Score from 0 to 5 for architecture, testing, CI/CD, and failure handling.")
    project_summary: str = Field(description="A 1-2 sentence evidence-backed summary of the candidate's technical projects.")
    strengths: List[str] = Field(description="List of 2-3 key technical strengths found in the resume.")
    concerns: List[str] = Field(description="List of 1-2 concerns, penalties applied, or missing skills.")

# Set up the parser for this specific schema
score_parser = PydanticOutputParser(pydantic_object=LLMScoreBreakdown)

def score_candidate(extracted_data: ExtractedResumeData) -> LLMScoreBreakdown:
    """Scores a candidate using the LLM based on extracted skills and projects."""
    
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a strict technical evaluator. Score the candidate based on their extracted skills and projects.\n"
            "Rules:\n"
            "- AI Project Depth (max 40): Reward real RAG, state, orchestration, and evaluation. Heavily penalize shallow LLM API wrappers.\n"
            "- Python & Backend (max 30): Reward evidence of backend systems over just keyword lists.\n"
            "- Cloud / Full Stack (max 15).\n"
            "- Engineering Depth (max 5).\n"
            "Ensure scores are integers within the maximum limits.\n\n"
            "{format_instructions}"
        ),
        (
            "human",
            "Candidate Skills:\n{skills}\n\nCandidate Projects:\n{projects}"
        )
    ])

    try:
        llm = get_llm()
        chain = prompt | llm | score_parser
        
        # Serialize the projects to a string format for the prompt
        projects_text = "\n".join([f"- {p.name}: {p.description} (Tech: {', '.join(p.technologies)})" for p in extracted_data.projects])
        skills_text = ", ".join(extracted_data.skills)

        result = chain.invoke({
            "skills": skills_text,
            "projects": projects_text,
            "format_instructions": score_parser.get_format_instructions()
        })
        
        # Guardrails: clamp the scores to their max limits defined in config.py just in case the LLM hallucinates
        result.ai_project_depth = min(max(result.ai_project_depth, 0), SCORING_WEIGHTS["ai_project_depth"])
        result.python_backend = min(max(result.python_backend, 0), SCORING_WEIGHTS["python_backend"])
        result.cloud_fullstack = min(max(result.cloud_fullstack, 0), SCORING_WEIGHTS["cloud_fullstack"])
        result.engineering_depth = min(max(result.engineering_depth, 0), SCORING_WEIGHTS["engineering_depth"])
        
        return result

    except Exception as e:
        logger.error(f"LLM scoring failed: {e}")
        # Return safe fallback with zero scores so the batch doesn't crash
        return LLMScoreBreakdown(
            ai_project_depth=0,
            python_backend=0,
            cloud_fullstack=0,
            engineering_depth=0,
            project_summary="Failed to parse project summary.",
            strengths=[],
            concerns=["LLM scoring adapter failed."]
        )