"""Server-side internationalisation for the notes returned by the API.

Translation files live in ``server/i18n/<locale>.json`` (see that folder and ``docs/explain_i18n.md``).
They are structured like the frontend messages: a nested JSON object looked up with dot keys, e.g. ``notes.epi.no_origin``.

Messages are written in frontend-style ICU MessageFormat (MF1 placeholders such as ``{origin}``), and converted to MF2 (``{$origin}``) when rendered.
Rendering uses :mod:`messageformat2`, which also provides locale-aware number formatting through Babel.

Lookup logic:

* the requested language is mapped to a full locale through
  :data:`LOCALE_MAPPING` (``"fr"`` -> ``"fr-FR"``, mirroring ``crowdin.yml``);
* a missing locale file falls back to :data:`FALLBACK_LOCALE` (``en-US``);
* a missing message key falls back to the ``en-US`` template, then to the message id itself,
  so a typo is visible but never crashes a request;
* each missing ``(locale, id)`` pair is logged once to avoid log spam.

Messages should stay simple: the MF1-to-MF2 conversion (:func:`to_mf2`) only rewrites plain variable placeholders
(``{name}``, ``{name :number}``).
MF1 structural constructs (``{n, plural, …}``, ``{x, select, …}``) are not converted and fall back to the verbatim template at render time,
so write server messages with simple placeholders only.

Translation files are baked into the image: each locale is loaded lazily on first use and cached for the process lifetime.
Languages listed in the ``SCORE_MY_RECIPE_WARMUP`` setting are loaded eagerly at startup through :func:`warmup`.
"""

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from messageformat2 import format_message

from api.lang import two_letter_lang_code

logger = logging.getLogger(__name__)

# Directory holding the per-locale JSON files (sibling of this package).
I18N_DIR = Path(__file__).resolve().parent.parent / "i18n"

FALLBACK_LOCALE = "en-US"

# Short language code -> locale file. Must stay in sync with the
# ``languages_mapping`` of ``crowdin.yml`` (guarded by a test).
LOCALE_MAPPING: dict[str, str] = {
    "en": "en-US",
    "fr": "fr-FR",
    "de": "de-DE",
    "es": "es-ES",
    "it": "it-IT",
    "ca": "ca-ES",
    "nl": "nl-NL",
    "pt": "pt-PT",
}

_locale_cache: dict[str, dict[str, Any] | None] = {}
_warned_missing: set[tuple[str, str]] = set()


def resolve_locale(lang: str | None) -> str:
    """Map a language code to a shipped locale, falling back to ``en-US``.

    Accepts short codes (``"fr"``) and full codes (``"fr-FR"``); the hyphenated form may use an underscore (``"fr_FR"``).
    Unknown languages are mapped to :data:`FALLBACK_LOCALE`, so callers always get a usable locale.
    """
    if not lang:
        return FALLBACK_LOCALE
    normalized = lang.replace("_", "-")
    if normalized in LOCALE_MAPPING.values():
        return normalized
    short = two_letter_lang_code(normalized)
    return LOCALE_MAPPING.get(short, FALLBACK_LOCALE)


def _load_locale(locale: str) -> dict[str, Any] | None:
    """Load (and cache) the message dict for ``locale``; ``None`` when absent."""
    if locale not in _locale_cache:
        path = I18N_DIR / f"{locale}.json"
        try:
            _locale_cache[locale] = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            logger.warning("Translation file not found for locale %s: %s", locale, path)
            _locale_cache[locale] = None
    return _locale_cache[locale]


# MF1-style variable placeholders ({name}), as used by the frontend messages and Crowdin, mapped to MF2's {$name}.
# Only simple variable references are converted: ``{name}`` and ``{name :number}`` become ``{$name}`` / ``{$name :number}``.
# MF1 structural constructs (plural/select) are left untouched and render as the verbatim template:
# translating them correctly needs a real MF1 parser, and server messages are plain placeholders.
_MF1_VARIABLE = re.compile(r"\{(?![{$])([A-Za-z_]\w*)(?=[}\]\s]|$)")


def to_mf2(template: str) -> str:
    """Convert frontend-style ``{name}`` placeholders to MF2 ``{$name}``."""
    return _MF1_VARIABLE.sub(r"{$\1", template)


def _lookup(messages: dict[str, Any] | None, message_id: str) -> str | None:
    """Look up a dotted ``message_id`` in a nested messages dict."""
    if messages is None:
        return None
    node: Any = messages
    for part in message_id.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, str) else None


def get_template(locale: str, message_id: str) -> str:
    """Return the ICU template for ``message_id`` in ``locale``.

    Falls back to :data:`FALLBACK_LOCALE`, then to the message id itself.
    A missing key is logged once per ``(locale, id)`` pair.
    """
    template = _lookup(_load_locale(locale), message_id)
    if template is not None:
        return template

    fallback_template = _lookup(_load_locale(FALLBACK_LOCALE), message_id)
    key = (locale, message_id)
    if key not in _warned_missing:
        _warned_missing.add(key)
        if fallback_template is None:
            logger.warning("Missing translation for %r in %s and its fallback", message_id, locale)
        else:
            logger.warning(
                "Missing translation for %r in %s, using %s", message_id, locale, FALLBACK_LOCALE
            )
    return fallback_template if fallback_template is not None else message_id


def render(template: str, params: dict[str, Any], locale: str) -> str:
    """Render an ICU template with ``params`` for ``locale``.

    Formatting errors (e.g. a parameter type mismatch) are reported through ``on_error``, and the faulty placeholder is kept verbatim,
    so a bad translation never turns into a 500.

    Note: Babel expects underscored locale codes (``"fr_FR"``), while our files use the hyphenated Crowdin form (``"fr-FR"``), so convert at the boundary.
    """
    babel_locale = locale.replace("-", "_")
    errors: list[Exception] = []
    try:
        message = format_message(to_mf2(template), params, babel_locale, on_error=errors.append)
    except Exception:
        # A malformed template (parse error) or an unknown locale cannot be rendered at all:
        # return it verbatim so consumers still see something meaningful.
        logger.warning("Could not render template %r for %s", template, locale, exc_info=True)
        return template
    for error in errors:
        logger.warning("Error rendering %r for %s: %s", template, locale, error)
    return message


def translate(message_id: str, params: dict[str, Any] | None, lang: str | None) -> tuple[str, str]:
    """Return ``(icu_template, message)`` for ``message_id`` in ``lang``.

    ``icu_template`` is the translated template (MF1, as stored in the files), and ``message`` its rendering with ``params``.
    Both use the resolved locale (see :func:`resolve_locale`).
    """
    locale = resolve_locale(lang)
    template = get_template(locale, message_id)
    return template, render(template, params or {}, locale)


def clear_cache() -> None:
    """Drop the locale cache and the missing-key log deduplication (used by tests)."""
    _locale_cache.clear()
    _warned_missing.clear()


@lru_cache(maxsize=None)
def available_locales() -> frozenset[str]:
    """Return the locales shipped with the server (from the i18n directory)."""
    return frozenset(path.stem for path in I18N_DIR.glob("*.json"))


async def warmup(lang: str) -> None:
    """Eagerly load the translation file for ``lang`` (see ``api.warmup``)."""
    _load_locale(resolve_locale(lang))
