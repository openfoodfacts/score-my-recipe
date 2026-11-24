/**
 * fileOverview Translations management
 *
 * Loads translations from messages files
 * and decide which locale to use (see getLocale)
 * Note: also look at hooks.server which may set locale based on request headers
 *
 * It also exports functions from svelte-i18n, like the translate function (aka `_`)
 */
import { init, locale, register, getLocaleFromNavigator } from 'svelte-i18n';
import { browser } from '$app/environment';
import countries from './countries.json';
import messageFiles from './messages';

function generateCountryCode(country: Record<string, string>) {
	return `${country['languageCode']}-${country['countryCode'].toUpperCase()}`;
}

/**
 * The messages file holding the translations for a locale code.
 *
 * Translations are stored once per language (`fr.json`, `nl.json`…), not once per
 * country variant, so every regional code of a language (`fr-FR`, `nl-BE`…)
 * reads the same file.
 * When a language has no file of its own, the fallback locale is loaded instead:
 * an empty dictionary would make `waitLocale` resolve, but this keeps it explicit
 * and lets svelte-i18n walk its usual `fr-FR` -> `fr` -> `en-US` chain.
 *
 * @param code full locale code (eg. "fr-FR")
 * @returns the messages file name without extension (eg. "fr" or "en-US")
 */
function messagesFileFor(code: string): string {
	const language = code.split('-')[0];
	return language in messageFiles ? language : 'en-US';
}

const AVAILABLE_LOCALES: Map<string, string>[] = [];

countries.forEach((country) => {
	const country_local: Map<string, string> = new Map();
	country_local.set('label', country['label']);
	country_local.set('code', generateCountryCode(country));
	AVAILABLE_LOCALES.push(country_local);
});

const FALLBACK_LOCALE = 'en-US';
let currentLocale = FALLBACK_LOCALE;

locale.subscribe((value) => {
	if (value) {
		currentLocale = value;
	}
});

export function getLocale() {
	return currentLocale;
}

// TODO: when we have many locales we should load them lazily, when we really need them
countries.forEach((locale) => {
	const code = generateCountryCode(locale);
	register(code, async () => {
		return (await import(`./messages/${messagesFileFor(code)}.json`)).default;
	});
});

init({
	fallbackLocale: FALLBACK_LOCALE,
	initialLocale: getInitialLocale()
});

/**
 * getInitialLocale from the browser
 * @returns {String} locale code (eg. "en-US")
 */
export function getInitialLocale() {
	return browser ? getBrowserLocale() : FALLBACK_LOCALE;
}

export function getBrowserLocale() {
	if (!browser) throw new Error('getBrowserLocale should only be called in the browser');
	// const preferredLang = get(preferences).lang;
	const navLang = getLocaleFromNavigator();
	return navLang || FALLBACK_LOCALE;
}

// Explicitly re-export the svelte-i18n helpers used elsewhere in the app
// waitLocale and isLoading are used to wait for translations files to be ready
export { dictionary, isLoading, locale, waitLocale, _ } from 'svelte-i18n';
export { AVAILABLE_LOCALES };
