import { describe, it, expect } from 'vitest';

import messageFiles from '$lib/i18n/messages';

const LANGUAGE_FILE_NAMES = ['ca', 'de', 'es', 'fr', 'it', 'nl', 'pt'];

describe('i18n message files', () => {
	it('ships the reference locale used as fallback', () => {
		expect(messageFiles).toHaveProperty('en-US');
	});

	it('has one file per language, not one per country variant', () => {
		const languageFiles = Object.keys(messageFiles).filter((name) => !name.includes('-'));

		expect(languageFiles.sort()).toEqual(LANGUAGE_FILE_NAMES);
	});
});
