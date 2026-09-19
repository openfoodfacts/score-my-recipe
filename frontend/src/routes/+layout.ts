import { locale, waitLocale } from '$lib/i18n';
import { browser } from '$app/environment';
import type { LayoutLoad } from './$types';

/**
 * At load time we set the language
 */
export const load: LayoutLoad = async () => {
	await waitLocale();

	return {};
};
