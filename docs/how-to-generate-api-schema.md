# How to generate api-schema

The api-schema is generated from the server openapi spec.

Just run: `just generate-openapi`

It will:
* regenerate the `openapi.json` in `docs` folder
* regenerate `frontend/src/api-schema.d.ts`