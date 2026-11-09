"""Types useful for green-score computation."""

import enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    import api.types


@dataclass(frozen=True)
class NoteRef:
    """A language-agnostic reference to a note.

    Holds the message ``id`` (a key in ``server/i18n/*.json``, e.g. ``"notes.epi.no_origin"``) and its ICU ``params``.
    The translated template and the rendered message are resolved at the API boundary (see :func:`api.i18n.translate`),
    so the computation code never depends on a language.
    """

    id: str
    params: dict[str, Any] = field(default_factory=dict)


class AccountedWeights(enum.StrEnum):
    """Accounted weights for the ponderated sum.

    * scorable takes the ratio of each ingredient compared to the total weight of ingredients that have an EF score
    * total takes the ratio of each ingredient compared to the total weight of all ingredients, including unmatched ones
    """

    ONLY_SCORABLE = "scorable"
    ALL_WEIGHTS = "total"


class NotesMixin(BaseModel):
    """Mixin for models that can have notes."""

    notes: Optional[list[NoteRef]] = Field(
        default=None,
        description="Optional notes about computation specifics",
    )

    def add_note(self, note_id: str, **params: Any) -> None:
        """Add a note referenced by its message ``id`` and ICU ``params``.

        Example: ``add_note("notes.epi.not_found", origin="en:france")``.
        """
        note = NoteRef(id=note_id, params=params)
        if self.notes is None:
            self.notes = [note]
        else:
            self.notes.append(note)


class IngredientMetrics(NotesMixin):
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
    epi_modifier: Optional[float] = Field(
        default=None,
        description="Modifier from ingredient origin agricultural system (EPI)",
    )
    distance_modifier: Optional[float] = Field(
        default=None,
        description="Modifier from ingredient origin distance to recipe country",
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


class RecipeMetrics(NotesMixin):
    """Metrics gathered for a recipe during green-score computation.

    Wraps the per-ingredient :class:`IngredientMetrics` computed by the score
    passes. The ``metrics`` list is filled by :func:`api.score.gather_ef_metrics`
    then mutated in place by the subsequent passes (ratios, labels, EPI and
    distance modifiers), so each :class:`IngredientMetrics` stays the single
    source of truth for its ingredient.
    """

    metrics: list[IngredientMetrics] = Field(
        default_factory=list,
        description="Per-ingredient metrics, one entry per recipe ingredient",
    )

    @property
    def ingredients_notes(self):
        """Return a dictionary of all notes from the ingredients metrics
        keyed by ingredient id.
        """
        return {metric.id: metric.notes for metric in self.metrics if metric.notes}


@dataclass(frozen=True)
class GreenScoreResult:
    """Language-agnostic result of the green-score computation.

    Holds the same fields as :class:`api.types.GreenScoreResponse`, except the notes, which stay as :class:`NoteRef`,
    so that translation happens at the API boundary (see :func:`api.api.green_score`).
    """

    global_ef_score: Optional[float]
    labels_bonus: Optional[float]
    epi_modifier: Optional[float]
    distances_modifier: Optional[float]
    seasonality_modifier: Optional[float]
    numeric_score: Optional[float]
    letter_grade: Optional[str]
    missing_ingredient_ids: list[str]
    notes: Optional[list[NoteRef]] = None
    ingredients_notes: Optional[dict[str, list[NoteRef]]] = field(default=None)


@dataclass(frozen=True)
class IngredientWithNotes:
    """A parsed recipe ingredient and its language-agnostic notes.

    ``recipes.off_ingredient_to_recipe_ingredient`` builds the public :class:`api.types.RecipeIngredient` without notes;
    the notes are kept here as :class:`NoteRef`, so the API boundary can translate them.
    """

    ingredient: "api.types.RecipeIngredient"
    notes: list[NoteRef]
