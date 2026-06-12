# Developer Quick Start

This guide explains how to set up and run the **Score My Recipe** API locally.

## One-liner setup (Linux & macOS)

If you prefer an automated setup, run the dev setup script from the repository root:

```bash
./scripts/dev-setup.sh
```

It will install all prerequisites and dependencies for both backend and frontend.
If you prefer to do things manually, follow the steps below.

## Backend

### Backend prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager and project runner

Install `uv` if you don't have it yet:

```bash
pip install uv
# or follow the official instructions at https://docs.astral.sh/uv/getting-started/installation/
```

### Install backend dependencies

From the project root, run:

```bash
cd server
uv sync
```

This creates a virtual environment in `server/.venv` and installs all dependencies declared in `server/pyproject.toml`.

### Run the API

```bash
cd server
uv run uvicorn api.api:app --reload
```

The API will be available at <http://localhost:8000>.

Interactive docs (Swagger UI) are at <http://localhost:8000/docs>.

### Run tests

To run tests:

```bash
cd server
uv run pytest tests/ -v
```

## Frontend

### Frontend prerequisites

Use preferentially Node lts (Node 24),
you can install it using [nvm](https://github.com/nvm-sh/nvm#usage)
in the `frontend` folder.

Then type `nvm use` in `frontend` folder whenever needed.

We also use `pnpm`.
You can install it with  `npm install -g pnpm`, in `frontend` folder.

### Install frontend dependencies

```bash
# in  frontend folder
pnpm install
```

Before running the project, set up the environment variables:

```bash
# in  frontend folder
cp .env.example .env
```
Edit `.env` as needed (defaults might be fine)

### Running the frontend

Spawn using
```bash
# in  frontend folder
pnpm run dev
```
