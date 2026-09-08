from typing import Annotated, Any, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

import api.score_types as score_types


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

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "taxonomy_id": "en:apple",
                    "is_in_taxonomy": True,
                    "codified_ingredient": "apple",
                    "quantity_g": 150.0,
                }
            ]
        }
    )

    taxonomy_id: Optional[str] = None
    is_in_taxonomy: bool
    codified_ingredient: str
    quantity_g: Optional[float] = None


class TaxonomyItem(BaseModel):
    """A taxonomy reference with an id and a localized label.

    Mirrors the frontend `TaxonomyItem` (used for codified ingredients, labels
    and origins).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"id": "en:apple", "label": "Apple", "synonyms": ["apples", "pommes"]}]
        }
    )

    id: Annotated[str, Field(description="Taxonomy id of the item")]
    label: Annotated[str, Field(description="Name of the item")]
    synonyms: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Synonyms in the requested language. "
            "Only present in the response when include_synonyms is true.",
        ),
    ]


class Origin(TaxonomyItem):
    """Origin model for Score My Recipe API"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"id": "en:france", "label": "France", "synonyms": ["french"]}]
        }
    )


class RecipeParseResponse(BaseModel):
    """Response model for parse_text endpoint"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "ingredients": [
                        {
                            "taxonomy_id": "en:apple",
                            "is_in_taxonomy": True,
                            "codified_ingredient": "apple",
                            "quantity_g": 150.0,
                        },
                        {
                            "taxonomy_id": "en:wheat-flour",
                            "is_in_taxonomy": True,
                            "codified_ingredient": "wheat flour",
                            "quantity_g": 200.0,
                        },
                    ]
                }
            ]
        }
    )

    ingredients: list[RecipeIngredient]


class LangRequest(BaseModel):
    """Request model for parse_text endpoint"""

    model_config = ConfigDict(json_schema_extra={"examples": [{"lang": "en"}]})

    lang: Annotated[str, Field(description="Language for the request (2 or 5 letter code)")]


class TaxonomyRequest(LangRequest):
    """Base request model for taxonomy endpoints (origins, labels, ingredients).

    Adds the option to request synonyms alongside the canonical label.
    """

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"lang": "en", "include_synonyms": False}]}
    )

    include_synonyms: Annotated[
        bool,
        Field(
            default=False,
            description="If true, include the synonyms of each item in the response.",
        ),
    ]


class OriginsRequest(TaxonomyRequest):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"lang": "en", "include_synonyms": True}]}
    )
    pass  # No additional fields for now, but we keep the class for future extensions


class RecipeParseRequest(LangRequest):
    """Request model for parse_text endpoint"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"lang": "en", "text": "200g of apple, 1 cup of wheat flour"}]
        }
    )

    text: str


class OriginsResponse(BaseModel):
    """Response model for get_origins endpoint"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "origins": [
                        {"id": "en:france", "label": "France", "synonyms": ["french"]},
                        {"id": "en:spain", "label": "Spain", "synonyms": ["spanish"]},
                    ]
                }
            ]
        }
    )

    origins: list[Origin]


class Label(TaxonomyItem):
    """Label model for Score My Recipe API"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"id": "en:eu-organic", "label": "EU Organic", "synonyms": ["bio"]}]
        }
    )


class LabelsRequest(TaxonomyRequest):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"lang": "en", "include_synonyms": False}]}
    )
    pass


class LabelsResponse(BaseModel):
    """Response model for get_labels endpoint"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "labels": [
                        {"id": "en:eu-organic", "label": "EU Organic"},
                        {"id": "en:fair-trade", "label": "Fair Trade"},
                    ]
                }
            ]
        }
    )

    labels: list[Label]


class Ingredient(TaxonomyItem):
    """Ingredient model for Score My Recipe API"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"id": "en:apple", "label": "Apple", "synonyms": ["apples"]}]
        }
    )


class IngredientsRequest(TaxonomyRequest):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"lang": "en", "include_synonyms": True}]}
    )
    pass


