from jobs.connectors.indeed_connector import IndeedConnector


def test_indeed_connector_graceful_empty_results():
    connector = IndeedConnector()
    jobs = connector.search_jobs("Treasury Manager", "France", limit=2)
    assert jobs == []
    assert connector.last_diagnostic
