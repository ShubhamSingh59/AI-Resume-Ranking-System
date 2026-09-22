import re
from pathlib import Path
from pypdf import PdfReader

GITHUB_REGEX = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9-]+)", re.IGNORECASE)
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Safely extracts all text from a PDF file."""
    text_content = []
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
    except Exception as e:
        return ""
    return "\n".join(text_content).strip()

def extract_candidate_metadata(text: str, file_name: str) -> dict:
    """Extracts candidate fallback name, email, and github handle."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
 
    raw_name = lines[0] if (lines and len(lines[0]) < 40 and not "@" in lines[0]) else Path(file_name).stem

    email_match = EMAIL_REGEX.search(text)
    email = email_match.group(0) if email_match else "Not Found"

    github_match = GITHUB_REGEX.search(text)
    github_user = github_match.group(1) if github_match else None
    
 
    if github_user and github_user.lower() in ["features", "pricing", "explore", "topics"]:
        github_user = None

    return {
        "name": raw_name.replace("_", " ").title(),
        "email": email,
        "github_username": github_user
    }