"""Run a manual full-pipeline job search from Codex.

Runnable with:
    python -m scripts.manual_search
"""

from __future__ import annotations

import importlib.util
import os
import sys


def _check_dependencies() -> bool:
    missing: list[str] = []
    if importlib.util.find_spec("requests") is None:
        missing.append("requests")
    if importlib.util.find_spec("bs4") is None:
        missing.append("beautifulsoup4")

    if missing:
        print("Missing live-connector dependencies:")
        for dep in missing:
            print(f"- {dep}")
        print("Install with: python -m pip install requests beautifulsoup4")
        return False
    return True


if not _check_dependencies():
    sys.exit(1)

from jobs.connectors.company_careers_connector import CompanyCareersConnector
from jobs.connectors.efinancialcareers_connector import EFinancialCareersConnector
from jobs.connectors.france_travail_connector import FranceTravailConnector
from jobs.job_importer import JobImporter
from jobs.job_search_engine import JobSearchEngine
from jobs.sqlite_repository import SQLiteJobRepository
from scoring.job_scorer import JobScorer


DEFAULT_QUERIES = [
    "Treasury Manager",
]


def _build_connectors() -> list:
    connectors = [
        EFinancialCareersConnector(),
        # Generic company connector placeholder; pass a target company URL as needed.
        CompanyCareersConnector(company_name="Generic Company", careers_url=""),
    ]

    has_france_travail = bool(os.getenv("FRANCE_TRAVAIL_CLIENT_ID") and os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET"))
    if has_france_travail:
        connectors.insert(0, FranceTravailConnector())
    else:
        print("France Travail credentials not found; connector skipped.")

    return connectors


def run_manual_search(location: str = "France", limit_per_source: int = 10) -> None:
    repository = SQLiteJobRepository(db_path="data/jobs_test.db")
    importer = JobImporter(scorer=JobScorer(), repository=repository)
    search_engine = JobSearchEngine(connectors=_build_connectors(), importer=importer)

    all_results = []

    for query in DEFAULT_QUERIES:
        print("\n" + "=" * 90)
        print(f"Running query: {query} | location={location} | limit={limit_per_source}")
        results = search_engine.search_and_import(
            query=query,
            location=location,
            limit_per_source=limit_per_source,
        )
        for diag in search_engine.last_run_diagnostics:
            print(
                f"[diag] {diag.get('source')}: "
                f"raw={diag.get('raw_jobs_returned')} | {diag.get('diagnostic')}"
            )
        all_results.extend(results)

    ranked = sorted(all_results, key=lambda r: r.score, reverse=True)

    print("\n" + "#" * 90)
    print(f"Ranked imported jobs: {len(ranked)}")
    for idx, job in enumerate(ranked, start=1):
        print(f"\n{idx}. Score={job.score} | Recommendation={job.recommendation}")
        print(f"   Title: {job.job_title}")
        print(f"   Company: {job.company}")
        print(f"   Location: {job.location}")
        print(f"   Source: {job.source}")
        print(f"   URL: {job.application_url}")
        print(f"   Strengths: {', '.join(job.strengths)}")
        print(f"   Gaps: {', '.join(job.gaps)}")


if __name__ == "__main__":
    run_manual_search()
