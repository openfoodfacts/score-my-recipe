"""Async client for the Ecobalyse API (food2 and food simulator)."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from api.settings import get_settings

logger = logging.getLogger(__name__)


class EcobalyseAPIError(Exception):
    """Raised when the Ecobalyse API returns an error or is unreachable."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class EcobalyseClient:
    """Async client communicating with the Ecobalyse service."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_token: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.ecobalyse_base_url).rstrip("/")
        self.api_token = api_token if api_token is not None else settings.ecobalyse_api_token
        self.timeout = timeout if timeout is not None else settings.ecobalyse_timeout_seconds
        self.mock_fallback = settings.ecobalyse_mock_fallback

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Score-My-Recipe/0.1.0",
        }
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
            headers["token"] = self.api_token
        return headers

    async def check_health(self) -> dict[str, Any]:
        """Check whether the configured Ecobalyse instance is reachable."""
        url = f"{self.base_url}/"
        try:
            async with httpx.AsyncClient(timeout=min(self.timeout, 3.0)) as client:
                resp = await client.get(url, headers=self._headers())
                reachable = resp.status_code < 500
                return {
                    "reachable": reachable,
                    "status_code": resp.status_code,
                    "base_url": self.base_url,
                    "authenticated": bool(self.api_token),
                }
        except Exception as err:
            logger.warning("Ecobalyse health check failed for %s: %s", url, err)
            return {
                "reachable": False,
                "error": str(err),
                "base_url": self.base_url,
                "authenticated": bool(self.api_token),
            }

    async def simulate_food(self, query: dict[str, Any]) -> dict[str, Any]:
        """Submit a food impact simulation query to Ecobalyse.

        Tries `/food2/simulator` first; if that returns 404, falls back to
        `/food/simulator`.
        """
        endpoints = [f"{self.base_url}/food2/simulator", f"{self.base_url}/food/simulator"]
        last_error: Optional[Exception] = None

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for url in endpoints:
                try:
                    logger.debug("Calling Ecobalyse simulator at %s with %s", url, query)
                    resp = await client.post(url, json=query, headers=self._headers())

                    if resp.status_code == 404 and url != endpoints[-1]:
                        # Try fallback endpoint
                        continue

                    if resp.status_code == 401:
                        raise EcobalyseAPIError(
                            "Ecobalyse API authentication failed (401 Unauthorized). "
                            "Please provide a valid SCORE_MY_RECIPE_ECOBALYSE_API_TOKEN or use a self-hosted instance.",
                            status_code=401,
                            response_body=resp.text,
                        )

                    if not resp.is_success:
                        raise EcobalyseAPIError(
                            f"Ecobalyse API error {resp.status_code}: {resp.text}",
                            status_code=resp.status_code,
                            response_body=resp.text,
                        )

                    return resp.json()
                except httpx.RequestError as exc:
                    last_error = exc
                    logger.warning("Request error calling %s: %s", url, exc)

        if self.mock_fallback:
            logger.info("Using mock Ecobalyse fallback calculation due to error: %s", last_error)
            return self._generate_mock_result(query)

        raise EcobalyseAPIError(f"Could not connect to Ecobalyse at {self.base_url}: {last_error}")

    def _generate_mock_result(self, query: dict[str, Any]) -> dict[str, Any]:
        """Deterministic mock calculation for offline/testing environments."""
        ingredients = query.get("ingredients", [])
        total_mass = sum(ing.get("mass", 0) for ing in ingredients)
        # Approximate baseline: ~0.15 impact pts per 100g on average
        mock_ecs = round((total_mass / 100.0) * 0.15, 4)
        mock_cch = round((total_mass / 100.0) * 0.25, 4)
        mock_wtu = round((total_mass / 100.0) * 0.05, 4)
        mock_bvi = round((total_mass / 100.0) * 0.02, 4)

        return {
            "webUrl": f"{self.base_url.replace('/api', '')}/#/food2/simulator",
            "results": {
                "impacts": {
                    "ecs": mock_ecs,
                    "cch": mock_cch,
                    "wtu": mock_wtu,
                    "bvi": mock_bvi,
                    "ldu": round(mock_ecs * 0.8, 4),
                    "acd": round(mock_ecs * 0.01, 4),
                },
                "complements": {
                    "agroecological": 0.0,
                },
            },
            "description": "Offline simulated result (Score My Recipe fallback)",
            "query": query,
        }


_ecobalyse_client: Optional[EcobalyseClient] = None


def get_ecobalyse_client() -> EcobalyseClient:
    """Get or create singleton EcobalyseClient."""
    global _ecobalyse_client
    if _ecobalyse_client is None:
        _ecobalyse_client = EcobalyseClient()
    return _ecobalyse_client
