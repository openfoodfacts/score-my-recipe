from fastapi import FastAPI
import api.recipes as recipes
import api.types as types

app = FastAPI(
    title="Score My Recipe",
    description="A tool to compute Green-Score of recipes.",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict:
    return {"message": "Score My Recipe API"}


@app.get("/v1/health")
async def health() -> dict:
    return {"status": "ok"}

# TODO: use a class for parameters to constraint values of lang
@app.post("/v1/parse_text")
async def parse_text(text: str, lang: str) -> types.RecipeParseResponse:
    """Parse a text and return a list of ingredients with quantities and eventual modifiers
    """
    ingredients = await recipes.parse_text(text, lang)
    return types.RecipeParseResponse(ingredients=ingredients)

