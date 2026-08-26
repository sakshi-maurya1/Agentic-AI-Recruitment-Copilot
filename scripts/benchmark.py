"""
Benchmark script for the AI Recruitment Copilot.

Runs the real pipeline (resume parsing -> resume agent -> jd agent ->
matching agent, with the FAISS semantic-matching pass inside it) across a
folder of resume PDFs against one job-description PDF, times each stage,
and logs everything to a CSV.

This calls your actual project functions directly — not the Streamlit UI —
so you can batch-test 100 resumes without clicking through the app 100 times.

Usage:
    python scripts/benchmark.py \
        --resumes_dir data/resumes \
        --jd_path data/job_descriptions/sample_jd.pdf \
        --output benchmark_results.csv \
        --skip_interview

Run from the project root (so the `agents`, `backend`, `rag`, `utils`
imports resolve the same way they do in backend/main.py).
"""

import argparse
import csv
import os
import time
import statistics
import sys

# Make project root importable when running as `python scripts/benchmark.py`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.pdf_loader import load_pdf
from agents.resume_agent import analyze_resume
from agents.jd_agent import analyze_job_description
from agents.matching_agent import calculate_match
from agents.interview_agent import generate_questions


def load_text(pdf_path):
    docs = load_pdf(pdf_path)
    return "\n".join(doc.page_content for doc in docs)


