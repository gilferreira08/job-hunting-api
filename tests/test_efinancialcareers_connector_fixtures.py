from pathlib import Path

from jobs.connectors.efinancialcareers_connector import EFinancialCareersConnector


def test_efinancialcareers_fixture_parsing_and_filtering() -> None:
    html = Path("tests/fixtures/efinancialcareers_sample.html").read_text(encoding="utf-8")

    connector = EFinancialCareersConnector()
    parsed = connector.parse_jobs_from_html(
        html=html,
        base_url="https://www.efinancialcareers.com",
        query="",
        location="France",
        limit=20,
    )

    titles = [job["title"] for job in parsed]

    assert any("Treasury Manager" in title for title in titles)
    assert any("Funding Manager" in title for title in titles)
    assert any("Project Finance Associate" in title for title in titles)
    assert any("Structured Finance Analyst" in title for title in titles)
    assert any("ALM Liquidity Manager" in title for title in titles)

    assert not any("Junior Accountant" in title for title in titles)
    assert not any("Audit Intern" in title for title in titles)
    assert not any("Back Office Analyst" in title for title in titles)

    normalized = [connector.normalize_job(job) for job in parsed]
    assert normalized
    for job in normalized:
        assert "job_title" in job
        assert "company" in job
        assert "location" in job
        assert "source" in job
        assert "job_description" in job
        assert "url" in job
