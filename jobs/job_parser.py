"""Primary rule-based extraction layer for job text.

Parser responsibilities:
- Normalize raw job text
- Detect atomic signals (keywords, tools, seniority, geography)
- Return a structured extraction payload for downstream engines

The parser does NOT score opportunities. It only extracts facts/signals.
"""

from __future__ import annotations

import re
from typing import TypedDict


class ParsedJobSignals(TypedDict):
    detected_keywords: list[str]
    detected_finance_domains: list[str]
    detected_tools: list[str]
    seniority_level: str
    geography_relevance: str
    signal_flags: dict[str, bool]


class JobParser:
    """Extract structured treasury/project-finance signals from raw text."""

    def parse(self, raw_job_description: str) -> ParsedJobSignals:
        """Return structured extraction output consumed by the scorer layer."""

        text = self._normalize(raw_job_description)

        keyword_map = {
            "treasury": ["treasury"],
            "hedging": ["hedging", "fx hedging", "interest rate hedging"],
            "liquidity": ["liquidity", "cash management", "cash forecasting"],
            "funding": ["funding", "capital structure"],
            "refinancing": ["refinancing", "debt restructuring"],
            "dscr": ["dscr"],
            "irr": ["irr"],
            "cfads": ["cfads"],
            "project finance": ["project finance"],
            "infrastructure finance": ["infrastructure finance"],
            "bloomberg": ["bloomberg"],
            "vba": ["vba"],
            "sql": ["sql"],
        }

        detected_keywords = [
            keyword
            for keyword, aliases in keyword_map.items()
            if any(alias in text for alias in aliases)
        ]

        domain_rules = {
            "Treasury": ["treasury", "liquidity"],
            "Hedging & Risk": ["hedging"],
            "Funding & Refinancing": ["funding", "refinancing"],
            "Project Finance": ["project finance", "infrastructure finance", "dscr", "irr", "cfads"],
        }
        detected_finance_domains = [
            domain
            for domain, required_keywords in domain_rules.items()
            if any(item in detected_keywords for item in required_keywords)
        ]

        tools = ["Bloomberg", "VBA", "SQL"]
        detected_tools = [tool for tool in tools if tool.lower() in text]

        seniority_level = self._detect_seniority(text)
        geography_relevance = self._detect_geography_relevance(text)

        # Atomic boolean flags make scorer logic modular and scalable.
        signal_flags = {
            "treasury": "treasury" in detected_keywords,
            "hedging": "hedging" in detected_keywords,
            "liquidity": "liquidity" in detected_keywords,
            "funding": "funding" in detected_keywords,
            "refinancing": "refinancing" in detected_keywords,
            "dscr": "dscr" in detected_keywords,
            "irr": "irr" in detected_keywords,
            "cfads": "cfads" in detected_keywords,
            "project_finance": "project finance" in detected_keywords,
            "infrastructure_finance": "infrastructure finance" in detected_keywords,
            "bloomberg": "Bloomberg" in detected_tools,
            "vba": "VBA" in detected_tools,
            "sql": "SQL" in detected_tools,
            "junior": seniority_level == "Junior",
            "manager_plus": seniority_level in {"Manager", "Senior"},
            "senior": seniority_level == "Senior",
            "geo_high": geography_relevance == "High",
            "geo_good": geography_relevance == "Good",
            "geo_medium": geography_relevance == "Medium",
        }

        return {
            "detected_keywords": detected_keywords,
            "detected_finance_domains": detected_finance_domains,
            "detected_tools": detected_tools,
            "seniority_level": seniority_level,
            "geography_relevance": geography_relevance,
            "signal_flags": signal_flags,
        }

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()

    @staticmethod
    def _detect_seniority(text: str) -> str:
        if any(token in text for token in ["intern", "internship", "graduate", "junior"]):
            return "Junior"
        if any(token in text for token in ["senior manager", "head of", "director"]):
            return "Senior"
        if "manager" in text:
            return "Manager"
        if any(token in text for token in ["analyst", "associate", "specialist"]):
            return "Mid"
        return "Unspecified"

    @staticmethod
    def _detect_geography_relevance(text: str) -> str:
        if any(token in text for token in ["france", "paris", "portugal", "lisbon", "switzerland", "geneva"]):
            return "High"
        if any(token in text for token in ["luxembourg", "remote europe", "europe remote"]):
            return "Good"
        if "brazil" in text:
            return "Good"
        if "europe" in text:
            return "Medium"
        return "Low"
