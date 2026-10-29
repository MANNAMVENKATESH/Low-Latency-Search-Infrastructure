
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["elasticsearch"] in ["connected", "unreachable"]


def test_status_endpoint():
    response = client.get("/status")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "green"
    assert data["number_of_nodes"] >= 1
    assert "active_primary_shards" in data


def test_search_endpoint():
    response = client.get(
        "/search",
        params={"q": "laptop for students", "size": 5}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["count"] > 0
    assert data["count"] == len(data["results"])
    assert len(data["results"]) <= 5

    first_result = data["results"][0]
    assert "id" in first_result
    assert "title" in first_result
    assert "rank" in first_result


def test_search_missing_query():
    response = client.get("/search")

    assert response.status_code == 422


def test_metrics_endpoint():
    response = client.get("/metrics")

    assert response.status_code == 200
    data = response.json()
    assert data["index"] == "products"
    assert data["documents"] >= 1
    assert data["elasticsearch"] == "connected"
