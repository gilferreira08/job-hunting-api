"""Rule-based scoring engine built on top of parser-extracted signals.

Scorer responsibilities:
- Consume structured parser output
- Compute weighted category scores
- Produce recommendation, strengths, and gaps

Why separation exists:
- Parser centralizes text extraction logic in one place.
- Scorer focuses on business scoring logic, not text matching.
- This modularity makes future upgrades (new signals/models) easier.
"""

from __future__ import annotations

from dataclasses import dataclass

from jobs.job_parser import JobParser, ParsedJobSignals


WEIGHTS = {
    "treasury_relevance": 0.30,
    "project_finance_exposure": 0.20,
    "debt_funding_refinancing": 0.15,
    "seniority": 0.15,
    "tools_and_systems": 0.10,
    "location_relevance": 0.10,
}


@dataclass(frozen=True)
class ScoreResult:
    score: int
    recommendation: str
    strengths: list[str]
    gaps: list[str]
    category_scores: dict[str, int]


class JobScorer:
    """Score job fit from structured parser signals."""

    def __init__(self, parser: JobParser | None = None) -> None:
        self.parser = parser or JobParser()

    def score_job(self, job_description: str) -> ScoreResult:
        parsed = self.parser.parse(job_description)

        category_scores = {
            "treasury_relevance": self._score_treasury_relevance(parsed),
            "project_finance_exposure": self._score_project_finance(parsed),
            "debt_funding_refinancing": self._score_debt_funding(parsed),
            "seniority": self._score_seniority(parsed),
            "tools_and_systems": self._score_tools_systems(parsed),
            "location_relevance": self._score_location(parsed),
        }

        weighted_score = sum(
            category_scores[key] * WEIGHTS[key] for key in category_scores
        )
        final_score = int(round(weighted_score))

        strengths, gaps = self._build_strengths_and_gaps(category_scores)
        recommendation = self._recommendation(final_score, parsed)

        return ScoreResult(
            score=final_score,
            recommendation=recommendation,
            strengths=strengths,
            gaps=gaps,
            category_scores=category_scores,
        )

    def _score_treasury_relevance(self, parsed: ParsedJobSignals) -> int:
        flags = parsed["signal_flags"]
        score = 0
        if flags["treasury"]:
            score += 45
        if flags["liquidity"]:
            score += 25
        if flags["hedging"]:
            score += 20
        if flags["funding"]:
            score += 10
        return min(score, 100)

    def _score_project_finance(self, parsed: ParsedJobSignals) -> int:
        flags = parsed["signal_flags"]
        score = 0
        if flags["project_finance"]:
            score += 45
        if flags["infrastructure_finance"]:
            score += 25
        if flags["dscr"]:
            score += 10
        if flags["irr"]:
            score += 10
        if flags["cfads"]:
            score += 10
        return min(score, 100)

    def _score_debt_funding(self, parsed: ParsedJobSignals) -> int:
        flags = parsed["signal_flags"]
        score = 0
        if flags["funding"]:
            score += 45
        if flags["refinancing"]:
            score += 35
        if flags["liquidity"]:
            score += 20
        return min(score, 100)

    def _score_seniority(self, parsed: ParsedJobSignals) -> int:
        level = parsed["seniority_level"]
        if level == "Junior":
            return 10
        if level == "Senior":
            return 90
        if level == "Manager":
            return 85
        if level == "Mid":
            return 65
        return 50

    def _score_tools_systems(self, parsed: ParsedJobSignals) -> int:
        tool_count = len(parsed["detected_tools"])
        # 0 tools -> 20 baseline, then +25 per tool up to 95.
        return min(20 + (tool_count * 25), 95)

    def _score_location(self, parsed: ParsedJobSignals) -> int:
        relevance = parsed["geography_relevance"]
        if relevance == "High":
            return 100
        if relevance == "Good":
            return 90
        if relevance == "Medium":
            return 80
        return 35

    def _build_strengths_and_gaps(self, category_scores: dict[str, int]) -> tuple[list[str], list[str]]:
        label_map = {
            "treasury_relevance": "Treasury / Hedging Relevance",
            "project_finance_exposure": "Project Finance Exposure",
            "debt_funding_refinancing": "Debt / Funding / Refinancing",
            "seniority": "Seniority Match",
            "tools_and_systems": "Tools & Systems",
            "location_relevance": "Location Fit",
        }

        strengths: list[str] = []
        gaps: list[str] = []
        for key, value in category_scores.items():
            label = label_map[key]
            if value >= 75:
                strengths.append(f"Strong {label} ({value}/100)")
            elif value < 50:
                gaps.append(f"Weak {label} ({value}/100)")

        if not strengths:
            strengths.append("No major strengths detected by rule-based screening")
        if not gaps:
            gaps.append("No critical gaps detected by rule-based screening")

        return strengths, gaps

    def _recommendation(self, score: int, parsed: ParsedJobSignals) -> str:
        flags = parsed["signal_flags"]

        # Hard exclusion first: junior roles are always skipped for this profile.
        if flags["junior"]:
            return "Skip"

        if score >= 80:
            return "Apply Now"
        if 70 <= score < 80:
            return "Consider"
        return "Skip"
