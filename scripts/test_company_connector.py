"""Lightweight validation script for CompanyCareersConnector.

Notes:
- Career pages vary significantly across companies and platforms.
- Extraction quality will vary with page structure and content conventions.
- This script is intended for connector validation and iterative improvement.
"""

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
        print("Missing dependencies detected for company connector test:")
        for dep in missing:
            print(f"- {dep}")
        print("Install them with: python -m pip install requests beautifulsoup4")
        return False
    return True


if not _check_dependencies():
    sys.exit(1)

from jobs.connectors.company_careers_connector import CompanyCareersConnector


COMPANIES = [
    {"name": "TotalEnergies", "url": "https://careers.totalenergies.com/"},
    {"name": "Engie", "url": "https://jobs.engie.com/"},
    {"name": "EDF", "url": "https://www.edf.fr/en/the-edf-group/edf-recruits"},
    {"name": "Vinci", "url": "https://jobs.vinci.com/"},
    {"name": "Eiffage", "url": "https://www.eiffage.com/career"},
    {"name": "Veolia", "url": "https://www.veolia.com/en/careers"},
]


def run_connector_checks(query: str = "treasury", location: str = "France", limit: int = 10) -> None:
    for company in COMPANIES:
        connector = CompanyCareersConnector(
            company_name=company["name"],
            careers_url=company["url"],
        )
        results = connector.search_jobs(query=query, location=location, limit=limit)
        normalized = [connector.normalize_job(job) for job in results]

        debug = connector.last_debug
        print(f"\n=== {company['name']} ===")
        print(f"Careers URL: {company['url']}")
        print(f"HTTP status: {debug.get('http_status')}")
        print(f"Final URL: {debug.get('final_url')}")
        print(f"Anchors scanned: {debug.get('anchors_scanned')}")
        print(f"Potential job links detected: {debug.get('potential_links_detected')}")
        print(f"Normalized jobs returned: {len(normalized)}")

        for idx, job in enumerate(normalized, start=1):
            print(f"{idx}. {job.get('job_title', '')}")
            print(f"   URL: {job.get('url', '')}")


if __name__ == "__main__":
    run_connector_checks()
