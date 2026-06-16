# How to generate api-schema

Until we automate it, to generate the schema,
1. first start the dev server in a shell: `cd server; uv run uvicorn api.api:app --reload`
2. go in project folder, and run
   ```bash
   # get openapi json
   curl http://127.0.0.1:8000/openapi.json -o openapi.json
   # generate typescript file with openapi-typescript
   docker run --rm -v $(pwd)/openapi.json:/openapi.json -v $(pwd)/frontend/src:/src courtapi/openapi-typescript:7.13.0 /openapi.json -o /src/api-schema.d.ts
   ```
