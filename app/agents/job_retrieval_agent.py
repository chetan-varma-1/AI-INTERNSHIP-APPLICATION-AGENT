"""Agent for retrieving internships from the RAG index."""

from __future__ import annotations

import asyncio
import json

from app.rag.retriever import InternshipRetriever
from app.schemas.matching import JobMatch, MatchCitation, MatchingProfile


class JobRetrievalAgent:
    """Build a profile query and retrieve ranked internship matches."""

    def __init__(self, retriever: InternshipRetriever) -> None:
        self._retriever = retriever

    async def retrieve(self, profile: MatchingProfile, top_k: int) -> list[JobMatch]:
        """Return relevant internships with source citations."""
        query = self._build_query(profile)
        results = await asyncio.to_thread(self._retriever.search, query, top_k)
        return [
            JobMatch(
                score=result.score,
                job=result.job,
                citation=MatchCitation(
                    source=result.metadata.get("source", "unknown"),
                    apply_url=result.metadata.get("apply_url", ""),
                    vector_document_id=result.job_id,
                ),
            )
            for result in results
        ]

    @staticmethod
    def _build_query(profile: MatchingProfile) -> str:
        matching_context = {
            "preferred_location": profile.location_preference,
            "skills": profile.skills,
            "education": profile.education,
            "projects": profile.projects,
            "experience": profile.experience,
            "profile_summary": profile.profile_summary,
            "certifications": profile.certifications,
        }
        return (
            "Find internships that best match this candidate profile:\n"
            f"{json.dumps(matching_context, ensure_ascii=False)}"
        )
