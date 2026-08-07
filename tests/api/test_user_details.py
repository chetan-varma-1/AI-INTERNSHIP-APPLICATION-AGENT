"""API tests for authenticated user document routes."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_user_detail_service
from app.api.user_details import router
from app.auth.dependencies import get_current_user
from app.core.config import Settings, get_settings
from app.schemas.auth import UserPublic
from app.schemas.user_detail import ParsedResumeResponse, ResumeData


class TestUserDetailRoutes:
    """Authorization and upload wiring for user document endpoints."""

    @staticmethod
    def _client(
        user_id: UUID,
        service: AsyncMock,
    ) -> TestClient:
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: UserPublic(
            id=user_id,
            name="Candidate",
            email="candidate@example.com",
        )
        app.dependency_overrides[get_settings] = lambda: Settings(max_upload_size_mb=1)
        app.dependency_overrides[get_user_detail_service] = lambda: service
        return TestClient(app)

    def test_lists_resumes_for_authenticated_user(self) -> None:
        user_id = uuid4()
        service = AsyncMock()
        service.list_resumes.return_value = []
        client = self._client(user_id, service)

        response = client.get("/resumes")

        assert response.status_code == 200
        service.list_resumes.assert_awaited_once_with(user_id)

    def test_parses_resume_multipart_upload(self) -> None:
        user_id = uuid4()
        service = AsyncMock()
        now = datetime.now(UTC)
        service.parse_resume.return_value = ParsedResumeResponse(
            id=uuid4(),
            user_id=user_id,
            file_name="resume.docx",
            file_path="uploads/resume.docx",
            extracted=ResumeData(skills=["Python"]),
            created_at=now,
            updated_at=now,
        )
        client = self._client(user_id, service)

        response = client.post(
            "/resumes/parse",
            files={
                "file": (
                    "resume.docx",
                    b"document bytes",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        assert response.status_code == 201
        assert response.json()["extracted"]["skills"] == ["Python"]
        service.parse_resume.assert_awaited_once_with(
            user_id,
            "resume.docx",
            b"document bytes",
        )
