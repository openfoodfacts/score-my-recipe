"""Domain-specific exceptions for the recipes business logic."""

import api.types as types


class UnknownUnitError(Exception):
    f"""Raised when a unit is neither the ``{types.ITEM_UNIT}`` sentinel nor a known taxonomy unit."""


class UnitConversionNotSupportedError(Exception):
    """Raised when the requested unit change cannot be computed yet.

    Covers unit changes that would require calling the Open Food Facts parse
    API (e.g. volume <-> mass, switching to a countable unit, or
    cross-multiplying from a zero old value).
    """
