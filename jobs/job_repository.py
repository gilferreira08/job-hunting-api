"""In-memory repository for analyzed jobs.

This repository is intentionally simple for MVP usage and local testing.
It is designed with a clear interface so it can later be swapped with a
persistent database implementation (SQLite/PostgreSQL) without changing
higher-level service logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from jobs.job_parser import ParsedJobSignals


@dataclass
class JobRecord:
    id: str
    job_title: str
    company: str
    location: str
    source: str
    job_description: str
    application_url: str
    external_job_id: str
    date_found: str
    parsed_signals: ParsedJobSignals
    score: int
    recommendation: str
    strengths: list[str]
    gaps: list[str]
    application_status: str
    created_at: str


class JobRepository:
    """Repository abstraction for CRM-style job tracking.

    Scalability note:
    - Current implementation stores records in process memory.
    - Method signatures mimic common repository patterns so a future DB-backed
      class can implement the same methods with minimal API changes.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}

    def add_job(
        self,
        *,
        job_title: str,
        company: str,
        location: str,
        source: str,
        job_description: str,
        application_url: str,
        external_job_id: str = "",
        date_found: str | None = None,
        parsed_signals: ParsedJobSignals,
        score: int,
        recommendation: str,
        strengths: list[str],
        gaps: list[str],
        application_status: str = "Open",
    ) -> JobRecord:
        """Add analyzed job if not duplicate; return existing duplicate otherwise."""

        duplicates = self.find_duplicates(job_title=job_title, company=company, location=location)
        if duplicates:
            return duplicates[0]

        job = JobRecord(
            id=str(uuid4()),
            job_title=job_title,
            company=company,
            location=location,
            source=source,
            job_description=job_description,
            application_url=application_url,
            external_job_id=external_job_id,
            date_found=date_found or datetime.now(timezone.utc).isoformat(),
            parsed_signals=parsed_signals,
            score=score,
            recommendation=recommendation,
            strengths=strengths,
            gaps=gaps,
            application_status=application_status,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._jobs[job.id] = job
        return job

    def get_job(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[JobRecord]:
        # newest-first ordering is useful for CRM dashboards.
        return sorted(self._jobs.values(), key=lambda item: item.created_at, reverse=True)

    def update_status(self, job_id: str, new_status: str) -> JobRecord | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        job.application_status = new_status
        return job

    def find_duplicates(self, *, job_title: str, company: str, location: str) -> list[JobRecord]:
        """Find duplicates using company + normalized title + normalized location."""

        target_key = self._build_duplicate_key(company=company, job_title=job_title, location=location)
        return [
            job
            for job in self._jobs.values()
            if self._build_duplicate_key(
                company=job.company,
                job_title=job.job_title,
                location=job.location,
            )
            == target_key
        ]

    @staticmethod
    def _build_duplicate_key(*, company: str, job_title: str, location: str) -> str:
        def normalize(value: str) -> str:
            return " ".join(value.lower().strip().split())

        return f"{normalize(company)}::{normalize(job_title)}::{normalize(location)}"
