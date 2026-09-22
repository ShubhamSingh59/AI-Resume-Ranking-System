1. Setup and Run InstructionsPrerequisitesPython 3.10+Google Gemini API KeyInstallationClone or extract the repository to your workspace.   

Create and activate a virtual environment:Bashpython -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

Install required packages:Bashpip install -r requirements.txt

ConfigurationCreate a .env file in the root folder using .env.example as a template

# Custom paths and worker count
python main.py --input ./resumes --output ./output/results.json --workers 5


The application outputs a batch summary in the terminal and writes detailed evaluations to results.json.   

2. If I Had More TimeOCR & Multi-Column Document Parsing: 
Integrate pdfplumber or marker to improve layout detection on complex multi-column resumes and graphics where raw stream extraction can fragment text.Context-Aware Deduplication: Compute file and text hashes to detect duplicate submissions across applicants and skip repeated LLM calls.   Local Result Caching: Store LLM outputs and parsed GitHub metadata in a local SQLite/DuckDB cache to ensure idempotency and reduce API costs during re-runs.   FastAPI Web Service: Package the CLI into a containerized FastAPI application exposing POST /screen for asynchronous file uploads and GET /results for monitoring real-time processing status.   