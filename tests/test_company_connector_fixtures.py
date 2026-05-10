from pathlib import Path

from jobs.connectors.company_careers_connector import CompanyCareersConnector


def test_company_connector_fixture_parsing_and_filtering() -> None:
    fixture_path = Path("tests/fixtures/company_careers_sample.html")
    html = fixture_path.read_text(encoding="utf-8")

    connector = CompanyCareersConnector(
        company_name="Sample Energy Co",
        careers_url="https://careers.sample-energy.com/",
    )

    parsed = connector.parse_jobs_from_html(
        html=html,
        base_url=connector.careers_url,
        query="",
        location="France",
        limit=20,
    )

    titles = [job["title"] for job in parsed]

    assert any("Treasury Manager" in title for title in titles)
    assert any("Funding Analyst" in title for title in titles)
    assert any("Project Finance Manager" in title for title in titles)
    assert any("Cash Management Specialist" in title for title in titles)

    assert not any("Accounting Assistant" in title for title in titles)
    assert not any("HR Business Partner" in title for title in titles)

    normalized = [connector.normalize_job(job) for job in parsed]
    assert normalized, "Expected at least one normalized job"

    for job in normalized:
        assert "job_title" in job
        assert "company" in job
        assert "location" in job
        assert "source" in job
        assert "job_description" in job
        assert "url" in job
