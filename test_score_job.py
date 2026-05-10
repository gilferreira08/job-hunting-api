from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_score_job_endpoint_returns_expected_shape() -> None:
    payload = {
        "job_title": "Senior Treasury Manager",
        "company": "Example Company",
        "location": "Paris, France",
        "job_description": (
            "We are hiring a Senior Treasury Manager to lead hedging, liquidity management, "
            "funding strategy, refinancing initiatives and project finance support. "
            "The role requires DSCR analysis, Bloomberg usage and collaboration with France treasury teams."
        ),
    }

    response = client.post("/score-job", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert "score" in data
    assert "recommendation" in data
    assert isinstance(data.get("strengths"), list)
    assert isinstance(data.get("gaps"), list)
