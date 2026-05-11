from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus

import requests

from jobs.connectors.base_connector import BaseConnector


class IndeedConnector(BaseConnector):
    source_name = "indeed"

    def __init__(self) -> None:
        self.base_url = "https://www.indeed.com"
        self.last_diagnostic = "not-run"

    def search_jobs(self, query: str, location: str | None = None, limit: int = 10) -> list[dict]:
        search_url = f"{self.base_url}/jobs?q={quote_plus(query)}&l={quote_plus(location or 'France')}"
        try:
            r = requests.get(search_url, timeout=20)
            if r.status_code in {403, 429}:
                self.last_diagnostic = f"Indeed blocked search_url={search_url} status={r.status_code}"
                return []
            r.raise_for_status()
        except requests.RequestException as exc:
            self.last_diagnostic = f"Indeed search failed search_url={search_url} error={exc}"
            return []
        self.last_diagnostic = f"Indeed unsupported parsing in this environment search_url={search_url} status={r.status_code}"
        return []

    def fetch_job_details(self, raw_job: dict) -> dict:
        return self.normalize_job(raw_job)

    def normalize_job(self, raw_job: dict) -> dict:
        url = str(raw_job.get("url", "")).strip()
        return {
            "job_title": str(raw_job.get("title", "")).strip(),
            "company": str(raw_job.get("company", "Unknown company")).strip() or "Unknown company",
            "location": str(raw_job.get("location", "France")).strip() or "France",
            "job_description": str(raw_job.get("description", "")).strip() or str(raw_job.get("title", "")).strip(),
            "application_url": url,
            "source": self.source_name,
            "external_job_id": url.rstrip("/").split("/")[-1] if url else "",
            "date_found": datetime.now(timezone.utc).isoformat(),
        }
