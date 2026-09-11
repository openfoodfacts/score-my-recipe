"""Data useful for green-score computation."""

import csv
import io

from aiofile import async_open
from asyncstdlib.functools import cache as async_cache

import api.settings as settings

# A dict associating labels to their bonus in the green-score computation.
# see https://docs.score-environnemental.com/methodologie-recette/bonus-malus-recette/systeme-de-production/labels
LABELS_BONUS = {
    "fr:nature-et-progres": 20,
    "fr:bio-coherence": 20,
    "en:demeter": 20,
    "fr:bio-equitable": 20,
    "en:eu-organic": 15,
    "fr:ab-agriculture-biologique": 15,
    # TODO: Needs verification.
    # it's there:
    # https://docs.score-environnemental.com/methodologie/produit/systeme-de-production/label
    # but not there:
    # https://docs.score-environnemental.com/methodologie-recette/bonus-malus-recette/systeme-de-production/labels
    "en:sustainable-fishing-method": 15,
    "fr:haute-valeur-environnementale": 10,
    "en:utz-certified": 10,
    "en:rainforest-alliance": 10,
    "en:fairtrade-international": 10,
    "fr:bleu-blanc-coeur": 10,
    # this one is conditionned by the ingredient type, see LABELS_BONUS_INGREDIENTS_RESTRICTIONS
    "fr:label-rouge": 10,
    "en:sustainable-seafood-msc": 10,
    "en:responsible-aquaculture-asc": 10,
}


# A dict that restrict some labels bonus to specific ingredients types
LABELS_BONUS_INGREDIENTS_RESTRICTIONS = {
    "fr:label-rouge": ["en:beef", "en:veal-meat", "en:lamb-meat"],
}


@async_cache
async def get_epi_bonuses():
    """return a dict mapping origins to EPI bonuses

    see https://docs.score-environnemental.com/methodologie-recette/bonus-malus-recette/systeme-de-production/origine/synthese

    Note that it's not the same as for products !
    """
    fpath = settings.get_settings().data_dir / "greenscore-epi-bonuses.csv"
    # async read, then use csv.DictReader (which does not support async)
    async with async_open(fpath, "r", encoding="utf-8") as f:
        content = await f.read()
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    return {row["origin"].strip(): float(row["bonus"]) for row in reader if row["origin"].strip()}
