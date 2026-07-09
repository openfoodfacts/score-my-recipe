"""Shared pytest fixtures for the green-score test suite."""

import pytest

from api import agribalyse


@pytest.fixture
def agribalyse_index():
    """Pre-populate the Agribalyse lookup tables with sample rows, reset afterwards.

    Each row carries an ``ef_score`` (mPt/kg) so the EF-score computation can be
    exercised. ``Carrot`` is only reachable through the Ciqual column to mirror
    the fallback code path.
    """
    by_code = {
        "10001": {"code": "10001", "ciqual_code": "20001", "name_fr": "Apple", "ef_score": 0.3},
        "10002": {"code": "10002", "ciqual_code": "20002", "name_fr": "Pear", "ef_score": 0.5},
    }
    by_ciqual = {
        "20001": by_code["10001"],
        "20002": by_code["10002"],
        "30000": {"code": "10003", "ciqual_code": "30000", "name_fr": "Carrot", "ef_score": 0.2},
    }
    saved = (agribalyse._agribalyse_by_code, agribalyse._agribalyse_by_ciqual)
    agribalyse._agribalyse_by_code = by_code
    agribalyse._agribalyse_by_ciqual = by_ciqual
    yield by_code, by_ciqual
    agribalyse._agribalyse_by_code, agribalyse._agribalyse_by_ciqual = saved
