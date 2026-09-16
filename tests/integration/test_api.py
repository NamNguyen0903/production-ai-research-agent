from fastapi.testclient import TestClient

from app.agent.graph import build_research_graph
from app.agent.nodes.planner import mock_planner_node
from app.main import create_app


def create_test_client() -> TestClient:
    graph = build_research_graph(mock_planner_node)

    app = create_app(graph=graph)

    return TestClient(app)


def test_health_endpoint():
    with create_test_client() as client:
        response = client.get("/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"


def test_research_endpoint():
    with create_test_client() as client:
        response = client.post(
            "/v1/research",
            json={"query": ("Research the current landscape of small language models")},
        )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "completed"

    assert body["query"] == ("Research the current landscape of small language models")

    assert len(body["plan"]) >= 2

    assert body["answer"] is not None

    assert body["metrics"]["iterations"] == 1


def test_research_endpoint_rejects_short_query():
    with create_test_client() as client:
        response = client.post(
            "/v1/research",
            json={"query": "a"},
        )

    assert response.status_code == 422
