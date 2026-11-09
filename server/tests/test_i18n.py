"""Tests for server-side internationalisation of the API notes."""

import logging
from pathlib import Path

import pytest
import yaml

import api.i18n as i18n
from api.score_types import NoteRef, RecipeMetrics


@pytest.fixture(autouse=True)
def _clear_i18n_cache():
    """Start every test from a cold cache so loading/logging is observable."""
    i18n.clear_cache()
    yield
    i18n.clear_cache()


# --- locale resolution -----------------------------------------------------


@pytest.mark.parametrize(
    ("lang", "expected"),
    [
        (None, "en-US"),
        ("", "en-US"),
        ("en", "en-US"),
        ("fr", "fr-FR"),
        ("fr-FR", "fr-FR"),
        ("fr_FR", "fr-FR"),
        ("de", "de-DE"),
        ("pt-BR", "pt-PT"),  # short code wins over the unknown region
        ("xx", "en-US"),  # unknown language falls back
    ],
)
def test_resolve_locale(lang, expected):
    """Short and full codes map to a shipped locale, unknown ones to en-US."""
    assert i18n.resolve_locale(lang) == expected


def test_locale_mapping_matches_crowdin():
    """``LOCALE_MAPPING`` must stay in sync with ``crowdin.yml``.

    Both trees (frontend and server) share the same Crowdin ``languages_mapping``:
    a divergence would make Crowdin write files the server does not expect.
    """
    crowdin = yaml.safe_load((Path(__file__).parent.parent.parent / "crowdin.yml").read_text())
    mappings = [entry["languages_mapping"]["locale"] for entry in crowdin["files"]]
    for mapping in mappings:
        assert mapping == i18n.LOCALE_MAPPING


# --- template lookup and fallback -----------------------------------------


def test_translate_returns_template_and_message():
    """The template keeps its placeholder, the message is rendered with params."""
    template, message = i18n.translate("notes.epi.not_found", {"origin": "en:france"}, "en")
    assert "{origin}" in template
    assert "en:france" in message
    assert "{origin}" not in message


def test_translate_in_french():
    """The same note id is rendered in French when lang is fr."""
    template, message = i18n.translate("notes.epi.no_origin", {}, "fr")
    assert "aucune origine" in message
    assert "no origin" not in message
    assert (
        template
        == "Modificateur EPI : aucune origine fournie, valeur par défaut « monde » appliquée"
    )


def test_unknown_language_falls_back_to_english():
    """An unsupported language is rendered with the en-US template."""
    _template, message = i18n.translate("notes.epi.no_origin", {}, "xx")
    assert message == i18n.translate("notes.epi.no_origin", {}, "en")[1]


def test_missing_key_falls_back_to_english_and_warns(caplog):
    """A key missing in the locale uses en-US and logs one warning."""
    with caplog.at_level(logging.WARNING, logger="api.i18n"):
        template, message = i18n.translate("notes.epi.no_origin", {}, "de")
    assert template == i18n.get_template("en-US", "notes.epi.no_origin")
    assert message == "EPI modifier: no origin provided, defaulting to world"
    assert any("notes.epi.no_origin" in record.message for record in caplog.records)


def test_missing_locale_file_falls_back_to_english():
    """A locale without a file (de is shipped by Crowdin, not yet here) renders the en-US template.

    The fallback must load the ``en-US`` file, not only report the missing one.
    """
    template, message = i18n.translate("notes.epi.no_origin", {}, "de")
    assert template == i18n.get_template("en-US", "notes.epi.no_origin")
    assert message == "EPI modifier: no origin provided, defaulting to world"
    # the missing locale is cached as absent, but the fallback file is loaded
    assert i18n._locale_cache.get("de-DE") is None
    assert i18n._locale_cache.get("en-US") is not None


def test_missing_key_everywhere_uses_id_and_warns_once(caplog):
    """An unknown id is used as template, and logged only once."""
    with caplog.at_level(logging.WARNING, logger="api.i18n"):
        first = i18n.translate("notes.does.not.exist", {}, "fr")
        second = i18n.translate("notes.does.not.exist", {}, "fr")
    assert first == ("notes.does.not.exist", "notes.does.not.exist")
    assert second == first
    warnings = [r for r in caplog.records if "notes.does.not.exist" in r.message]
    assert len(warnings) == 1


def test_all_shipped_locales_have_the_same_keys():
    """Every shipped locale defines every en-US key (no silent fallback in prod)."""

    def flatten(node, prefix=""):
        keys = set()
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                keys |= flatten(value, path)
            else:
                keys.add(path)
        return keys

    reference = flatten(i18n._load_locale("en-US"))
    for locale in i18n.available_locales():
        assert flatten(i18n._load_locale(locale)) == reference, locale


# --- rendering robustness --------------------------------------------------


def test_render_keeps_bad_placeholder(caplog):
    """A format error (missing param) never raises; the placeholder is kept."""
    with caplog.at_level(logging.WARNING, logger="api.i18n"):
        message = i18n.render("origin {origin}", {}, "en-US")
    assert "origin" in message


def test_render_malformed_template_returns_it_verbatim(caplog):
    """A template that cannot be parsed is returned as-is instead of raising."""
    with caplog.at_level(logging.WARNING, logger="api.i18n"):
        message = i18n.render("broken {foo", {}, "en-US")
    assert message == "broken {foo"


def test_mf1_placeholder_conversion():
    """Frontend-style ``{name}`` (with or without a formatter) becomes ``{$name}``.

    Already-converted ``{$name}`` references are left untouched, so the conversion is idempotent.
    """
    assert i18n.to_mf2("{a} and {b}") == "{$a} and {$b}"
    assert i18n.to_mf2("{$a} and {b :number}") == "{$a} and {$b :number}"
    assert i18n.to_mf2(i18n.to_mf2("{a}")) == "{$a}"


# --- warmup ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_warmup_loads_locale():
    """Warmup loads the translation file so the cache stays warm."""
    await i18n.warmup("fr")
    assert i18n._locale_cache.get("fr-FR") is not None


@pytest.mark.asyncio
async def test_warmup_unknown_language_loads_fallback():
    """Warming an unknown language loads the fallback locale."""
    await i18n.warmup("xx")
    assert i18n._locale_cache.get("en-US") is not None


# --- domain side -----------------------------------------------------------


def test_add_note_builds_note_refs():
    """``add_note`` stores a language-agnostic NoteRef with its params."""
    metrics = RecipeMetrics()
    metrics.add_note("notes.epi.not_found", origin="en:france")
    metrics.add_note("notes.seasonality.no_fresh_produce")
    assert metrics.notes == [
        NoteRef(id="notes.epi.not_found", params={"origin": "en:france"}),
        NoteRef(id="notes.seasonality.no_fresh_produce", params={}),
    ]
