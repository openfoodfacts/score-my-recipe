/**
 * @fileoverview - compute link to off website based on locale
 */

import { waitLocale, getLocale } from '$lib/i18n';

export async function getOffWebsiteLink() {
	await waitLocale();
	const locale = getLocale();
	// off only use short code
	const offLocale = locale.split('-')[0];
	return `world-${offLocale}.openfoodfacts.org`;
}

export const offLinks = { website: await getOffWebsiteLink() };
