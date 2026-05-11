from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ai.job_insights import JobInsightsGenerator
from jobs.connectors.company_careers_connector import CompanyCareersConnector
from jobs.connectors.efinancialcareers_connector import EFinancialCareersConnector
from jobs.connectors.france_travail_connector import FranceTravailConnector
from jobs.connectors.wttj_connector import WTTJConnector
from jobs.job_search_engine import JobSearchEngine
from jobs.job_importer import JobImportValidationError, JobImporter
from jobs.job_parser import ParsedJobSignals
from jobs.job_repository import JobRecord
from jobs.sqlite_repository import SQLiteJobRepository
from scoring.job_scorer import JobScorer

app = FastAPI(title="Treasury & Project Finance AI Job Hunting Platform")
scorer = JobScorer()
repository = SQLiteJobRepository(db_path="data/jobs.db")
importer = JobImporter(scorer=scorer, repository=repository)
insights_generator = JobInsightsGenerator()
search_engine = JobSearchEngine(
    connectors=[FranceTravailConnector(), WTTJConnector(), EFinancialCareersConnector(), CompanyCareersConnector()],
    importer=importer,
)

SUPPORTED_STATUSES = {"new", "applied", "interview", "rejected", "offer", "archived"}


class ScoreJobRequest(BaseModel):
    job_title: str
    company: str
    location: str
    source: str = "manual"
    job_description: str
    application_url: str
    external_job_id: str = ""
    date_found: str | None = None


class JobResponse(BaseModel):
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
    ai_insights: dict[str, str] | None = None


class UpdateStatusRequest(BaseModel):
    status: Literal["new", "applied", "interview", "rejected", "offer", "archived"]


class SearchJobsRequest(BaseModel):
    query: str
    location: str | None = None
    limit_per_source: int = 10


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "project": "Treasury & Project Finance AI Job Hunting Platform",
        "status": "running",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/context")
def context() -> dict[str, str]:
    return {
        "mission": (
            "Build a focused treasury and project finance job-search CRM to track verified "
            "opportunities, manage applications, and improve strategic targeting."
        )
    }


@app.post("/score-job", response_model=JobResponse)
def score_job(payload: ScoreJobRequest) -> JobResponse:
    return import_job(payload)


@app.post("/import-job", response_model=JobResponse)
def import_job(payload: ScoreJobRequest) -> JobResponse:
    try:
        stored = importer.import_job(payload.model_dump())
    except JobImportValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    ai_insights = None
    if insights_generator.is_enabled():
        ai_insights = insights_generator.generate_insights(
            parsed_signals=stored.parsed_signals,
            score=stored.score,
            strengths=stored.strengths,
            gaps=stored.gaps,
            recommendation=stored.recommendation,
        )

    return _to_job_response(stored, ai_insights=ai_insights)


@app.post("/search-jobs", response_model=list[JobResponse])
def search_jobs(payload: SearchJobsRequest) -> list[JobResponse]:
    jobs = search_engine.search_and_import(
        query=payload.query,
        location=payload.location,
        limit_per_source=payload.limit_per_source,
    )

    # Debug diagnostics showing live-source return volumes.
    for entry in search_engine.last_run_diagnostics:
        if entry.get("source") in {"France Travail", "eFinancialCareers"}:
            print(
                f"[search-jobs] {entry.get('source')}: "
                f"{entry.get('raw_jobs_returned')} raw jobs | {entry.get('diagnostic')}"
            )

    return [_to_job_response(job) for job in jobs]


@app.get("/jobs", response_model=list[JobResponse])
def list_jobs() -> list[JobResponse]:
    return [_to_job_response(job) for job in repository.list_jobs()]


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    job = repository.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return _to_job_response(job)


@app.patch("/jobs/{job_id}/status", response_model=JobResponse)
def update_job_status(job_id: str, payload: UpdateStatusRequest) -> JobResponse:
    if payload.status not in SUPPORTED_STATUSES:
        raise HTTPException(status_code=400, detail="Unsupported status")

    job = repository.update_status(job_id, payload.status)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return _to_job_response(job)


def _to_job_response(job: JobRecord, ai_insights: dict[str, str] | None = None) -> JobResponse:
    return JobResponse(
        id=job.id,
        job_title=job.job_title,
        company=job.company,
        location=job.location,
        source=job.source,
        job_description=job.job_description,
        application_url=job.application_url,
        external_job_id=job.external_job_id,
        date_found=job.date_found,
        parsed_signals=job.parsed_signals,
        score=job.score,
        recommendation=job.recommendation,
        strengths=job.strengths,
        gaps=job.gaps,
        application_status=job.application_status,
        created_at=job.created_at,
        ai_insights=ai_insights,
    )
