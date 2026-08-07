"""Resume, cover-letter, and profile-summary HTTP endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.dependencies import get_profile_service, get_user_detail_service
from app.auth.dependencies import get_current_user
from app.core.config import Settings, get_settings
from app.core.exceptions import (
    DocumentParsingError,
    DocumentTooLargeError,
    EmptyDocumentError,
    InvalidDocumentError,
    ResourceNotFoundError,
    UnsupportedDocumentTypeError,
)
from app.schemas.auth import UserPublic
from app.schemas.user_detail import (
    ParsedCoverLetterResponse,
    ParsedResumeResponse,
    ProfileSummaryResponse,
)
from app.services.profile_service import ProfileService
from app.services.user_detail_service import UserDetailService

router = APIRouter(tags=["user documents"])


async def _read_upload(file: UploadFile, settings: Settings) -> bytes:
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    try:
        return await file.read(max_bytes + 1)
    finally:
        await file.close()


def _raise_document_http_error(exc: Exception) -> None:
    if isinstance(exc, DocumentTooLargeError):
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(exc))
    if isinstance(exc, UnsupportedDocumentTypeError):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        )
    if isinstance(exc, (EmptyDocumentError, InvalidDocumentError)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )
    if isinstance(exc, DocumentParsingError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    raise exc


@router.post(
    "/resumes/parse",
    response_model=ParsedResumeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def parse_resume(
    file: UploadFile,
    current_user: UserPublic = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    service: UserDetailService = Depends(get_user_detail_service),
) -> ParsedResumeResponse:
    """Parse and save an authenticated user's PDF or DOCX resume."""
    file_name = file.filename or ""
    content = await _read_upload(file, settings)
    try:
        return await service.parse_resume(current_user.id, file_name, content)
    except (
        DocumentParsingError,
        DocumentTooLargeError,
        EmptyDocumentError,
        InvalidDocumentError,
        UnsupportedDocumentTypeError,
    ) as exc:
        _raise_document_http_error(exc)
        raise AssertionError("unreachable")


@router.get("/resumes", response_model=list[ParsedResumeResponse])
async def list_resumes(
    current_user: UserPublic = Depends(get_current_user),
    service: UserDetailService = Depends(get_user_detail_service),
) -> list[ParsedResumeResponse]:
    """List the authenticated user's parsed resumes."""
    return await service.list_resumes(current_user.id)


@router.post(
    "/cover-letters/parse",
    response_model=ParsedCoverLetterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def parse_cover_letter(
    file: UploadFile,
    current_user: UserPublic = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    service: UserDetailService = Depends(get_user_detail_service),
) -> ParsedCoverLetterResponse:
    """Parse and save an authenticated user's PDF or DOCX cover letter."""
    file_name = file.filename or ""
    content = await _read_upload(file, settings)
    try:
        return await service.parse_cover_letter(current_user.id, file_name, content)
    except (
        DocumentParsingError,
        DocumentTooLargeError,
        EmptyDocumentError,
        InvalidDocumentError,
        UnsupportedDocumentTypeError,
    ) as exc:
        _raise_document_http_error(exc)
        raise AssertionError("unreachable")


@router.get(
    "/cover-letters",
    response_model=list[ParsedCoverLetterResponse],
)
async def list_cover_letters(
    current_user: UserPublic = Depends(get_current_user),
    service: UserDetailService = Depends(get_user_detail_service),
) -> list[ParsedCoverLetterResponse]:
    """List the authenticated user's parsed cover letters."""
    return await service.list_cover_letters(current_user.id)


@router.post("/profile-summary", response_model=ProfileSummaryResponse)
async def create_profile_summary(
    current_user: UserPublic = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileSummaryResponse:
    """Create a matching-ready summary from user and profile data."""
    try:
        return await service.create_summary(current_user.id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
