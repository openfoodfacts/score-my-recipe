"""Tests for ``score.score_to_letter``.

The thresholds (and their boundaries) follow the green-score grading scale:
A+ (>=90), A (>=75), B (>=60), C (>=45), D (>=30), E (>=15), F otherwise.
"""

import pytest

from api import score

# (input_score, expected_letter) covering each threshold and its boundary.
LETTER_CASES = [
    (100, "A+"),
    (90, "A+"),
    (89.99, "A"),
    (75, "A"),
    (74.99, "B"),
    (60, "B"),
    (59.99, "C"),
    (45, "C"),
    (44.99, "D"),
    (30, "D"),
    (29.99, "E"),
    (15, "E"),
    (14.99, "F"),
    (0, "F"),
]


@pytest.mark.parametrize("score_value, expected", LETTER_CASES)
@pytest.mark.asyncio
async def test_score_to_letter_thresholds(score_value, expected):
    """Each score value maps to its expected letter grade."""
    assert await score.score_to_letter(score_value) == expected
