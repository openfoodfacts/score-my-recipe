/**
 * @fileoverview The languages that have their own translation file.
 *
 * Translations are stored once per language, not once per country variant:
 * `fr.json` covers `fr-FR`, `nl.json` covers `nl-NL` and `nl-BE`.
 * This module only imports the files, so it is the single place that knows
 * which languages are translated; `index.ts` reads the keys to register them.
 *
 * Adding a language: add an entry here and run `pnpm i18ncheck`.
 * A language without a file here falls back to `en-US` at runtime.
 *
 * Locale files are partial and may be missing keys:
 * a missing key is resolved from `en-US` (see `docs/explain_i18n.md`).
 */
import ca from './ca.json';
import de from './de.json';
import enAU from './en-AU.json';
import enGB from './en-GB.json';
import enUS from './en-US.json';
import es from './es.json';
import fr from './fr.json';
import it from './it.json';
import nl from './nl.json';
import pt from './pt.json';

const messageFiles: Record<string, unknown> = {
	ca,
	de,
	'en-AU': enAU,
	'en-GB': enGB,
	'en-US': enUS,
	es,
	fr,
	it,
	nl,
	pt
};

export default messageFiles;
