"""AI insights generator that complements deterministic scoring.

Deterministic responsibilities (parser + scorer):
- Extract objective signals and compute reproducible fit score.
- Produce recommendation based on fixed rules.

AI responsibilities (this module):
- Convert structured outputs into concise executive guidance.
- Provide qualitative strategy suggestions without overriding score logic.
"""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI


class JobInsightsGenerator:
    """Generate finance-oriented narrative insights from deterministic outputs."""

    def __init__(self, model: str = "gpt-4.1-mini") -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def is_enabled(self) -> bool:
        return self.client is not None

    def generate_insights(
        self,
        *,
        parsed_signals: dict[str, Any],
        score: int,
        strengths: list[str],
        gaps: list[str],
        recommendation: str,
    ) -> dict[str, str] | None:
        if not self.client:
            return None

        system_prompt = (
            "You are a senior finance career advisor for Treasury, Funding, Liquidity, "
            "Project Finance and Risk roles. Use a professional executive tone. "
            "Do not change the deterministic score or recommendation. "
            "Your role is to provide concise strategic guidance that complements the rule-based engine."
        )

        user_prompt = f"""
Structured deterministic output:
- Score: {score}
- Recommendation: {recommendation}
- Strengths: {strengths}
- Gaps: {gaps}
- Parsed signals: {parsed_signals}

Return JSON with keys:
- executive_summary
- strategic_fit_analysis
- main_strengths
- main_risks_gaps
- application_strategy_advice

Keep each field concise (2-4 sentences), practical, and finance-oriented.
"""

        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text={"format": {"type": "json_object"}},
        )

        if not response.output_text:
            return None

        # The response is constrained to JSON, so parsing is deterministic here.
        import json

        data = json.loads(response.output_text)
        return {
            "executive_summary": str(data.get("executive_summary", "")),
            "strategic_fit_analysis": str(data.get("strategic_fit_analysis", "")),
            "main_strengths": str(data.get("main_strengths", "")),
            "main_risks_gaps": str(data.get("main_risks_gaps", "")),
            "application_strategy_advice": str(data.get("application_strategy_advice", "")),
        }
