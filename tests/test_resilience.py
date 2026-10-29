
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
from api.main import app
import api.main as api_main


client = TestClient(app)


def test_recovery_endpoint_detects_unavailable_elasticsearch():
    original_failure_time = api_main.failure_detected_at

    try:
        api_main.failure_detected_at = None

        with patch.object(api_main.es, "ping", return_value=False):
            response = client.get("/recovery")

        assert response.status_code == 200
        data = response.json()
        assert data["current_status"] == "degraded"
        assert data["failure_active"] is True
        assert data["last_recovery_time_ms"] is None
    finally:
        api_main.failure_detected_at = original_failure_time


def test_recovery_endpoint_records_recovery():
    original_state = (
        api_main.failure_detected_at,
        api_main.last_recovery_time_ms,
        api_main.recovery_count,
    )

    try:
        api_main.failure_detected_at = (
            datetime.now(timezone.utc) - timedelta(seconds=2)
        )
        api_main.last_recovery_time_ms = None
        api_main.recovery_count = 0

        with patch.object(api_main.es, "ping", return_value=True):
            response = client.get("/recovery")

        assert response.status_code == 200
        data = response.json()
        assert data["current_status"] == "healthy"
        assert data["failure_active"] is False
        assert data["recovery_count"] == 1
        assert data["last_recovery_time_ms"] >= 1000
    finally:
        (
            api_main.failure_detected_at,
            api_main.last_recovery_time_ms,
            api_main.recovery_count,
        ) = original_state
