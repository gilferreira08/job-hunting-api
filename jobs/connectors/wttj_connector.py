from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from jobs.connectors.base_connector import BaseConnector


class WTTJConnector(BaseConnector):
    source_name = "welcometothejungle"

    def __init__(self) -> None:
        self.base_url = "https://www.welcometothejungle.com"
        self.last_diagnostic = "not-run"

    def search_jobs(self, query: str, location: str | None = None, limit: int = 10) -> list[dict]:
        search_url = f"{self.base_url}/en/jobs?query={quote_plus(query)}&aroundQuery={quote_plus(location or 'France')}"
        try:
            r = requests.get(search_url, timeout=20)
            r.raise_for_status()
        except requests.RequestException as exc:
            self.last_diagnostic = f"WTTJ search failed url={search_url} error={exc}"
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        anchors = soup.select("a[href]")
        out = []
        for a in anchors:
            href = a.get("href", "")
            title = " ".join(a.get_text(" ", strip=True).split())
            if "/jobs/" not in href or not title:
                continue
            out.append({"title": title, "url": urljoin(self.base_url, href), "location": location or "France"})
            if len(out) >= limit:
                break
        self.last_diagnostic = f"WTTJ search_url={search_url} status={r.status_code} candidates={len(out)}"
        return out

    def fetch_job_details(self, raw_job: dict) -> dict:
        detail_url = str(raw_job.get("url", "")).strip()
        if not detail_url:
            return self.normalize_job(raw_job)
        try:
            r = requests.get(detail_url, timeout=20)
            r.raise_for_status()
        except requests.RequestException as exc:
            self.last_diagnostic = f"WTTJ detail failed detail_url={detail_url} error={exc}"
            return self.normalize_job(raw_job)

        soup = BeautifulSoup(r.text, "html.parser")
        title_node = soup.select_one("h1")
        title = title_node.get_text(" ", strip=True) if title_node else str(raw_job.get("title", "")).strip()
        company_node = soup.select_one("[data-testid='company-name'], a[href*='/companies/']")
        company = company_node.get_text(" ", strip=True) if company_node else "Unknown company"
        location_node = soup.select_one("[data-testid='job-location'], [class*='location']")
        location = location_node.get_text(" ", strip=True) if location_node else str(raw_job.get("location", "France"))
        description_node = soup.select_one("main") or soup.select_one("article") or soup
        description = " ".join(description_node.get_text(" ", strip=True).split())
        return self.normalize_job({"title": title, "company": company, "location": location, "description": description, "url": detail_url})

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
