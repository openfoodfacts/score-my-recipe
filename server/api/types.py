from typing import Annotated, Any, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class OFFIngredient(BaseModel):
    """Ingredient model for Open Food Facts API"""

    # TODO convert str to bool and is_in_taxonomy to bool
    id: str
    text: str
    quantity: Optional[str] = None
    quantity_g: Optional[float] = None
    ecobalyse_code: Optional[str] = None
    ciqual_food_code: Optional[str] = None
    is_in_taxonomy: Optional[int] = None


class RecipeIngredient(BaseModel):
    """Ingredient model for Score My Recipe API"""

    taxonomy_id: Optional[str] = None
    is_in_taxonomy: bool
    codified_ingredient: str
    quantity_g: Optional[float] = None


class TaxonomyItem(BaseModel):
    id: Annotated[str, Field(description="Taxonomy id of the item")]
    label: Annotated[str, Field(description="Name of the item")]


class Origin(TaxonomyItem):
    """Origin model for Score My Recipe API"""


class RecipeParseResponse(BaseModel):
    """Response model for parse_text endpoint"""

    ingredients: list[RecipeIngredient]


class LangRequest(BaseModel):
    """Request model for parse_text endpoint"""

    lang: Annotated[str, Field(description="Language for the request (2 or 5 letter code)")]


class OriginsRequest(LangRequest):
    pass  # No additional fields for now, but we keep the class for future extensions


class RecipeParseRequest(LangRequest):
    """Request model for parse_text endpoint"""

    text: str


class OriginsResponse(BaseModel):
    """Response model for get_origins endpoint"""

    origins: list[Origin]


class Label(TaxonomyItem):
    """Label model for Score My Recipe API"""


class LabelsRequest(LangRequest):
    pass


class LabelsResponse(BaseModel):
    """Response model for get_labels endpoint"""

    labels: list[Label]


class Ingredient(TaxonomyItem):
    """Ingredient model for Score My Recipe API"""


class IngredientsRequest(LangRequest):
    pass


class IngredientsResponse(BaseModel):
    """Response model for get_ingredients endpoint"""

    ingredients: list[Ingredient]


# --- Green-score computation -------------------------------------------------
#
# The following models mirror the frontend ingredient structures
# (see `frontend/src/lib/types/ingredient.ts`). They use camelCase aliases
# so the JSON accepted by the API matches what the SvelteKit frontend sends.


class CamelModel(BaseModel):
    """Base model exposing camelCase aliases (matching the frontend) in the OpenAPI schema."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TaxonomyItem(CamelModel):
    """A taxonomy reference with an id and a localized label.

    Mirrors the frontend `TaxonomyItem` (used for codified ingredients, labels
    and origins).
    """

    id: Annotated[str, Field(description="Taxonomy identifier")]
    label: Annotated[str, Field(description="Display label in the current language")]
    is_in_taxonomy: Annotated[
        bool, Field(description="Whether the item comes from the taxonomy (true) or is custom")
    ]


class RecipeIngredientInput(CamelModel):
    """A single ingredient of a recipe"""

    # TODO: decide if we keep id and name
    id: Annotated[str, Field(description="Unique identifier for the ingredient")]
    name: Annotated[str, Field(description="Display name of the ingredient")]
    weight: Annotated[float, Field(description="Weight in grams")]
    codified_ingredient: Annotated[
        TaxonomyItem,
        Field(description="Codified ingredient"),
    ]
    labels: Annotated[
        list[TaxonomyItem], Field(description="Labels / certifications (organic, fair-trade...)")
    ] = []
    seasonality: Annotated[bool, Field(description="Whether the ingredient is seasonal")] = False
    origin: Annotated[
        Optional[TaxonomyItem], Field(description="Origin country/region, null if unspecified")
    ] = None


RecipeInput = list[RecipeIngredientInput]


class GreenScoreRequest(CamelModel):
    """Request body for the green-score computation endpoint.

    It is a thin wrapper around a list of ingredients
    """

    ingredients: Annotated[RecipeInput, Field(description="The ingredients of the recipe")]


class IngredientAgribalyse(CamelModel):
    """Per-ingredient result of the green-score computation.

    For now only the Agribalyse lookup result is returned; the actual score
    fields will be added later.
    """

    id: Annotated[str, Field(description="The frontend ingredient id")]
    name: Annotated[str, Field(description="The ingredient display name")]
    matched_code: Annotated[
        Optional[str], Field(description="The code used to find the Agribalyse row, null if none")
    ] = None
    code_source: Annotated[
        Optional[str],
        Field(description="The taxonomy property that yielded the code, null if none"),
    ] = None
    agribalyse: Annotated[
        Optional[dict[str, Any]],
        Field(description="The matching Agribalyse row as a dict, null if not found"),
    ] = None


class GreenScoreResponse(CamelModel):
    """Response model for the green-score computation endpoint."""

    numeric_score: Annotated[
        Optional[float],
        Field(
            description="The computed green-score of the recipe, null if no ingredients have a score"
        ),
    ] = None
    letter_grade: Annotated[
        Optional[str],
        Field(
            description="The letter grade corresponding to the numeric score, null if no ingredients have a score"
        ),
    ] = None
    missing_ingredient_ids: Annotated[
        list[str],
        Field(
            description="List of ingredient ids that were missing from the Agribalyse computation"
        ),
    ] = []
