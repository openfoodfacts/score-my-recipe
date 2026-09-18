"""Some high level checks (that are not self contained)"""

import api.off as off


async def check_language_code(lang: str) -> bool:
    """Check if the language code is valid (exists in the OFF languages taxonomy)"""

    languages = await off.languages_by_code()
    return lang in languages


async def check_country_code(country: str) -> bool:
    """Check if the country code is valid (exists in the OFF countries taxonomy)"""

    countries = await off.origins_by_country_code()
    return country in countries
