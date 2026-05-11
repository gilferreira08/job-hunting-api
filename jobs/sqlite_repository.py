"""SQLite-backed repository for analyzed jobs.

Why repository abstraction exists:
- API/services depend on repository methods, not storage internals.
- This allows swapping implementations (in-memory, SQLite, PostgreSQL)
  without changing parsing/scoring/business workflow code.

Future PostgreSQL migration path:
- Keep method signatures unchanged (`add_job`, `get_job`, `list_jobs`,
  `update_status`, `find_duplicates`).
- Replace sqlite SQL statements with PostgreSQL equivalents in a new
  repository class and wire it in dependency setup.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from uuid import uuid4

from jobs.job_parser import ParsedJobSignals
from jobs.job_repository import JobRecord


class SQLiteJobRepository:
    def __init__(self, db_path: str = "data/jobs.db") -> None:
        self.db_path = db_path
        self._ensure_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_database(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    job_title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT NOT NULL,
                    source TEXT NOT NULL,
                    job_description TEXT NOT NULL,
                    application_url TEXT NOT NULL DEFAULT '',
                    external_job_id TEXT NOT NULL DEFAULT '',
                    date_found TEXT NOT NULL DEFAULT '',
                    parsed_signals_json TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    recommendation TEXT NOT NULL,
                    strengths_json TEXT NOT NULL,
                    gaps_json TEXT NOT NULL,
                    application_status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC)"
            )
            existing_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(jobs)").fetchall()
            }
            if "application_url" not in existing_columns:
                connection.execute("ALTER TABLE jobs ADD COLUMN application_url TEXT NOT NULL DEFAULT ''")
            if "external_job_id" not in existing_columns:
                connection.execute("ALTER TABLE jobs ADD COLUMN external_job_id TEXT NOT NULL DEFAULT ''")
            if "date_found" not in existing_columns:
                connection.execute("ALTER TABLE jobs ADD COLUMN date_found TEXT NOT NULL DEFAULT ''")

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
        duplicates = self.find_duplicates(job_title=job_title, company=company, location=location)
        if duplicates:
            return duplicates[0]

        record = JobRecord(
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

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO jobs (
                    id, job_title, company, location, source, job_description,
                    application_url, external_job_id, date_found,
                    parsed_signals_json, score, recommendation,
                    strengths_json, gaps_json, application_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.job_title,
                    record.company,
                    record.location,
                    record.source,
                    record.job_description,
                    record.application_url,
                    record.external_job_id,
                    record.date_found,
                    json.dumps(record.parsed_signals),
                    record.score,
                    record.recommendation,
                    json.dumps(record.strengths),
                    json.dumps(record.gaps),
                    record.application_status,
                    record.created_at,
                ),
            )
        return record

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return self._row_to_job_record(row) if row else None

    def list_jobs(self) -> list[JobRecord]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        return [self._row_to_job_record(row) for row in rows]

    def update_status(self, job_id: str, new_status: str) -> JobRecord | None:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE jobs SET application_status = ? WHERE id = ?",
                (new_status, job_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return self._row_to_job_record(row) if row else None

    def find_duplicates(self, *, job_title: str, company: str, location: str) -> list[JobRecord]:
        target_key = self._build_duplicate_key(company=company, job_title=job_title, location=location)
        matches: list[JobRecord] = []
        for job in self.list_jobs():
            candidate_key = self._build_duplicate_key(
                company=job.company,
                job_title=job.job_title,
                location=job.location,
            )
            if candidate_key == target_key:
                matches.append(job)
        return matches

    @staticmethod
    def _build_duplicate_key(*, company: str, job_title: str, location: str) -> str:
        def normalize(value: str) -> str:
            return " ".join(value.lower().strip().split())

        return f"{normalize(company)}::{normalize(job_title)}::{normalize(location)}"

    @staticmethod
    def _row_to_job_record(row: sqlite3.Row) -> JobRecord:
        return JobRecord(
            id=row["id"],
            job_title=row["job_title"],
            company=row["company"],
            location=row["location"],
            source=row["source"],
            job_description=row["job_description"],
            application_url=row["application_url"],
            external_job_id=row["external_job_id"],
            date_found=row["date_found"],
            parsed_signals=json.loads(row["parsed_signals_json"]),
            score=row["score"],
            recommendation=row["recommendation"],
            strengths=json.loads(row["strengths_json"]),
            gaps=json.loads(row["gaps_json"]),
            application_status=row["application_status"],
            created_at=row["created_at"],
        )
