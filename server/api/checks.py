"""Some high level checks (that are not self contained)"""

from api.off import languages_by_code


async def check_language_code(lang: str) -> bool:
    """Check if the language code is valid (exists in the OFF languages taxonomy)"""

    languages = await languages_by_code()
    return lang in languages
