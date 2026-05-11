"""Base connector contract for external job sources.

Real connector implementations will be added iteratively. This interface keeps
source-specific logic separate from orchestration/import/scoring logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseConnector(ABC):
    source_name: str = "unknown"

    @abstractmethod
    def search_jobs(self, query: str, location: str | None = None, limit: int = 10) -> list[dict]:
        """Fetch raw job entries from a source."""

    @abstractmethod
    def normalize_job(self, raw_job: dict) -> dict:
        """Normalize a source-specific job payload to importer-compatible fields."""

    def fetch_job_details(self, raw_job: dict) -> dict:
        """Optional enrichment step from candidate/list item to full normalized job.

        Default behavior keeps backward compatibility by normalizing the candidate
        directly. Connectors that support detail-page extraction should override
        this method and return the full shared schema payload.
        """
        return self.normalize_job(raw_job)
