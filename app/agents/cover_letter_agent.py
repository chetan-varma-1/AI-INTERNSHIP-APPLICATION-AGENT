"""Agent for extracting structured cover-letter content."""

from app.llm.client import StructuredExtractionClient
from app.schemas.user_detail import CoverLetterData

COVER_LETTER_EXTRACTION_INSTRUCTIONS = (
    "Extract the applicant contact details, letter date, hiring manager, company, "
    "job title, salutation, opening, body paragraphs, motivation for this company, "
    "closing paragraph, and signature from this cover letter."
)


class CoverLetterAgent:
    """Convert cover-letter text into validated structured data."""

    def __init__(self, extraction_client: StructuredExtractionClient) -> None:
        self._extraction_client = extraction_client

    async def parse(self, text: str) -> CoverLetterData:
        """Extract structured cover-letter fields."""
        return await self._extraction_client.extract(
            text,
            CoverLetterData,
            COVER_LETTER_EXTRACTION_INSTRUCTIONS,
        )
