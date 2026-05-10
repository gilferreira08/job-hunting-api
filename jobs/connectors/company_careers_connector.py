"""Generic company careers connector (MVP).

Important notes:
- Different companies expose very different HTML structures.
- This first version is intentionally generic and lightweight.
- Future versions may require company-specific adapters/selectors.
"""

from __future__ import annotations

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from jobs.connectors.base_connector import BaseConnector


class CompanyCareersConnector(BaseConnector):
    source_name = "company_careers"

    RELEVANCE_KEYWORDS = [
        "treasury",
        "funding",
        "liquidity",
        "hedging",
        "refinancing",
        "project finance",
        "cash management",
        "risk management",
        "corporate finance",
        "debt",
        "alm",
    ]
    EXCLUDED_KEYWORDS = ["accounting", "hr", "human resources", "assistant", "recruiter"]

    def __init__(self, company_name: str = "Unknown Company", careers_url: str = "") -> None:
        self.company_name = company_name
        self.careers_url = careers_url
        self.last_debug: dict[str, str | int | None] = {
            "company": company_name,
            "careers_url": careers_url,
            "http_status": None,
            "final_url": None,
            "anchors_scanned": 0,
            "potential_links_detected": 0,
        }

    def search_jobs(self, query: str, location: str | None = None, limit: int = 10) -> list[dict]:
        self.last_debug = {
            "company": self.company_name,
            "careers_url": self.careers_url,
            "http_status": None,
            "final_url": None,
            "anchors_scanned": 0,
            "potential_links_detected": 0,
        }

        if not self.careers_url:
            return []

        try:
            response = requests.get(self.careers_url, timeout=15)
            response.raise_for_status()
            self.last_debug["http_status"] = response.status_code
            self.last_debug["final_url"] = response.url
        except requests.RequestException:
            return []

        # Parsing/filtering split into dedicated method so fixture tests can validate
        # logic without live HTTP access in restricted Codex environments.
        return self.parse_jobs_from_html(
            html=response.text,
            base_url=self.careers_url,
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
        """Parse and filter job candidates from HTML fixture or live page HTML.

        Fixture tests validate this method in Codex/offline environments.
        Live HTTP validation should be done later in Replit or another runtime.
        """

        soup = BeautifulSoup(html, "html.parser")
        anchors = soup.find_all("a", href=True)
        self.last_debug["anchors_scanned"] = len(anchors)

        candidates: list[dict] = []
        for anchor in anchors:
            title = " ".join(anchor.get_text(" ", strip=True).split())
            href = anchor.get("href", "")
            if not title or not href:
                continue

            title_l = title.lower()
            href_l = href.lower()
            haystack = f"{title_l} {href_l}"

            if not any(k in haystack for k in ["job", "career", "vacancy", "position", "opportun"]):
                continue
            if not any(keyword in haystack for keyword in self.RELEVANCE_KEYWORDS):
                continue
            if any(excluded in haystack for excluded in self.EXCLUDED_KEYWORDS):
                continue
            if query and query.lower() not in title_l:
                continue

            full_url = urljoin(base_url, href)
            candidates.append(
                {
                    "title": title,
                    "url": full_url,
                    "location": location or "Not specified",
                }
            )
            if len(candidates) >= limit:
                break

        self.last_debug["potential_links_detected"] = len(candidates)
        return candidates

    def normalize_job(self, raw_job: dict) -> dict:
        return {
            "job_title": str(raw_job.get("title", "")).strip(),
            "company": self.company_name,
            "location": str(raw_job.get("location", "Not specified")).strip() or "Not specified",
            "source": self.source_name,
            "job_description": str(raw_job.get("title", "")).strip(),
            "url": str(raw_job.get("url", "")).strip(),
        }
