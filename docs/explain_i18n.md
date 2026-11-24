# Explain internationalisation (i18n)

The frontend translates all user-facing strings with
[svelte-i18n](https://github.com/kaisermann/svelte-i18n) (v4).

## Where the messages live

- Setup: [`frontend/src/lib/i18n/index.ts`](../frontend/src/lib/i18n/index.ts)
  registers every locale and re-exports the `_` store.
- Messages: one JSON file per **language** in
  [`frontend/src/lib/i18n/messages/`](../frontend/src/lib/i18n/messages/),
  e.g. `en-US.json`, `fr.json`, `nl.json`. `en-US.json` is the reference source file.
  [`messages/index.ts`](../frontend/src/lib/i18n/messages/index.ts) lists which files exist;
  it is the only place to touch when adding a language.
- Keys are nested objects, looked up with dot notation: `navbar.score_recipe`.
- In components: `{$_('navbar.score_recipe', { default: 'Score a recipe' })}`.
  Always keep the `default` fallback (see `frontend/AGENTS.md`).

## One file per language, not per country

Translations are stored once per language (`fr.json`, `nl.json`…).
A regional code such as `fr-FR` or `nl-BE` loads the file of its language:
`messagesFileFor` in `index.ts` strips the country part.
This matters because svelte-i18n resolves `fr-FR` as `fr-FR` → `fr` → `en-US`:
a `fr.json` next to a `fr-FR.json` would silently act as an override layer,
and the two files would drift apart with no way to tell which one is authoritative.

Adding a language-specific exception later is still possible:
put the few differing keys in a regional file and register it in `messages/index.ts`
instead of adding a whole new language file.

## Locale files are partial, missing keys fall back to `en-US`

`en-US.json` must contain every key.
Every other locale file may contain **only the keys that were actually translated**;
a key absent from a locale file is resolved from `en-US.json` at runtime.

This is provided by svelte-i18n itself:
`init({ fallbackLocale: 'en-US' })` makes lookups walk the current locale and its fallback,
and the fallback dictionary is loaded together with the requested one,
so `waitLocale` covers it before the page renders.
Adding a label therefore only touches `en-US.json` in the repository;
translations for other languages land later through Crowdin.

Consequences to keep in mind:

- Never copy an English value into another locale file to "complete" it.
  That hides the fact that the string is untranslated and shadows future `en-US` fixes.
  `pnpm i18nsync` removes such leftovers.
- A locale file that is identical to `en-US` is useless: delete it and let the fallback apply.
- Code that reads `$dictionary` directly must merge `en-US` under the requested locale
  instead of picking one dictionary (see `getRecipeExamples` in
  [`frontend/src/lib/ui/recipeExamples.ts`](../frontend/src/lib/ui/recipeExamples.ts)).

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

`pnpm i18ncheck` (in `frontend/`) fails on keys that no longer exist in `en-US.json`
and on placeholder mismatches, and prints the translation coverage of each locale.
Missing keys are **not** an error: they fall back to `en-US`, see above.

`pnpm i18nsync` prunes the keys removed from `en-US.json`,
and drops the leaves that are identical to `en-US` (untranslated leftovers).
It never copies English into another locale.

Both live in [`frontend/scripts/i18n-sync.ts`](../frontend/scripts/i18n-sync.ts).

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
`en-US.json` is the source, and each language is written to `frontend/src/lib/i18n/messages/<language>.json`, with the `languages_mapping` collapsing country variants onto the language file (`fr` → `fr.json`, `nl` → `nl.json`…).
A second entry covers the backend: `server/i18n/en-US.json` is the source, and each language is written to `server/i18n/<locale>.json`, with the same `languages_mapping`.
That mapping is duplicated as `LOCALE_MAPPING` in `server/api/i18n.py`, and a test guards that both stay identical.

Sync is done by the Crowdin GitHub Action (using `@crowdin/cli` and the `CROWDIN_PROJECT_ID` / `CROWDIN_PERSONAL_TOKEN` secrets), which opens a PR titled `l10n: New Crowdin translations to review and merge`.
To fix a bad translation, correct it in Crowdin first, so it is not re-applied on the next sync.

Only translated strings are pulled into the locale files (`skip_untranslated_strings: true`
and `json.preserve_keys_with_empty_values: false`), which keeps the files partial:
untranslated keys simply stay absent and fall back to `en-US`.

See the Crowdin GitHub Action documentation:
<https://github.com/crowdin/github-action>
