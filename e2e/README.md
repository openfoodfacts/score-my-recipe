# End-to-end integration tests

This package runs the **real** frontend and **real** backend together in a
browser (Playwright, Chromium) and drives a representative user flow:
French UI → parse a recipe → see the green score.

We don't want to test many scenarios,
(e2e tests are expensive),
but they insure we don't inadvertandly break some important feature.

## How it works

Playwright's `webServer` launches two processes, each with its own readiness
check so tests start only after both are ready (the backend is checked first):

1. **Backend** — `start-backend.sh` runs `server/tests/integration_server.py`,
   the real FastAPI app on port `8800`, with the OpenFoodFacts external
   dependency mocked so tests are deterministic and fully offline:
   - `parse_text` returns a recorded fixture
     (`server/tests/data/parse_text_recipe.json`) instead of calling live OFF.
   - Taxonomies are read from pinned snapshots
     (`server/tests/data/taxonomies/*.json`) via `SCORE_MY_RECIPE_CACHE_DIR`.
2. **Frontend** — `start-frontend.sh` runs `vite dev` on port `5174`, with
   `PUBLIC_RECIPE_API_URL=http://localhost:8800` pointing at the test backend.

Everything else (HTTP layer, ingredient mapping, green-score computation, CORS)
runs unmodified.

## Run

From the repo root:

```bash
just e2e
```

(or `just test` in this folder)

This installs e2e deps + Chromium (if needed) and runs the tests.

Run with a visible browser, in this folder:

```bash
npx playwright test --headed
```

## Refreshing pinned data

Both fixtures are committed to git and only need refreshing occasionally.

From this folder:

```bash
just refresh_test_data
```

If the green-score letter grade changes after a refresh, update
`EXPECTED_LETTER_GRADE` in `tests/recipe-score.spec.ts` after verifying the
new score is correct.

## Layout

```
e2e/
├── eslint.config.mjs        # ESLint flat config (TypeScript)
├── playwright.config.ts     # Playwright config (webServer array, Chromium project)
├── start-backend.sh         # Launches the backend (8800)
├── start-frontend.sh        # Launches the frontend dev server (5174)
├── tests/
│   └── recipe-score.spec.ts # the integration test
├── tsconfig.json            # TypeScript config (type-checking)
└── package.json
```
