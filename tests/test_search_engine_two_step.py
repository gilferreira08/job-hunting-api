from jobs.job_importer import JobImporter
from jobs.job_repository import JobRepository
from jobs.job_search_engine import JobSearchEngine
from scoring.job_scorer import JobScorer


class DummyConnector:
    source_name = "dummy"
    last_diagnostic = "ok"

    def search_jobs(self, query, location=None, limit=10):
        return [{"url": "https://x/jobs/1", "title": "Treasury Manager"}]

    def fetch_job_details(self, raw_job):
        return {
            "job_title": "Treasury Manager",
            "company": "ACME",
            "location": "France",
            "job_description": "Treasury funding liquidity hedging role",
            "application_url": raw_job["url"],
            "source": "dummy",
            "external_job_id": "1",
            "date_found": "2026-05-11T00:00:00+00:00",
        }


def test_search_engine_two_step_flow():
    importer = JobImporter(scorer=JobScorer(), repository=JobRepository())
    engine = JobSearchEngine(connectors=[DummyConnector()], importer=importer)
    out = engine.search_and_import(query="Treasury Manager", location="France", limit_per_source=5)
    assert len(out) == 1
    assert out[0].application_url == "https://x/jobs/1"
    assert engine.last_run_diagnostics[0]["accepted_jobs_imported"] == 1
