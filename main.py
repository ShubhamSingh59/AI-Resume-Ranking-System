import argparse
import json
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from parser import extract_text_from_pdf, extract_candidate_metadata
from extractor import extract_skills_and_projects
from eligibility import check_eligibility
from github_client import enrich_github_profile
from scorer import score_candidate

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def process_single_resume(file_path: Path) -> dict:
    """Processes a single resume end-to-end to enable parallel execution."""
    logger.info(f"Processing: {file_path.name}")
    
    raw_text = extract_text_from_pdf(file_path)
    if not raw_text:
        logger.warning(f"Unreadable or empty resume: {file_path.name}")
        return {"status": "failed", "file_name": file_path.name}

    meta = extract_candidate_metadata(raw_text, file_path.name)
    extracted_data = extract_skills_and_projects(raw_text)
    eligibility = check_eligibility(extracted_data)

    if not eligibility["eligible"]:
        return {
            "status": "rejected",
            "data": {
                "candidate": meta["name"],
                "email": meta["email"],
                "file_name": file_path.name,
                "eligible": False,
                "rejection_reasons": eligibility["rejection_reasons"],
                "matched_skills": eligibility["matched_skills"]
            }
        }

    github_res = enrich_github_profile(meta["github_username"])
    llm_score = score_candidate(extracted_data)

    total_score = (
        llm_score.ai_project_depth
        + llm_score.python_backend
        + llm_score.cloud_fullstack
        + llm_score.engineering_depth
        + github_res["github_score"]
    )

    return {
        "status": "eligible",
        "data": {
            "candidate_name": meta["name"],
            "email": meta["email"],
            "file_name": file_path.name,
            "eligible": True,
            "total_score": total_score,
            "score_breakdown": {
                "ai_project_depth": llm_score.ai_project_depth,
                "python_backend": llm_score.python_backend,
                "cloud_fullstack": llm_score.cloud_fullstack,
                "github": github_res["github_score"],
                "engineering_depth": llm_score.engineering_depth
            },
            "matched_skills": eligibility["matched_skills"],
            "project_summary": llm_score.project_summary,
            "github_summary": github_res["github_summary"],
            "strengths": llm_score.strengths,
            "concerns": llm_score.concerns
        }
    }

def run_pipeline(input_dir: str, output_path: str, max_workers: int = 5):
    resumes_dir = Path(input_dir)
    pdf_files = list(resumes_dir.glob("*.pdf"))

    eligible_candidates = []
    rejected_candidates = []
    failed_count = 0

    print(f"Found {len(pdf_files)} resumes to process in {input_dir}...")
    print(f"Processing concurrently with up to {max_workers} workers...")

    # Bounded concurrency: max_workers controls how many threads run simultaneously
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(process_single_resume, fp): fp for fp in pdf_files}
        
        # as_completed yields results as soon as a thread finishes
        for future in as_completed(future_to_file):
            try:
                result = future.result()
                if result["status"] == "failed":
                    failed_count += 1
                elif result["status"] == "rejected":
                    rejected_candidates.append(result["data"])
                elif result["status"] == "eligible":
                    eligible_candidates.append(result["data"])
            except Exception as e:
                logger.error(f"Unexpected error processing a file: {e}")
                failed_count += 1

    eligible_candidates.sort(key=lambda x: x["total_score"], reverse=True)
    for index, candidate in enumerate(eligible_candidates, start=1):
        candidate["rank"] = index

    final_output = {
        "batch_summary": {
            "total_resumes": len(pdf_files),
            "successfully_parsed": len(pdf_files) - failed_count,
            "eligible": len(eligible_candidates),
            "rejected": len(rejected_candidates),
            "failed_or_unreadable": failed_count
        },
        "ranked_candidates": eligible_candidates,
        "rejected_candidates": rejected_candidates
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    print("\n--- Screening Complete ---")
    print(json.dumps(final_output["batch_summary"], indent=2))
    print(f"Results successfully saved to: {out_file.resolve()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Resume Screening and Ranking CLI")
    parser.add_argument("--input", default="./resumes", help="Path to resume directory")
    parser.add_argument("--output", default="./output/results.json", help="Path to output JSON")
    parser.add_argument("--workers", type=int, default=5, help="Number of concurrent workers")
    args = parser.parse_args()

    run_pipeline(args.input, args.output, args.workers)