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

Run these commands in order every time you start work in a fresh environment:

```bash
cp .env.example .env
pnpm install --frozen-lockfile
```

---

## Key Commands

| Command       | Purpose                                     | Approx. time       |
| ------------- | ------------------------------------------- | ------------------ |
| `pnpm dev`    | Start dev server at <http://localhost:5173> | ~3s (runs forever) |
| `pnpm build`  | Production build                            | ~20s               |
| `pnpm check`  | TypeScript + Svelte type check              | ~10s               |
| `pnpm lint`   | Prettier + ESLint                           | ~15s               |
| `pnpm format` | Auto-format all files                       | ~5s                |

> External API calls to OpenFoodFacts will fail in sandboxed environments — this is expected. Focus on UI and code correctness.


---

## Source Structure

This is a mono repository with two components:

* the frontend in `frontend` based on sveltekit
* the backend in `server` based on FastAPI

---

## Contributing Rules

### Branches & Commits

- Branch off `main`.
- Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/): `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, etc.

### Pull Requests

- **If your PR addresses an issue, link it** using a closing keyword: `Fixes: #N` or `Closes: #N`.
- In the LLM disclosure section, state your agent name, model version, and how it was used (agentic / autocomplete / review).
- **Always disclose that you are an AI agent** both on the issue (when claiming it) and in the PR.
- Do not open a PR with failing lint, type errors, or build failures.
