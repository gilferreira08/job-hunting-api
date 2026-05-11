"""Job import orchestration layer.

Responsibilities:
- Accept raw job dictionaries from API/integration adapters
- Normalize and validate required fields
- Run parser + scorer + repository pipeline
- Return stored analyzed JobRecord

Future integrations:
This module is the natural entrypoint for ingestion connectors (LinkedIn,
eFinancialCareers, WelcomeToTheJungle, and company career pages). Each connector
can map external payloads to this importer contract while keeping scoring/storage
logic centralized.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from jobs.job_repository import JobRecord
from scoring.job_scorer import JobScorer




class JobRepositoryProtocol(Protocol):
    # Connectors must normalize into this shared schema before scoring/storage.
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
        parsed_signals: dict[str, object],
        score: int,
        recommendation: str,
        strengths: list[str],
        gaps: list[str],
        application_status: str = "Open",
    ) -> JobRecord: ...
class JobImportValidationError(ValueError):
    """Raised when a raw job payload is missing required fields."""


@dataclass
class NormalizedJobInput:
    job_title: str
    company: str
    location: str
    source: str
    job_description: str
    application_url: str
    external_job_id: str
    date_found: str | None


class JobImporter:
    """Import jobs through parse -> score -> repository pipeline."""

    REQUIRED_FIELDS = ("job_title", "company", "location", "source", "job_description", "application_url")

    def __init__(self, *, scorer: JobScorer, repository: JobRepositoryProtocol) -> None:
        self.scorer = scorer
        self.repository = repository

    def import_job(self, raw_job: dict[str, object]) -> JobRecord:
        normalized = self._normalize_and_validate(raw_job)

        # Duplicate prevention is delegated to repository.add_job(), so any caller
        # gets consistent de-duplication behavior across API/import integrations.
        parsed = self.scorer.parser.parse(normalized.job_description)
        score_result = self.scorer.score_job(normalized.job_description)

        return self.repository.add_job(
            job_title=normalized.job_title,
            company=normalized.company,
            location=normalized.location,
            source=normalized.source,
            job_description=normalized.job_description,
            application_url=normalized.application_url,
            external_job_id=normalized.external_job_id,
            date_found=normalized.date_found,
            parsed_signals=parsed,
            score=score_result.score,
            recommendation=score_result.recommendation,
            strengths=score_result.strengths,
            gaps=score_result.gaps,
            application_status="new",
        )

    def _normalize_and_validate(self, raw_job: dict[str, object]) -> NormalizedJobInput:
        normalized: dict[str, str] = {}

        for field in self.REQUIRED_FIELDS:
            value = raw_job.get(field)
            if field == "application_url" and value is None:
                value = raw_job.get("url")
            if not isinstance(value, str) or not value.strip():
                raise JobImportValidationError(
                    f"Invalid job payload: '{field}' is required and must be a non-empty string"
                )
            normalized[field] = " ".join(value.strip().split())

        application_url = raw_job.get("application_url") or raw_job.get("url")
        external_job_id = raw_job.get("external_job_id")
        date_found = raw_job.get("date_found")

        return NormalizedJobInput(
            job_title=normalized["job_title"],
            company=normalized["company"],
            location=normalized["location"],
            source=normalized["source"].lower(),
            job_description=normalized["job_description"],
            application_url=" ".join(str(application_url).strip().split()) if application_url else "",
            external_job_id=str(external_job_id).strip() if external_job_id else "",
            date_found=str(date_found).strip() if isinstance(date_found, str) and date_found.strip() else None,
        )
