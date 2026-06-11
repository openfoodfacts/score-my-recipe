# Agent Guide —  Score my recipe backend

---


## Projects instructions

Ensure you read the [global AGENTS.md](../AGENTS.md),
those file add specific instruction for the backend part.

## Bootstrap

Run these commands in order every time you start work in a fresh environment:

```bash
cd server  # if you start from the project folder
pip install uv
uv sync
```

---

## Key Commands

| Command       | Purpose                                     | Approx. time       |
| ------------- | ------------------------------------------- | ------------------ |
| `uv run uvicorn api.api.app --reload`       | Start server |  |
| `uv run pytest tests -v` | Run tests | ~20s        |

> External API calls to OpenFoodFacts will fail in sandboxed environments — this is expected. Focus on UI and code correctness.

---

## Pre-PR Validation (mandatory)

Before opening any pull request, run all of the following and fix every error:

```bash
uv run pytest tests -v
```

No PR should be opened with errors.

---

## Source Structure

```text
api/                  # API related code
tests/                # tests (using pytest)
```

---

## Coding style

Always add a meaningful doc string to functions, modules, etc.

Add comments for complex part or to justify non intuitive choices, or to summarize long code chunks (so that reader can quickly get an overview of the code). Still try not to be too verbose (find the right balance). If you use advance features (that not many programers might now), add a link to the documentation in the comment.

Try to make the code as clear as possible, by normalizing cases before processing, using the single responsibility pattern.

We try to use the frameworks at their best to have easy to read, semantic code. Especially Pydantic / FastAPI / pytest.
---

## Always add tests

Always add tests to the code you generate.
Think about edge cases.

Still try to keep the tests easy to maintain. As for code, add comments to help reader (see coding style).
