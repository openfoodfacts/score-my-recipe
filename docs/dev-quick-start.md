# Developer Quick Start

This guide explains how to set up and run the **Score My Recipe** API locally.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager and project runner

Install `uv` if you don't have it yet:

```bash
pip install uv
# or follow the official instructions at https://docs.astral.sh/uv/getting-started/installation/
```

## Install dependencies

From the project root, run:

```bash
uv sync
```

This creates a virtual environment in `.venv` and installs all dependencies declared in `pyproject.toml`.

## Run the API

```bash
uv run uvicorn api.api:app --reload
```

The API will be available at <http://localhost:8000>.

Interactive docs (Swagger UI) are at <http://localhost:8000/docs>.

## Available endpoints

| Method | Path      | Description          |
|--------|-----------|----------------------|
| GET    | `/`       | Welcome message      |
| GET    | `/health` | Health check         |
