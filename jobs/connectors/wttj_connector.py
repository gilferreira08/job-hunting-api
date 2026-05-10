"""WelcomeToTheJungle connector skeleton.

TODO: implement official API integration or compliant retrieval strategy.
"""

from __future__ import annotations

from jobs.connectors.base_connector import BaseConnector


class WTTJConnector(BaseConnector):
    source_name = "welcometothejungle"

    def search_jobs(self, query: str, location: str | None = None, limit: int = 10) -> list[dict]:
        # TODO: integrate WTTJ data source. Return empty list for architecture-first MVP.
        return []

    def normalize_job(self, raw_job: dict) -> dict:
        # TODO: map WTTJ fields to importer schema.
        return raw_job
