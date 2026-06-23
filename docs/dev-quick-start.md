# Developer Quick Start

This guide explains how to set up and run the **Score My Recipe** API locally.

## Setup

### One-liner setup - recommended

For an automated setup, run the dev setup script from the repository root:

```bash
./scripts/dev-setup.sh
```

It will install all prerequisites and dependencies for both backend and frontend.
If you prefer to do things manually, follow the steps below.

On Windows, the best option seems to use the automated setup above in WSL.
### Manual install

You must install [`just`](https://just.systems/man/en/).

Also `bash` must be available.

For server (backend), install [`uv`](https://docs.astral.sh/uv/) and then use `uv sync` in `server` folder.

For frontend, install [nvm (Node version Manager)](https://github.com/nvm-sh/nvm),
go in `frontend` folder and use `nvm use && npm install -g pnpm && pnpm install`.
Also copy `.env.example` to `.env`.
### Refreshing your project

If you want to refresh your project dependencies,
in the main folder, run:
```bash
just refresh
```

## Common operations

We use [`just`](https://just.systems/man/en/) for common operations.

Just run `just` in main folder or in `frontend` and `server` folder
to get the list of actions.

Don't hesitate to look at `justfile` if you need to tweak some commands.

### Checks

Before pushing a PR, remember to run:
```bash
just check
```

## Backend

### Run the API

In `server` folder:
```bash
just dev
```

The API will be available at <http://localhost:8000>.

Interactive docs (Swagger UI) are at <http://localhost:8000/docs>.


## Frontend

### Running the frontend

In `frontend` folder:
```bash
just dev
```