class IngredientsResponse(BaseModel):
    """Response model for get_ingredients endpoint"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "ingredients": [
                        {"id": "en:apple", "label": "Apple"},
                        {"id": "en:wheat-flour", "label": "Wheat flour"},
                    ]
                }
            ]
        }
    )

    ingredients: list[Ingredient]


class ScoredIngredient(Ingredient):
    """An ingredient alternative with its matching Agribalyse row code.

    Mirrors the ``Ingredient`` structure (so it can be presented to the user just
    like the ``get_ingredients`` results) and adds the Agribalyse row code that
    the suggestion resolves to. Exposes camelCase aliases (matching the frontend
    convention) for multi-word fields.
    """

    model_config = ConfigDict()

    agribalyse_code: Annotated[
        str,
        Field(description="The Agribalyse row code (row identity) matching this ingredient"),
    ]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {"id": "en:apple", "label": "Apple", "agribalyse_code": "10001"},
                {"id": "en:wheat-flour", "label": "Wheat flour", "agribalyseCode": "10602"},
            ]
        },
    )


class SuggestScoredIngredientRequest(TaxonomyRequest):
    """Request model for the suggest-scored-ingredient endpoint."""

    taxonomy_id: Annotated[
        str,
        Field(description="Taxonomy id of the ingredient to find alternatives for"),
    ]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"lang": "en", "include_synonyms": False, "taxonomy_id": "en:meat"}]
        }
    )


class SuggestScoredIngredientResponse(BaseModel):
    """Response model for the suggest-scored-ingredient endpoint."""

    ingredients: list[ScoredIngredient]


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

    # json_schema_extra is merged with the inherited CamelModel config
    # (alias_generator + populate_by_name are preserved).
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"id": "en:apple", "label": "Apple", "isInTaxonomy": True}]}
    )

    id: Annotated[str, Field(description="Taxonomy identifier")]
    label: Annotated[str, Field(description="Display label in the current language")]
    is_in_taxonomy: Annotated[
        bool, Field(description="Whether the item comes from the taxonomy (true) or is custom")
    ]


class RecipeIngredientInput(CamelModel):
    """A single ingredient of a recipe"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "i1",
                    "name": "apple",
                    "weight": 150,
                    "codifiedIngredient": {
                        "id": "en:apple",
                        "label": "Apple",
                        "isInTaxonomy": True,
                    },
                    "labels": [
                        {
                            "id": "en:eu-organic",
                            "label": "EU Organic",
                            "isInTaxonomy": True,
                        }
                    ],
                    "seasonality": False,
                    "origin": {
                        "id": "en:france",
                        "label": "France",
                        "isInTaxonomy": True,
                    },
                }
            ]
        }
    )

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

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "ingredients": [
                        {
                            "id": "i1",
                            "name": "apple",
                            "weight": 150,
                            "codifiedIngredient": {
                                "id": "en:apple",
                                "label": "Apple",
                                "isInTaxonomy": True,
                            },
                            "labels": [],
                            "seasonality": False,
                            "origin": None,
                        },
                        {
                            "id": "i2",
                            "name": "wheat flour",
                            "weight": 200,
                            "codifiedIngredient": {
                                "id": "en:wheat-flour",
                                "label": "Wheat flour",
                                "isInTaxonomy": True,
                            },
                            "labels": [],
                            "seasonality": False,
                            "origin": None,
                        },
                    ]
                }
            ]
        }
    )

    ingredients: Annotated[RecipeInput, Field(description="The ingredients of the recipe")]

    accounted_weights: Annotated[
        score_types.AccountedWeights,
        Field(
            default=score_types.AccountedWeights.ONLY_SCORABLE,
            description=score_types.AccountedWeights.__doc__,
        ),
    ] = score_types.AccountedWeights.ONLY_SCORABLE


class IngredientAgribalyse(CamelModel):
    """Per-ingredient result of the green-score computation.

    For now only the Agribalyse lookup result is returned; the actual score
    fields will be added later.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "i1",
                    "name": "apple",
                    "matchedCode": "10001",
                    "codeSource": "agribalyse_food_code",
                    "agribalyse": {
                        "code": "10001",
                        "ciqual_code": "20001",
                        "name_fr": "Apple",
                        "score": 0.3,
                    },
                }
            ]
        }
    )

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

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "numericScore": 76.38,
                    "letterGrade": "A",
                    "missingIngredientIds": [],
                }
            ]
        }
    )

    global_ef_score: Annotated[
        Optional[float],
        Field(
            description="The computed global EF score of the recipe, null if no ingredients have a score"
        ),
    ] = None
    labels_bonus: Annotated[
        Optional[float],
        Field(
            description="The bonus from ingredient labels, null if no ingredients have a score, 0 if no labels"
        ),
    ] = None
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
