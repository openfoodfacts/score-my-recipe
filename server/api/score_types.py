"""Per-ingredient metrics gathered during green-score computation."""

import enum
from typing import Optional

from pydantic import BaseModel, Field


# see https://docs.score-environnemental.com/methodologie-recette/bonus-malus-recette/systeme-de-production/labels
LABELS_BONUS = {
    "fr:nature-et-progres": 20,
    "fr:bio-coherence": 20,
    "en:demeter": 20,
    "fr:bio-equitable": 20,
    "en:eu-organic": 15,
    "fr:ab-agriculture-biologique": 15,
    # TODO: Needs verification.
    # it's there:
    # https://docs.score-environnemental.com/methodologie/produit/systeme-de-production/label
    # but not there:
    # https://docs.score-environnemental.com/methodologie-recette/bonus-malus-recette/systeme-de-production/labels
    "en:sustainable-fishing-method": 15,
    "fr:haute-valeur-environnementale": 10,
    "en:utz-certified": 10,
    "en:rainforest-alliance": 10,
    "en:fairtrade-international": 10,
    "fr:bleu-blanc-coeur": 10,
    "fr:label-rouge": 10,
    "en:sustainable-seafood-msc": 10,
    "en:responsible-aquaculture-asc": 10,
}


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
    labels_bonus: Optional[float] = Field(
        default=None,
        description="Bonus from ingredient labels",
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


#: Type alias for a list of per-ingredient metrics
RecipeMetrics = list[IngredientMetrics]
