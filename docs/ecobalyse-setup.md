# Ecobalyse & Coût Environnemental Setup Guide

Score my Recipe supports two environmental scoring methodologies:
1. **Green-Score**: Based on Agribalyse PEF single-score data, normalized on a 0–100 scale with letter grades A+ to F.
2. **Coût Environnemental (Ecobalyse)**: The official French methodology (ADEME / Ministère de la Transition Écologique) powered by the **Food2** generic calculation engine, expressed in official **Points d'impact (Pts)**.

---

## 1. Using the Hosted Official Ecobalyse API

By default, Score my Recipe connects to the official API at `https://ecobalyse.beta.gouv.fr/api`.

Because the official hosted API requires authentication, configure your API token in `.env`:

```bash
# In your server environment or .env:
SCORE_MY_RECIPE_ECOBALYSE_BASE_URL=https://ecobalyse.beta.gouv.fr/api
SCORE_MY_RECIPE_ECOBALYSE_API_TOKEN=your_token_here
```

To obtain a token for the official API:
- Request an API token from the [Ecobalyse / Affichage Environnemental portal](https://ecobalyse.beta.gouv.fr/#/api).
- Fill in the access request form if needed.

---

## 2. Self-Hosting Ecobalyse (Local / Private Instance)

To run Ecobalyse completely locally without rate limits or token requirements:

### Using Docker Compose

Start Score my Recipe with the Ecobalyse service override:

```bash
docker compose -f docker-compose.yml -f docker/docker-compose.ecobalyse.yml up -d
```

Or using `just`:

```bash
just ecobalyse-up
```

To stop the instance:

```bash
just ecobalyse-down
```

### Configuration for Self-Hosted Instance

When running Ecobalyse locally on port `8001`:

```bash
SCORE_MY_RECIPE_ECOBALYSE_BASE_URL=http://localhost:8001/api
# No SCORE_MY_RECIPE_ECOBALYSE_API_TOKEN is needed for self-hosted instances!
```

---

## 3. Offline / Mock Fallback for CI and Sandboxes

When running in sandboxed environments or CI pipelines without internet access or local Ecobalyse containers:

```bash
SCORE_MY_RECIPE_ECOBALYSE_MOCK_FALLBACK=true
```

When enabled, if the Ecobalyse server cannot be reached, Score my Recipe produces deterministic simulation results based on recipe ingredient weights so development and testing can proceed uninterrupted.

---

## 4. Health Check Endpoint

Check the status of the Ecobalyse integration at any time:

```bash
curl http://localhost:8000/v1/health
```

Example response:
```json
{
  "status": "ok",
  "ecobalyse": {
    "reachable": true,
    "status_code": 200,
    "base_url": "https://ecobalyse.beta.gouv.fr/api",
    "authenticated": true
  }
}
```