def timed(fn, *args, **kwargs):
    """Run fn, return (result, elapsed_seconds)."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return result, elapsed


def timed_with_retry(fn, *args, max_retries=5, base_delay=5, **kwargs):
    """
    Like timed(), but retries on Groq 429 (rate limit) errors with
    exponential backoff instead of crashing the whole batch run.
    Only retries on 429s — other errors (e.g. malformed resume, parsing
    failure) still raise immediately so they show up in the CSV as a
    genuine per-resume failure, not a silent retry loop.
    """
    for attempt in range(max_retries + 1):
        try:
            return timed(fn, *args, **kwargs)
        except Exception as e:
            is_rate_limit = "429" in str(e) or "rate_limit" in str(e).lower() \
                or "Too Many Requests" in str(e)
            if is_rate_limit and attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                print(f"  Rate limited — waiting {delay}s before retry "
                      f"({attempt + 1}/{max_retries})...")
                time.sleep(delay)
                continue
            raise


def percentile(values, pct):
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * (pct / 100)
    f = int(k)
    c = min(f + 1, len(values) - 1)
    if f == c:
        return values[f]
    return values[f] + (values[c] - values[f]) * (k - f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resumes_dir", required=True, help="Folder of resume PDFs")
    parser.add_argument("--jd_path", required=True, help="Path to a single job description PDF")
    parser.add_argument("--output", default="benchmark_results.csv")
    parser.add_argument("--limit", type=int, default=None, help="Only process first N resumes")
    parser.add_argument(
        "--skip_interview",
        action="store_true",
        help="Skip the interview-question generation LLM call — it doesn't "
             "affect match scoring, and skipping it saves API calls/time "
             "when batch-testing 100 resumes.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Seconds to pause between resumes, to stay under Groq's free-tier "
             "rate limit. Increase this if you still hit 429s. Default: 2.0",
    )
    args = parser.parse_args()

    resume_files = sorted(
        f for f in os.listdir(args.resumes_dir)
        if f.lower().endswith(".pdf")
    )
    if args.limit:
        resume_files = resume_files[: args.limit]

    if not resume_files:
        print(f"No PDF files found in {args.resumes_dir}")
        return

    print(f"Found {len(resume_files)} resumes. Loading job description...")

    # JD is the same for every resume in this run — parse it once, not per resume.
    jd_text = load_text(args.jd_path)
    jd_data, jd_agent_time = timed_with_retry(analyze_job_description, jd_text)
    print(f"JD parsed in {jd_agent_time:.3f}s")

    rows = []
    parse_times, resume_agent_times, matching_times, interview_times, total_times = (
        [], [], [], [], []
    )
    exact_counts, semantic_counts = [], []
    resumes_with_uplift = 0
    ocr_count = 0

    for i, filename in enumerate(resume_files, start=1):
        path = os.path.join(args.resumes_dir, filename)
        print(f"[{i}/{len(resume_files)}] {filename}")

        run_start = time.perf_counter()

        try:
            resume_docs, parse_time = timed(load_pdf, path)
            resume_text = "\n".join(doc.page_content for doc in resume_docs)
            ocr_used = any(doc.metadata.get("ocr_used") for doc in resume_docs)
            resume_data, resume_agent_time = timed_with_retry(analyze_resume, resume_text)
            match_result, matching_time = timed_with_retry(calculate_match, resume_data, jd_data)

            interview_time = 0.0
            if not args.skip_interview:
                _, interview_time = timed_with_retry(generate_questions, resume_data, jd_data)

            total_time = time.perf_counter() - run_start

            parse_times.append(parse_time)
            resume_agent_times.append(resume_agent_time)
            matching_times.append(matching_time)
            if not args.skip_interview:
                interview_times.append(interview_time)
            total_times.append(total_time)

            exact_c = match_result.get("exact_matched_count", 0)
            semantic_c = match_result.get("semantic_matched_count", 0)
            exact_counts.append(exact_c)
            semantic_counts.append(semantic_c)
            if semantic_c > 0:
                resumes_with_uplift += 1
            if ocr_used:
                ocr_count += 1

            rows.append({
                "filename": filename,
                "ocr_used": ocr_used,
                "parse_time_s": round(parse_time, 4),
                "resume_agent_time_s": round(resume_agent_time, 4),
                "matching_time_s": round(matching_time, 4),
                "interview_time_s": round(interview_time, 4),
                "total_time_s": round(total_time, 4),
                "match_percentage": match_result.get("match_percentage"),
                "exact_matched_count": exact_c,
                "semantic_matched_count": semantic_c,
                "semantic_matches_detail": match_result.get("semantic_matches_detail"),
                "error": "",
            })

        except Exception as e:
            rows.append({
                "filename": filename,
                "ocr_used": "",
                "parse_time_s": "", "resume_agent_time_s": "",
                "matching_time_s": "", "interview_time_s": "",
                "total_time_s": "", "match_percentage": "",
                "exact_matched_count": "", "semantic_matched_count": "",
                "semantic_matches_detail": "",
                "error": str(e),
            })
            print(f"  FAILED: {e}")

        # Small pacing delay between resumes to stay under Groq's free-tier
        # rate limit — cheaper than retrying after a 429 hits.
        time.sleep(args.delay)

    # Write CSV
    fieldnames = [
        "filename", "ocr_used", "parse_time_s", "resume_agent_time_s", "matching_time_s",
        "interview_time_s", "total_time_s", "match_percentage",
        "exact_matched_count", "semantic_matched_count",
        "semantic_matches_detail", "error",
    ]
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    n_ok = len(total_times)
    n_failed = len(resume_files) - n_ok

    print("\n" + "=" * 60)
    print(f"BENCHMARK SUMMARY  ({n_ok} succeeded, {n_failed} failed)")
    print("=" * 60)

    if n_ok:
        print(f"Avg parse time:        {statistics.mean(parse_times):.3f}s")
        print(f"Avg resume-agent time: {statistics.mean(resume_agent_times):.3f}s")
        print(f"Avg matching time:     {statistics.mean(matching_times):.3f}s (includes FAISS semantic pass)")
        if not args.skip_interview and interview_times:
            print(f"Avg interview time:    {statistics.mean(interview_times):.3f}s")
        print(f"Avg total time/resume: {statistics.mean(total_times):.3f}s")
        print(f"p95 total time/resume: {percentile(total_times, 95):.3f}s")
        print()
        print(f"Avg exact-matched skills per resume:    {statistics.mean(exact_counts):.2f}")
        print(f"Avg semantic-matched skills per resume: {statistics.mean(semantic_counts):.2f}")
        print(f"Resumes where semantic matching found >=1 extra skill: "
              f"{resumes_with_uplift}/{n_ok} ({100 * resumes_with_uplift / n_ok:.1f}%)")
        print(f"Resumes that required OCR (image-based/scanned): {ocr_count}/{n_ok}")

    print(f"\nFull results written to {args.output}")


if __name__ == "__main__":
    main()