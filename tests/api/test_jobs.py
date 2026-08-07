"""API tests for authenticated job endpoints."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.jobs import router


class TestJobRouteAuthentication:
    """Verify job operations require an access-token cookie."""

    @staticmethod
    def _client() -> TestClient:
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_scrape_rejects_missing_access_token(self) -> None:
        response = self._client().post("/jobs/scrape")

        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}

    def test_list_rejects_missing_access_token(self) -> None:
        response = self._client().get("/jobs")

        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}
