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

`pnpm i18nsync` (in `frontend/`) adds missing keys to every locale from
`en-US.json`; `pnpm i18ncheck` reports missing/extra keys and placeholder
mismatches. See [`frontend/scripts/i18n-sync.ts`](../frontend/scripts/i18n-sync.ts).

## Crowdin

Actual translations are written by the community on the Open Food Facts Crowdin
project (<https://translate.openfoodfacts.org>).
The mapping between the Crowdin project and the files above is configured in
[`crowdin.yml`](../crowdin.yml):
`en-US.json` is the source,
and each language is written to `frontend/src/lib/i18n/messages/<locale>.json`.

Sync is done by the Crowdin GitHub Action (using `@crowdin/cli`
and the `CROWDIN_PROJECT_ID` / `CROWDIN_PERSONAL_TOKEN` secrets),
which opens a PR titled `l10n: New Crowdin translations to review and merge`.
To fix a bad translation, correct it in Crowdin first
so it is not re-applied on the next sync.

See the Crowdin GitHub Action documentation:
<https://github.com/crowdin/github-action>
