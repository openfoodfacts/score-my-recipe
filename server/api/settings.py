from enum import StrEnum
from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenFoodFactsEnvironments(StrEnum):
    """Enum for the OpenFoodFacts API environments."""

    PROD = "prod"
    STAGING = "staging"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SCORE_MY_RECIPE_")

    data_dir: Annotated[Path, Field(description="Directory where data is stored")] = Path("./data")

    cache_dir: Annotated[Path, Field(description="Directory where cache is stored")] = Path(
        "./data/cache"
    )

    agribalyse_csv_path: Annotated[
        Path, Field(description="Path to the merged Agribalyse Synthese CSV file")
    ] = Path("./data/agribalyse.csv")

    openfoodfacts_env: Annotated[
        OpenFoodFactsEnvironments,
        Field(description="Environment to use for OpenFoodFacts API (prod or staging)"),
    ] = OpenFoodFactsEnvironments.PROD

    ecobalyse_base_url: Annotated[
        str,
        Field(
            description="Base URL for the Ecobalyse API (official hosted or self-hosted instance)"
        ),
    ] = "https://ecobalyse.beta.gouv.fr/api"

    ecobalyse_api_token: Annotated[
        str | None,
        Field(
            description="API token for Ecobalyse API (required for hosted API, optional for self-hosted)"
        ),
    ] = None

    ecobalyse_timeout_seconds: Annotated[
        float, Field(description="HTTP timeout for requests to Ecobalyse in seconds")
    ] = 8.0

    ecobalyse_mock_fallback: Annotated[
        bool,
        Field(
            description="Whether to fall back to a mock computation when Ecobalyse is unreachable (useful in sandboxes/offline tests)"
        ),
    ] = False


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
