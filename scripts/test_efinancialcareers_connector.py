"""Manual Codex validation script for EFinancialCareersConnector."""

from __future__ import annotations

import importlib.util
import sys


def _check_dependencies() -> bool:
    missing: list[str] = []
    if importlib.util.find_spec("requests") is None:
        missing.append("requests")
    if importlib.util.find_spec("bs4") is None:
        missing.append("beautifulsoup4")

    if missing:
        print("Missing dependencies detected for eFinancialCareers connector test:")
        for dep in missing:
            print(f"- {dep}")
        print("Install with: python -m pip install requests beautifulsoup4")
        return False
    return True


if not _check_dependencies():
    sys.exit(1)

from jobs.connectors.efinancialcareers_connector import EFinancialCareersConnector


QUERIES = [
    "Treasury Manager",
    "Funding Manager",
    "Project Finance",
    "Structured Finance",
    "ALM Liquidity",
]


def run_checks(location: str = "France", limit: int = 10) -> None:
    connector = EFinancialCareersConnector()

    for query in QUERIES:
        print("\n" + "=" * 80)
        print(f"Query: {query}")

        raw_jobs = connector.search_jobs(query=query, location=location, limit=limit)
        normalized = [connector.normalize_job(job) for job in raw_jobs]

        debug = connector.last_debug
        print(f"Search URL: {debug.get('search_url')}")
        print(f"HTTP status: {debug.get('http_status')}")
        print(f"Final URL: {debug.get('final_url')}")
        print(f"Job-like links detected: {debug.get('job_like_detected')}")
        print(f"Normalized jobs returned: {debug.get('normalized_returned')}")

        for idx, job in enumerate(normalized, start=1):
            print(f"{idx}. {job.get('job_title', '')}")
            print(f"   Company: {job.get('company', '')}")
            print(f"   Location: {job.get('location', '')}")
            print(f"   URL: {job.get('url', '')}")


if __name__ == "__main__":
    run_checks()
