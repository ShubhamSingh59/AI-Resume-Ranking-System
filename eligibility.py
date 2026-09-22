from schemas import ExtractedResumeData

# Define keyword sets for deterministic matching
PYTHON_KEYWORDS = {"python", "fastapi", "django", "flask", "sqlalchemy", "pytest", "celery"}
AI_KEYWORDS = {
    "ai", "llm", "rag", "agent", "langchain", "langgraph", "llamaindex", 
    "vector", "embedding", "openai", "huggingface", "generative ai", "genai",
    "machine learning", "nlp"
}

def check_eligibility(extracted_data: ExtractedResumeData) -> dict:
    has_python = False
    has_ai = False
    matched_skills = set()

    # Normalize all skills to lowercase for matching
    candidate_skills = [skill.lower() for skill in extracted_data.skills]
    
    # 1. Check Skills section
    for skill in candidate_skills:
        if any(py_kw in skill for py_kw in PYTHON_KEYWORDS):
            has_python = True
            matched_skills.add(skill.title())
        if any(ai_kw in skill for ai_kw in AI_KEYWORDS):
            has_ai = True
            matched_skills.add(skill.title())

    # 2. Check Projects (Name, Description, and Technologies)
    for project in extracted_data.projects:
        project_text = f"{project.name} {project.description} {' '.join(project.technologies)}".lower()
        
        # Look for Python evidence in projects
        if not has_python and any(py_kw in project_text for py_kw in PYTHON_KEYWORDS):
            has_python = True
            matched_skills.add("Python (Project Evidence)")
            
        # Look for AI evidence in projects
        if not has_ai and any(ai_kw in project_text for ai_kw in AI_KEYWORDS):
            has_ai = True
            matched_skills.add("AI/Agentic (Project Evidence)")

    # 3. Compile Results
    is_eligible = has_python and has_ai
    rejection_reasons = []
    
    if not has_python:
        rejection_reasons.append("No evidence of Python stack")
    if not has_ai:
        rejection_reasons.append("No AI/agentic project evidence")

    return {
        "eligible": is_eligible,
        "rejection_reasons": rejection_reasons,
        "matched_skills": list(matched_skills)
    }