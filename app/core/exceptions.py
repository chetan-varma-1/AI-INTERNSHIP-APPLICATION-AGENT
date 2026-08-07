"""Authentication domain exceptions."""


class AuthError(Exception):
    """Base authentication error."""


class EmailAlreadyRegisteredError(AuthError):
    """Raised when signup email already exists."""


class InvalidCredentialsError(AuthError):
    """Raised when login credentials are invalid."""


class UnauthorizedError(AuthError):
    """Raised when an access token is missing or invalid."""


class DocumentError(RuntimeError):
    """Base error for uploaded-document processing."""


class UnsupportedDocumentTypeError(DocumentError):
    """Raised when an uploaded file is not a PDF or DOCX."""


class DocumentTooLargeError(DocumentError):
    """Raised when an uploaded document exceeds the configured limit."""


class EmptyDocumentError(DocumentError):
    """Raised when no readable text can be extracted from a document."""


class InvalidDocumentError(DocumentError):
    """Raised when a PDF or DOCX file cannot be decoded."""


class DocumentParsingError(DocumentError):
    """Raised when structured extraction fails."""


class InvalidDocumentSelectionError(DocumentError):
    """Raised when a workflow receives the wrong document category."""


class ResourceNotFoundError(RuntimeError):
    """Raised when a requested domain record does not exist."""


class ResourceAccessDeniedError(RuntimeError):
    """Raised when a user attempts to access another user's record."""
