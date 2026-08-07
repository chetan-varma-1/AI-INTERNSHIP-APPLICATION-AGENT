"""Agent for extracting structured resume content."""

from app.llm.client import StructuredExtractionClient
from app.schemas.user_detail import ResumeData

RESUME_EXTRACTION_INSTRUCTIONS = (
    "Extract education, skills, projects, work experience, a concise profile "
    "summary, and certifications from this resume."
)


class ResumeAgent:
    """Convert resume text into a validated structured profile."""

    def __init__(self, extraction_client: StructuredExtractionClient) -> None:
        self._extraction_client = extraction_client

    async def parse(self, text: str) -> ResumeData:
        """Extract structured resume fields."""
        return await self._extraction_client.extract(
            text,
            ResumeData,
            RESUME_EXTRACTION_INSTRUCTIONS,
        )
