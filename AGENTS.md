# Agent Guide —  Score my recipe

This is the canonical guide for AI agents working on this repository.
**Read this file before doing anything else.**

> Humans contributing code should read [CONTRIBUTING.md](docs/CONTRIBUTING.md) instead.
> This file is intentionally structured for machine consumption.

---

## Project Overview

Open Score My Recipe is a software to compute different scores on a recipe. Right now it concentrate on the green-score.
It has a **FastAPI** backend (in `server` folder) and a **SvelteKit** frontend (in `frontend` folder).



---

## Bootstrap

Run this command in a fresh environment to set up both the frontend and backend
(it installs `uv`, `nvm`/Node/pnpm, dependencies, and copies `.env` files):

```bash
./scripts/dev-setup.sh full
```

See the `frontend/` and `server/` folders for their own bootstrap instructions.

---

## Key Commands

| Command       | Purpose                                     | Approx. time       |
| ------------- | ------------------------------------------- | ------------------ |
| `just e2e`    | End-to-end integration tests (Playwright)   | ~30s               |
| `pnpm dev`    | Start dev server at <http://localhost:5173> | ~3s (runs forever) |
| `pnpm build`  | Production build                            | ~20s               |
| `pnpm check`  | TypeScript + Svelte type check              | ~10s               |
| `pnpm lint`   | Prettier + ESLint                           | ~15s               |
| `pnpm format` | Auto-format all files                       | ~5s                |

> External API calls to OpenFoodFacts will fail in sandboxed environments — this is expected. Focus on UI and code correctness.

---

## Integration tests

End-to-end tests live in `e2e/` (Playwright, Chromium). They start the **real**
backend (FastAPI with OpenFoodFacts mocked) and the **real** frontend (vite dev)
together, then drive the browser through a representative user flow.

The OpenFoodFacts dependency is mocked so tests are deterministic and offline:

- **parse_text** — a recorded fixture (`server/tests/data/parse_text_recipe.json`)
  replaces live OFF ingredient parsing. Re-capture with
  `server/tests/data/capture_parse_text.py` (network required).
- **Taxonomies** — pinned snapshots live in `server/tests/data/taxonomies/`.
  Refresh with `server/tests/data/update_taxonomies.sh` (network required).
- The backend entrypoint is `server/tests/integration_server.py`.

Run with `just e2e` (installs deps + Chromium on first run).


---

## Source Structure

This is a mono repository with two components:

* the frontend in `frontend` based on sveltekit
* the backend in `server` based on FastAPI

---

## Contributing Rules

Read [architecture document](./docs/technical-architecture.md)

### Branches & Commits

- Branch off `main`.
- Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/): `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, etc.

### Pull Requests

- **If your PR addresses an issue, link it** using a closing keyword: `Fixes: #N` or `Closes: #N`.
- In the LLM disclosure section, state your agent name, model version, and how it was used (agentic / autocomplete / review).
- **Always disclose that you are an AI agent** both on the issue (when claiming it) and in the PR.
- Do not open a PR with failing lint, type errors, or build failures.
