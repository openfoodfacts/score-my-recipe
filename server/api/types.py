from typing import Annotated, Optional
from pydantic import Field, BaseModel


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


class RecipeParseResponse(BaseModel):
    """Response model for parse_text endpoint"""

    ingredients: list[RecipeIngredient]


class LangRequest(BaseModel):
    """Request model for parse_text endpoint"""

    lang: Annotated[str, Field(description="Language for the request (2 or 5 letter code)")]


class TaxonomyRequest(LangRequest):
    """Base request model for taxonomy endpoints (origins, labels, ingredients).

    Adds the option to request synonyms alongside the canonical label.
    """

    include_synonyms: Annotated[
        bool,
        Field(
            default=False,
            description="If true, include the synonyms of each item in the response.",
        ),
    ]


class OriginsRequest(TaxonomyRequest):
    pass  # No additional fields for now, but we keep the class for future extensions


class RecipeParseRequest(LangRequest):
    """Request model for parse_text endpoint"""

    text: str


class OriginsResponse(BaseModel):
    """Response model for get_origins endpoint"""

    origins: list[Origin]


class Label(TaxonomyItem):
    """Label model for Score My Recipe API"""


class LabelsRequest(TaxonomyRequest):
    pass


class LabelsResponse(BaseModel):
    """Response model for get_labels endpoint"""

    labels: list[Label]


class Ingredient(TaxonomyItem):
    """Ingredient model for Score My Recipe API"""


class IngredientsRequest(TaxonomyRequest):
    pass


class IngredientsResponse(BaseModel):
    """Response model for get_ingredients endpoint"""

    ingredients: list[Ingredient]
