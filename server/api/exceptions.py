"""Domain-specific exceptions for the recipes business logic."""

from fastapi.exceptions import RequestValidationError


class UnknownUnitError(Exception):
    """Raised when a unit is neither the ``item`` sentinel nor a known taxonomy unit."""


class UnknownIngredientError(Exception):
    """Raised when an ingredient taxonomy id is not found in the ingredients taxonomy."""


class UnitConversionNotSupportedError(Exception):
    """Raised when the requested unit change cannot be computed yet.

    Covers unit changes that would require calling the Open Food Facts parse
    API (e.g. volume <-> mass, switching to a countable unit, or
    cross-multiplying from a zero old value).
    """


class CsvParseError(Exception):
    """Raised when pasted spreadsheet data cannot be turned into ingredients.

    Carries a translation message id and its ICU params, so the HTTP layer can
    return a translated 422 ``detail`` without the CSV logic depending on a
    language.
    """

    def __init__(self, message_id: str, params: dict | None = None):
        super().__init__(message_id)
        self.message_id = message_id
        self.params = params or {}


class AsyncRequestValidationError(RequestValidationError):
    """Custom exception to distinguish async validation errors from sync ones.

    This is used to return a 422 response with a different error message
    when the request body fails async validation (e.g. language code not supported).
    """
