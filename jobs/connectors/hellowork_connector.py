from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from jobs.connectors.base_connector import BaseConnector


class HelloWorkConnector(BaseConnector):
    source_name = "hellowork"

    def __init__(self) -> None:
        self.base_url = "https://www.hellowork.com"
        self.last_diagnostic = "not-run"

    def search_jobs(self, query: str, location: str | None = None, limit: int = 10) -> list[dict]:
        loc = quote_plus((location or "France").strip())
        q = quote_plus(query)
        search_url = f"{self.base_url}/fr-fr/emploi/recherche.html?k={q}&l={loc}"
        try:
            r = requests.get(search_url, timeout=20)
            r.raise_for_status()
        except requests.RequestException as exc:
            self.last_diagnostic = f"HelloWork search failed url={search_url} error={exc}"
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        anchors = soup.select("a[href]")
        candidates = []
        for a in anchors:
            href = a.get("href", "")
            title = " ".join(a.get_text(" ", strip=True).split())
            if not href or not title:
                continue
            if "emploi" not in href.lower() and "job" not in href.lower():
                continue
            candidates.append({"title": title, "url": urljoin(self.base_url, href), "location": location or "France"})
            if len(candidates) >= limit:
                break
        self.last_diagnostic = f"HelloWork search_url={search_url} status={r.status_code} candidates={len(candidates)}"
        return candidates

    def fetch_job_details(self, raw_job: dict) -> dict:
        detail_url = str(raw_job.get("url", "")).strip()
        if not detail_url:
            return self.normalize_job(raw_job)
        try:
            r = requests.get(detail_url, timeout=20)
            r.raise_for_status()
        except requests.RequestException as exc:
            self.last_diagnostic = f"HelloWork detail_failed detail_url={detail_url} error={exc}"
            return self.normalize_job(raw_job)

        soup = BeautifulSoup(r.text, "html.parser")
        title = (soup.select_one("h1").get_text(" ", strip=True) if soup.select_one("h1") else raw_job.get("title", ""))
        company = ""
        for sel in ["[data-testid='company-name']", ".company", "a[href*='entreprise']"]:
            node = soup.select_one(sel)
            if node and node.get_text(strip=True):
                company = node.get_text(" ", strip=True)
                break
        location = raw_job.get("location", "France")
        desc_node = soup.select_one("main") or soup.select_one("article") or soup
        description = " ".join(desc_node.get_text(" ", strip=True).split())
        return self.normalize_job({"title": title, "company": company or "Unknown company", "location": location, "description": description, "url": detail_url})

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
