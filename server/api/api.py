from fastapi import FastAPI

app = FastAPI(
    title="Score My Recipe",
    description="A tool to compute Green-Score of recipes.",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict:
    return {"message": "Score My Recipe API"}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
