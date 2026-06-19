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

class Origin(BaseModel):
    """Origin model for Score My Recipe API"""
    id: Annotated[str, Field(description="Taxonomy id of the origin")]
    label: Annotated[str, Field(description="Name of the origin")]

class RecipeParseResponse(BaseModel):
    """Response model for parse_text endpoint"""
    ingredients: list[RecipeIngredient]


class LangRequest(BaseModel):
    """Request model for parse_text endpoint"""
    lang: Annotated[str, Field(description="Language for the request (2 or 5 letter code)")]

class OriginsRequest(LangRequest, BaseModel):
    pass  # No additional fields for now, but we keep the class for future extensions

class RecipeParseRequest(LangRequest, BaseModel):
    """Request model for parse_text endpoint"""
    text: str

class OriginsResponse(BaseModel):
    """Response model for get_origins endpoint"""
    origins: list[Origin]