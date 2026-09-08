"""Per-ingredient metrics gathered during green-score computation.
"""
import enum
from typing import Optional

from pydantic import BaseModel, Field


class AccountedWeights(enum.StrEnum):
    """Accounted weights for the ponderated sum.

    * scorable takes the ratio of each ingredient compared to the total weight of ingredients that have an EF score
    * total takes the ratio of each ingredient compared to the total weight of all ingredients, including unmatched ones
    """
    ONLY_SCORABLE = "scorable"
    ALL_WEIGHTS = "total"


class IngredientMetrics(BaseModel):
    """Metrics gathered for a single ingredient during score computation

    Fields are filled incrementally by the score passes
    """

    id: str = Field(description="The frontend ingredient id")
    weight: float = Field(description="Weight in grams")
    ef_score: Optional[float] = Field(
        default=None,
        description="Per-kg EF score from Agribalyse (mPt/kg), None when the ingredient is missing",
    )
    ratio: Optional[float] = Field(
        default=None,
        description="Share of the ingredient weight in the chosen denominator "
        "(scorable weight or total recipe weight)",
    )
    missing: bool = Field(
        default=False,
        description="True when the ingredient has no usable Agribalyse EF score",
    )
