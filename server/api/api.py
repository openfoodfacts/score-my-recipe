import httpx
from fastapi import FastAPI, HTTPException

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


@app.get("/v1/autocomplete/origins")
async def autocomplete_origins(term: str, lc: str) -> dict:
    params = {"tagtype": "origins", "term": term, "lc": lc, "limit": 300}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://world.openfoodfacts.org/cgi/suggest.pl",
                params=params,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Open Food Facts API unavailable") from exc

    return response.json()
