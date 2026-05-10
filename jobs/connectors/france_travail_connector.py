"""France Travail connector.

This is the first real live-source connector in the project.
It uses credentials from environment variables and gracefully falls back
when API access is not configured.
"""

from __future__ import annotations

from datetime import datetime, timezone
import os

import requests

from jobs.connectors.base_connector import BaseConnector


class FranceTravailConnector(BaseConnector):
    source_name = "France Travail"

    TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
    SEARCH_URL = "https://api.emploi-store.fr/partenaire/offresdemploi/v2/offres/search"

    def __init__(self) -> None:
        self.client_id = os.getenv("FRANCE_TRAVAIL_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET", "").strip()
        self.last_diagnostic = "not-run"

    def search_jobs(self, query: str, location: str | None = None, limit: int = 10) -> list[dict]:
        if not self.client_id or not self.client_secret:
            self.last_diagnostic = (
                "France Travail credentials missing. "
                "Set FRANCE_TRAVAIL_CLIENT_ID and FRANCE_TRAVAIL_CLIENT_SECRET."
            )
            return []

        token = self._get_access_token()
        if not token:
            return []

        params = {
            "motsCles": query,
            "range": f"0-{max(limit - 1, 0)}",
        }
        if location:
            params["lieux"] = location

        try:
            response = requests.get(
                self.SEARCH_URL,
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            self.last_diagnostic = f"France Travail search request failed: {exc}"
            return []

        results = payload.get("resultats", []) if isinstance(payload, dict) else []
        self.last_diagnostic = f"France Travail returned {len(results)} jobs"
        return results[:limit]

    def normalize_job(self, raw_job: dict) -> dict:
        company = raw_job.get("entreprise", {}) if isinstance(raw_job.get("entreprise"), dict) else {}
        contact = raw_job.get("contact", {}) if isinstance(raw_job.get("contact"), dict) else {}

        return {
            "job_title": str(raw_job.get("intitule", "")).strip(),
            "company": str(company.get("nom", "Unknown company")).strip() or "Unknown company",
            "location": str(raw_job.get("lieuTravail", {}).get("libelle", "France")).strip()
            if isinstance(raw_job.get("lieuTravail"), dict)
            else "France",
            "source": self.source_name,
            "job_description": str(raw_job.get("description", "")).strip(),
            "url": str(contact.get("urlPostulation", "")).strip() or str(raw_job.get("origineOffre", {}).get("urlOrigine", "")).strip(),
            "external_job_id": raw_job.get("id"),
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

    def _get_access_token(self) -> str | None:
        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "api_offresdemploiv2 o2dsoffre",
                },
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            self.last_diagnostic = f"France Travail token request failed: {exc}"
            return None

        token = payload.get("access_token") if isinstance(payload, dict) else None
        if not token:
            self.last_diagnostic = "France Travail token response missing access_token"
            return None
        return str(token)
