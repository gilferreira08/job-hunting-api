"""Lightweight eFinancialCareers connector for finance job search pages."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin
import re
import time

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
        self.base_url_global = "https://www.efinancialcareers.com"
        self.base_url_france = "https://www.efinancialcareers.fr"
        self.last_diagnostic = "not-run"
        self.last_request_ts: float = 0.0
        self.min_delay_seconds = 2.0
        self.last_debug: dict[str, str | int | bool | None] = {
            "selected_domain": None,
            "search_url": None,
            "http_status": None,
            "final_url": None,
            "blocked_or_rate_limited": None,
            "job_like_detected": 0,
            "normalized_returned": 0,
            "candidate_url_tried": None,
            "page_title": None,
            "page_h1": None,
            "anchors_scanned": 0,
            "anchors_with_jobs_path": 0,
        }


    def _build_query_slug(self, query: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9\s-]+", "", query).strip()
        return re.sub(r"\s+", "-", cleaned)

    def search_jobs(self, query: str, location: str | None = None, limit: int = 10) -> list[dict]:
        location_value = (location or "France").strip()
        is_france_search = "france" in location_value.lower()
        base_url = self.base_url_france if is_france_search else self.base_url_global

        location_query = quote_plus(location_value)
        query_q = quote_plus(query)
        keyword_url = f"{base_url}/en/jobs?keywords={query_q}&location={location_query}" if is_france_search else f"{base_url}/jobs?keywords={query_q}&location={location_query}"

        slug = self._build_query_slug(query)
        candidate_urls = [
            f"{base_url}/en/jobs/{slug}/in-france-europe",
            f"{base_url}/en/jobs/{slug}",
            keyword_url,
        ] if is_france_search else [keyword_url]

        self.last_debug = {
            "selected_domain": base_url,
            "search_url": keyword_url,
            "http_status": None,
            "final_url": None,
            "blocked_or_rate_limited": None,
            "job_like_detected": 0,
            "normalized_returned": 0,
            "candidate_url_tried": None,
            "page_title": None,
            "page_h1": None,
            "anchors_scanned": 0,
            "anchors_with_jobs_path": 0,
        }

        # Polite throttling to reduce risk of rapid repeat requests.
        elapsed = time.time() - self.last_request_ts
        if elapsed < self.min_delay_seconds:
            time.sleep(self.min_delay_seconds - elapsed)

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        for candidate_url in candidate_urls:
            self.last_debug["candidate_url_tried"] = candidate_url
            try:
                response = requests.get(candidate_url, headers=headers, timeout=20)
                self.last_request_ts = time.time()
                response.raise_for_status()
            except requests.HTTPError:
                status = response.status_code if 'response' in locals() else None
                self.last_debug["http_status"] = status
                self.last_debug["blocked_or_rate_limited"] = status in {403, 429}
                continue
            except requests.RequestException as exc:
                self.last_diagnostic = f"eFinancialCareers request failed: {exc}"
                continue

            self.last_debug["http_status"] = response.status_code
            self.last_debug["final_url"] = response.url
            self.last_debug["blocked_or_rate_limited"] = response.status_code in {403, 429}

            parsed = self.parse_jobs_from_html(
                html=response.text,
                base_url=base_url,
                query=query,
                location=location,
                limit=limit,
            )
            if parsed:
                return parsed

        self.last_diagnostic = (
            f"eFinancialCareers domain={base_url} candidate_url={self.last_debug.get('candidate_url_tried')} "
            f"search_url={keyword_url} status={self.last_debug.get('http_status')} "
            f"blocked_or_rate_limited={self.last_debug.get('blocked_or_rate_limited')} "
            f"normalized=0"
        )
        return []


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
        page_title = (soup.title.get_text(" ", strip=True) if soup.title else "")
        h1 = soup.select_one("h1")
        h1_text = h1.get_text(" ", strip=True) if h1 else ""

        results: list[dict] = []
        anchors_with_jobs_path = 0
        for node in candidate_nodes:
            title = " ".join(node.get_text(" ", strip=True).split())
            href = node.get("href", "")
            if "/jobs/" in href.lower():
                anchors_with_jobs_path += 1
            if not title or not href:
                continue

            haystack = f"{title.lower()} {href.lower()}"
            if "job" not in haystack and "careers" not in haystack and "position" not in haystack:
                continue
            if not any(keyword in haystack for keyword in self.RELEVANCE_KEYWORDS):
                continue
            if any(ex in haystack for ex in self.EXCLUDED_KEYWORDS):
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

        self.last_debug["page_title"] = page_title
        self.last_debug["page_h1"] = h1_text
        self.last_debug["anchors_scanned"] = len(candidate_nodes)
        self.last_debug["anchors_with_jobs_path"] = anchors_with_jobs_path
        self.last_debug["job_like_detected"] = len(results)
        self.last_debug["normalized_returned"] = len(results)
        self.last_diagnostic = (
            f"eFinancialCareers domain={self.last_debug.get('selected_domain')} "
            f"candidate_url={self.last_debug.get('candidate_url_tried')} "
            f"search_url={self.last_debug.get('search_url')} status={self.last_debug.get('http_status')} "
            f"blocked_or_rate_limited={self.last_debug.get('blocked_or_rate_limited')} "
            f"title={page_title!r} h1={h1_text!r} anchors={len(candidate_nodes)} "
            f"jobs_path_anchors={anchors_with_jobs_path} normalized={len(results)}"
        )
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
