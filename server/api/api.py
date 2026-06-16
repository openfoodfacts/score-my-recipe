from fastapi import FastAPI
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
    # => Workarround: use allow_origin_regex
    # Source: https://github.com/tiangolo/fastapi/issues/133#issuecomment-646985050
    allow_origin_regex="https?://.*",
    allow_credentials=True,
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

# TODO: use a class for parameters to constraint values of lang
@app.get("/v1/parse_text")
async def parse_text(text: str, lang: str) -> types.RecipeParseResponse:
    """Parse a text and return a list of ingredients with quantities and eventual modifiers
    """
    ingredients = await recipes.parse_text(text, lang)
    return types.RecipeParseResponse(ingredients=ingredients)

