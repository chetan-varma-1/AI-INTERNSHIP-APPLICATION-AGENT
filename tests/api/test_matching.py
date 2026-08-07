"""API tests for authenticated internship matching."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_matching_orchestrator, get_user_detail_service
from app.api.matching import router
from app.auth.dependencies import get_current_user
from app.core.config import Settings, get_settings
from app.schemas.auth import UserPublic
from app.schemas.matching import MatchingProfile, MatchingResponse
from app.schemas.user_detail import ParsedResumeResponse, ResumeData


class TestMatchingRoute:
    """Resume selection and authenticated ownership behavior."""

    @staticmethod
    def _response(user_id: UUID) -> MatchingResponse:
        return MatchingResponse(
            profile=MatchingProfile(
                user_id=user_id,
                name="Candidate",
                email="candidate@example.com",
            ),
            matches=[],
        )

    @staticmethod
    def _client(
        user_id: UUID,
        orchestrator: AsyncMock,
        detail_service: AsyncMock | None = None,
    ) -> TestClient:
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: UserPublic(
            id=user_id,
            name="Candidate",
            email="candidate@example.com",
        )
        app.dependency_overrides[get_matching_orchestrator] = lambda: orchestrator
        app.dependency_overrides[get_settings] = lambda: Settings(max_upload_size_mb=1)
        app.dependency_overrides[get_user_detail_service] = lambda: (
            detail_service if detail_service is not None else AsyncMock()
        )
        return TestClient(app)

    def test_matches_with_existing_user_detail_id(self) -> None:
        user_id = uuid4()
        detail_id = uuid4()
        orchestrator = AsyncMock()
        orchestrator.match.return_value = self._response(user_id)
        client = self._client(user_id, orchestrator)

        response = client.post("/matching", data={"user_detail_id": str(detail_id)})

        assert response.status_code == 200
        called_user_id, request = orchestrator.match.await_args.args
        assert called_user_id == user_id
        assert request.user_detail_id == detail_id

    def test_matches_without_resume_selection(self) -> None:
        user_id = uuid4()
        orchestrator = AsyncMock()
        orchestrator.match.return_value = self._response(user_id)
        client = self._client(user_id, orchestrator)

        response = client.post("/matching")

        assert response.status_code == 200
        _, request = orchestrator.match.await_args.args
        assert request.user_detail_id is None

    def test_rejects_invalid_user_detail_id(self) -> None:
        client = self._client(uuid4(), AsyncMock())

        response = client.post("/matching", data={"user_detail_id": "not-a-uuid"})

        assert response.status_code == 422
        assert response.json()["detail"] == "user_detail_id must be a valid UUID"

    def test_parses_uploaded_resume_then_matches(self) -> None:
        user_id = uuid4()
        detail_id = uuid4()
        now = datetime.now(UTC)
        detail_service = AsyncMock()
        detail_service.parse_resume.return_value = ParsedResumeResponse(
            id=detail_id,
            user_id=user_id,
            file_name="resume.pdf",
            file_path="uploads/resume.pdf",
            extracted=ResumeData(skills=["Python"]),
            created_at=now,
            updated_at=now,
        )
        orchestrator = AsyncMock()
        orchestrator.match.return_value = self._response(user_id)
        client = self._client(user_id, orchestrator, detail_service)

        response = client.post(
            "/matching",
            files={
                "file": (
                    "resume.pdf",
                    b"%PDF-1.4 resume bytes",
                    "application/pdf",
                )
            },
        )

        assert response.status_code == 200
        detail_service.parse_resume.assert_awaited_once_with(
            user_id,
            "resume.pdf",
            b"%PDF-1.4 resume bytes",
        )
        _, request = orchestrator.match.await_args.args
        assert request.user_detail_id == detail_id

    def test_rejects_file_and_user_detail_id_together(self) -> None:
        detail_service = AsyncMock()
        client = self._client(uuid4(), AsyncMock(), detail_service)

        response = client.post(
            "/matching",
            data={"user_detail_id": str(uuid4())},
            files={"file": ("resume.pdf", b"%PDF-1.4", "application/pdf")},
        )

        assert response.status_code == 422
        assert response.json()["detail"] == "Provide either user_detail_id or file, not both"
        detail_service.parse_resume.assert_not_awaited()
