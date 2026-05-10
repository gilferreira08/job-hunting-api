"""Lightweight eFinancialCareers connector for finance job search pages."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from jobs.connectors.base_connector import BaseConnector


class EFinancialCareersConnector(BaseConnector):
    source_name = "eFinancialCareers"

    RELEVANCE_KEYWORDS = [
        "treasury",
        "funding",
        "liquidity",
        "hedging",
        "refinancing",
        "project finance",
        "structured finance",
        "debt",
        "alm",
        "risk management",
    ]
    EXCLUDED_KEYWORDS = [
        "audit intern",
        "accounting assistant",
        "junior accountant",
        "back office",
        "back office only",
        "internship",
    ]

    def __init__(self) -> None:
        self.base_url = "https://www.efinancialcareers.com"
        self.last_diagnostic = "not-run"
        self.last_debug: dict[str, str | int | None] = {
            "search_url": None,
            "http_status": None,
            "final_url": None,
            "job_like_detected": 0,
            "normalized_returned": 0,
        }

    def search_jobs(self, query: str, location: str | None = None, limit: int = 10) -> list[dict]:
        location_query = quote_plus(location) if location else "France"
        query_q = quote_plus(query)
        search_url = f"{self.base_url}/jobs?keywords={query_q}&location={location_query}"

        self.last_debug = {
            "search_url": search_url,
            "http_status": None,
            "final_url": None,
            "job_like_detected": 0,
            "normalized_returned": 0,
        }

        try:
            response = requests.get(search_url, timeout=20)
            response.raise_for_status()
        except requests.RequestException as exc:
            self.last_diagnostic = f"eFinancialCareers request failed: {exc}"
            return []

        self.last_debug["http_status"] = response.status_code
        self.last_debug["final_url"] = response.url

        # Parsing/filtering is separated for fixture-based offline validation.
        return self.parse_jobs_from_html(
            html=response.text,
            base_url=self.base_url,
            query=query,
            location=location,
            limit=limit,
        )

    def parse_jobs_from_html(
        self,
        *,
        html: str,
        base_url: str,
        query: str,
        location: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Parse eFinancialCareers-like HTML in offline fixture tests.

        Fixture tests validate connector logic in restricted Codex environments.
        Live HTTP validation should happen later in Replit or another runtime.
        """

        soup = BeautifulSoup(html, "html.parser")
        candidate_nodes = soup.select("a[href]")

        results: list[dict] = []
        for node in candidate_nodes:
            title = " ".join(node.get_text(" ", strip=True).split())
            href = node.get("href", "")
            if not title or not href:
                continue

            haystack = f"{title.lower()} {href.lower()}"
            if "job" not in haystack and "careers" not in haystack and "position" not in haystack:
                continue
            if not any(keyword in haystack for keyword in self.RELEVANCE_KEYWORDS):
                continue
            if any(ex in haystack for ex in self.EXCLUDED_KEYWORDS):
                continue
            if query and query.lower() not in title.lower():
                continue

            full_url = urljoin(base_url, href)
            results.append(
                {
                    "title": title,
                    "company": "",
                    "location": location or "France/Europe",
                    "description": title,
                    "url": full_url,
                }
            )
            if len(results) >= limit:
                break

        self.last_debug["job_like_detected"] = len(results)
        self.last_debug["normalized_returned"] = len(results)
        return results

    def normalize_job(self, raw_job: dict) -> dict:
        url = str(raw_job.get("url", "")).strip()
        external_id = url.rstrip("/").split("/")[-1] if url else None
        return {
            "job_title": str(raw_job.get("title", "")).strip(),
            "company": str(raw_job.get("company", "Unknown company")).strip() or "Unknown company",
            "location": str(raw_job.get("location", "France/Europe")).strip() or "France/Europe",
            "source": self.source_name,
            "job_description": str(raw_job.get("description", "")).strip() or str(raw_job.get("title", "")).strip(),
            "url": url,
            "external_job_id": external_id,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }
