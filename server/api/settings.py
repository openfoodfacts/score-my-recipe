from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenFoodFactsEnvironments(str, Enum):
    """Enum for the OpenFoodFacts API environments."""

    PROD = "prod"
    STAGING = "staging"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SCORE_MY_RECIPE_")

    cache_dir: Annotated[Path, Field(description="Directory where cache is stored")] = Path(
        "./data/cache"
    )

    agribalyse_csv_path: Annotated[
        Path, Field(description="Path to the merged Agribalyse Synthese CSV file")
    ] = Path("./data/agribalyse.csv")

    openfoodfacts_env: Annotated[
        OpenFoodFactsEnvironments, Field(description="Environment to use for OpenFoodFacts API (prod or staging)")
    ] = OpenFoodFactsEnvironments.PROD


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
