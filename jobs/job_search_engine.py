"""Central job search orchestration engine.

This engine coordinates connectors + importer while keeping deterministic
parsing/scoring pipeline intact.
"""

from __future__ import annotations

from jobs.job_importer import JobImportValidationError, JobImporter
from jobs.job_repository import JobRecord


class JobSearchEngine:
    def __init__(self, connectors: list, importer: JobImporter) -> None:
        self.connectors = connectors
        self.importer = importer
        self.last_run_diagnostics: list[dict[str, object]] = []

    def search_and_import(
        self,
        query: str,
        location: str | None = None,
        limit_per_source: int = 10,
    ) -> list[JobRecord]:
        imported_jobs: list[JobRecord] = []

        self.last_run_diagnostics = []
        for connector in self.connectors:
            raw_jobs = connector.search_jobs(query, location, limit_per_source)
            self.last_run_diagnostics.append(
                {
                    "source": getattr(connector, "source_name", connector.__class__.__name__),
                    "raw_jobs_returned": len(raw_jobs),
                    "diagnostic": getattr(connector, "last_diagnostic", ""),
                }
            )
            for raw_job in raw_jobs:
                # Two-step connector contract:
                # 1) search_jobs returns raw/candidate summaries (typically with URL)
                # 2) fetch_job_details returns full normalized schema for importer
                normalized = connector.fetch_job_details(raw_job)
                try:
                    # Importer handles normalization/validation/scoring/storage and
                    # repository handles duplicate prevention.
                    record = self.importer.import_job(normalized)
                except JobImportValidationError:
                    # Skip malformed entries gracefully; continue processing source feed.
                    continue
                imported_jobs.append(record)

        # Ranking is deterministic and score-driven.
        return sorted(imported_jobs, key=lambda item: item.score, reverse=True)
