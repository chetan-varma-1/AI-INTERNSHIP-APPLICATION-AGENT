"""Tests for matching-agent coordination and citations."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.agents.job_retrieval_agent import JobRetrievalAgent
from app.agents.orchestrator import MatchingOrchestrator
from app.core.exceptions import ResourceAccessDeniedError
from app.models.user import User, UserProfile
from app.models.user_detail import UserDetail
from app.schemas.matching import MatchingProfile, MatchingRequest
from app.schemas.rag import InternshipJob, SearchResult


class FakeRetriever:
    """Deterministic retriever used by agent tests."""

    def __init__(self) -> None:
        self.query = ""

    def search(self, query: str, top_k: int) -> list[SearchResult]:
        self.query = query
        job = InternshipJob(
            title="Backend Intern",
            company="Example",
            description="Build APIs",
            skills_required=["Python"],
            location="Remote",
            apply_url="https://example.com/apply",
        )
        return [
            SearchResult(
                job_id="job-1",
                score=0.91,
                document=job.to_document_text(),
                metadata=job.to_metadata(),
                job=job,
            )
        ][:top_k]


class TestJobRetrievalAgent:
    """Semantic query and citation behavior."""

    @pytest.mark.asyncio
    async def test_returns_cited_matches_without_embedding_identity(self) -> None:
        retriever = FakeRetriever()
        agent = JobRetrievalAgent(retriever)  # type: ignore[arg-type]
        profile = MatchingProfile(
            user_id=uuid4(),
            name="Candidate",
            email="private@example.com",
            location_preference="Remote",
            skills=["Python"],
        )

        matches = await agent.retrieve(profile, top_k=5)

        assert matches[0].score == 0.91
        assert matches[0].citation.apply_url == "https://example.com/apply"
        assert matches[0].citation.vector_document_id == "job-1"
        assert "private@example.com" not in retriever.query


class TestMatchingOrchestrator:
    """Candidate profile resolution behavior."""

    @staticmethod
    def _user() -> User:
        user_id = uuid4()
        user = User(
            id=user_id,
            name="Candidate",
            email="candidate@example.com",
            password_hash="hash",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        user.profile = UserProfile(
            id=uuid4(),
            user_id=user_id,
            location_preference="Remote",
            skills=["Python"],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return user

    @pytest.mark.asyncio
    async def test_merges_profile_resume_and_request_data(self) -> None:
        user = self._user()
        detail = UserDetail(
            id=uuid4(),
            user_id=user.id,
            document_type="resume",
            file_name="resume.pdf",
            file_path="uploads/resume.pdf",
            education=[],
            skills=["FastAPI"],
            projects=[],
            experience=[],
            profile_summary="Backend developer",
            certifications=[],
            body_paragraphs=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        users = AsyncMock()
        users.get_by_id.return_value = user
        details = AsyncMock()
        details.get_by_id.return_value = detail
        retrieval = AsyncMock()
        retrieval.retrieve.return_value = []
        orchestrator = MatchingOrchestrator(users, details, retrieval)

        response = await orchestrator.match(
            user.id,
            MatchingRequest(user_detail_id=detail.id),
        )

        assert response.profile.skills == ["Python", "FastAPI"]
        assert response.profile.profile_summary == "Backend developer"
        retrieval.retrieve.assert_awaited_once_with(response.profile, 5)

    @pytest.mark.asyncio
    async def test_rejects_document_owned_by_another_user(self) -> None:
        user = self._user()
        users = AsyncMock()
        users.get_by_id.return_value = user
        details = AsyncMock()
        details.get_by_id.return_value = UserDetail(
            id=uuid4(),
            user_id=uuid4(),
            document_type="resume",
        )
        orchestrator = MatchingOrchestrator(users, details, AsyncMock())

        with pytest.raises(ResourceAccessDeniedError):
            await orchestrator.match(
                user.id,
                MatchingRequest(
                    user_detail_id=details.get_by_id.return_value.id,
                ),
            )
