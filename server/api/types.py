from typing import Optional
from pydantic import BaseModel


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


class RecipeParseResponse(BaseModel):
    """Response model for parse_text endpoint"""
    ingredients: list[RecipeIngredient]


class RecipeParseRequest(BaseModel):
    """Request model for parse_text endpoint"""
    text: str
    lang: str