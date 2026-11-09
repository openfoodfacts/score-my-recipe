# Explain internationalisation (i18n)

The frontend translates all user-facing strings with
[svelte-i18n](https://github.com/kaisermann/svelte-i18n) (v4).

## Where the messages live

- Setup: [`frontend/src/lib/i18n/index.ts`](../frontend/src/lib/i18n/index.ts)
  registers every locale and re-exports the `_` store.
- Messages: one JSON file per locale in
  [`frontend/src/lib/i18n/messages/`](../frontend/src/lib/i18n/messages/),
  e.g. `en-US.json`, `fr-FR.json`. `en-US.json` is the reference source file.
- Keys are nested objects, looked up with dot notation: `navbar.score_recipe`.
- In components: `{$_('navbar.score_recipe', { default: 'Score a recipe' })}`.
  Always keep the `default` fallback (see `frontend/AGENTS.md`).

## Formatting messages with parameters

Messages are formatted with **ICU MessageFormat**, not `printf`-style `%s`/`%d`.
Parameters are named and passed through `values`:

```jsonc
// messages/en-US.json
"recipe": {
	"weight": "The ingredient {name} weighs {weight, number} g",
	"ingredients_count": "{count, plural, =0 {no ingredients} one {# ingredient} other {# ingredients}}"
}
```

```svelte
{$_('recipe.weight', {
	values: { name: 'tomato', weight: 120 },
	default: 'The ingredient {name} weighs {weight} g'
})}
{$_('recipe.ingredients_count', { values: { count: 3 } })}
```

Numbers, dates, plurals and selects are all supported and are formatted
according to the current locale.

Full syntax reference (plurals, select, number/date skeletons, escaping…):

<https://github.com/kaisermann/svelte-i18n/blob/5afd1f8677c8371dcbec5b5b9a7175500f17591b/docs/Formatting.md>

## Keeping locale files in sync

`pnpm i18nsync` (in `frontend/`) adds missing keys to every locale from `en-US.json`;
`pnpm i18ncheck` reports missing/extra keys and placeholder mismatches.
See [`frontend/scripts/i18n-sync.ts`](../frontend/scripts/i18n-sync.ts).

## Server side: notes returned by the API

The notes attached to ingredients and scores (`notes` / `ingredientsNotes`) are translated by the backend, so that API consumers get readable messages.

### Where the messages live

- Messages are in [`server/i18n/`](../server/i18n/), one JSON file per locale.
- They are structured like the frontend ones: nested objects, looked up with dot keys (e.g. `notes.epi.no_origin`).
- `en-US.json` is the reference, `fr-FR.json` is maintained alongside it, and the other locales come from Crowdin.

### How messages are written

Messages are written in ICU MessageFormat, with frontend-style placeholders (`{origin}`), so that both file sets read the same.

Rendering uses the [`messageformat2`](https://pypi.org/project/messageformat2/) package, which expects MF2 syntax (`{$origin}`).
The conversion happens at render time (see `to_mf2` in `server/api/i18n.py`), so the files themselves stay in the frontend form.
As a result, `icu_template` in the API response is the template as stored in the files (frontend-style placeholders), and `message` is the rendered result.

Server messages must use plain placeholders (`{origin}`, `{count :number}`).
The conversion only rewrites variables, so MF1 constructs (`{n, plural, …}`, `{x, select, …}`) are not supported:
such a template is never formatted and falls back to being returned verbatim,
which keeps a bad translation from breaking a request.

### How notes reach the API

The computation code only fills `id` and `params` of each note (a plain `api.types.Note`, see `server/api/types.py`).
They are translated at the API boundary (`translate_notes` in `server/api/api_i18n.py`), which sets the two remaining fields:

| Field          | Content                                                 |
| -------------- | ------------------------------------------------------- |
| `id`           | message id, e.g. `notes.epi.not_found`                  |
| `icu_template` | the translated template, with its `{placeholders}`       |
| `params`       | the values used for the placeholders                    |
| `message`      | the template rendered with `params` (convenience only)  |

### Which language is used

The request language comes from the `lang` parameter.

Short codes are mapped to locales like on the frontend (`en` → `en-US`, `fr` → `fr-FR`, see `LOCALE_MAPPING`).
Unknown languages fall back to `en-US`, and a missing message falls back to its `en-US` version, then to its id.

Translation files are loaded lazily; set `SCORE_MY_RECIPE_WARMUP=fr,en` to load them at startup.

## Crowdin

Actual translations are written by the community on the Open Food Facts Crowdin project (<https://translate.openfoodfacts.org>).
The mapping between the Crowdin project and the files above is configured in [`crowdin.yml`](../crowdin.yml):
`en-US.json` is the source, and each language is written to `frontend/src/lib/i18n/messages/<locale>.json`.
A second entry covers the backend: `server/i18n/en-US.json` is the source, and each language is written to `server/i18n/<locale>.json`, with the same `languages_mapping`.
That mapping is duplicated as `LOCALE_MAPPING` in `server/api/i18n.py`, and a test guards that both stay identical.

Sync is done by the Crowdin GitHub Action (using `@crowdin/cli` and the `CROWDIN_PROJECT_ID` / `CROWDIN_PERSONAL_TOKEN` secrets), which opens a PR titled `l10n: New Crowdin translations to review and merge`.
To fix a bad translation, correct it in Crowdin first, so it is not re-applied on the next sync.

See the Crowdin GitHub Action documentation:
<https://github.com/crowdin/github-action>
