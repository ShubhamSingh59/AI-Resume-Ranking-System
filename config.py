import os
from dotenv import load_dotenv
load_dotenv()

# We will load al the credeitnal from env file here. Also we will declasre the weight constant also here

HF_TOKEN = os.getenv("HF_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SCORING_WEIGHTS = {
    "ai_project_depth": 40,      # Real AI systems: agents, RAG, tools, etc.
    "python_backend": 30,        # Python, FastAPI, PostgreSQL, Redis, etc.
    "cloud_fullstack": 15,       # GCP, Docker, React/Next.js (end-to-end)
    "github_activity": 10,       # Recent public activity, maintained repos
    "engineering_depth": 5       # Testing, architecture, caching, etc.
}