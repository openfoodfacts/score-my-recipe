"""HTTP API for recipes scoring.


Note: the business logic is in api/recipes.py,
this file should only handle the HTTP specific parts.
"""

from typing import Annotated

from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware

import api.recipes as recipes
import api.types as types

app = FastAPI(
    title="Score My Recipe",
    description="A tool to compute Green-Score of recipes.",
    version="0.1.0",
)


# Allow anyone to call the API from their own apps
app.add_middleware(
    CORSMiddleware,
    # FastAPI doc related to allow_origin (to avoid CORS issues):
    # "It's also possible to declare the list as "*" (a "wildcard") to say that all are allowed.
    # But that will only allow certain types of communication, excluding everything that involves
    # credentials: Cookies, Authorization headers like those used with Bearer Tokens, etc.
    # So, for everything to work correctly, it's better to specify explicitly the allowed origins."
    # => Workaround: use allow_origin_regex
    # Source: https://github.com/tiangolo/fastapi/issues/133#issuecomment-646985050
    allow_origin_regex="https?://.*",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/")
async def root() -> dict:
    return {"message": "Score My Recipe API"}


@app.get("/v1/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/parse_text")
async def parse_text(request: types.RecipeParseRequest) -> types.RecipeParseResponse:
    """Parse a text and return a list of ingredients with quantities and eventual modifiers"""
    ingredients = await recipes.parse_text(request.text, request.lang)
    return types.RecipeParseResponse(ingredients=ingredients)


@app.get("/v1/origins")
async def get_origins(
    filter_query: Annotated[types.OriginsRequest, Query()], response: Response
) -> types.OriginsResponse:
    """Get the list of origins available in the database

    Note: as the list is not too big, we let clients handle suggestions to users
    """
    origins = await recipes.get_origins(filter_query.lang)
    response.headers["Cache-Control"] = "max-age=86400"
    return types.OriginsResponse(origins=origins)


@app.get("/v1/labels")
async def get_labels(
    filter_query: Annotated[types.LabelsRequest, Query()], response: Response
) -> types.LabelsResponse:
    """Get the list of labels relevant for green-score computation
    """
    labels = await recipes.get_labels(filter_query.lang)
    response.headers["Cache-Control"] = "max-age=86400"
    return types.LabelsResponse(labels=labels)
