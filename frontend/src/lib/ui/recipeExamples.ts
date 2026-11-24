/**
 * @fileoverview Example recipes shown on the "add recipe" page as quick-fill
 * shortcuts (the "Or try an example:" buttons).
 *
 * Only the recipe ids live here. The displayed name and the ingredient text are
 * translated, so they are stored in the i18n message files under the `recipes`
 * namespace using the keys `recipes.<id>.name` and `recipes.<id>.content`.
 * See {@link getRecipeExamples}.
 */
import { get } from 'svelte/store';
import { dictionary } from 'svelte-i18n';

/** Fallback locale used when the requested one has no loaded messages yet. */
const FALLBACK_LOCALE = 'en-US';

export type RecipeExample = {
	id: string;
	/** Already-translated display name for the requested locale. */
	name: string;
	/** Already-translated ingredient text for the requested locale. */
	text: string;
};

/**
 * Ordered list of example recipe ids. The matching name and content are read
 * from the i18n dictionary at runtime (see {@link getRecipeExamples}).
 */
export const recipeExampleIds: string[] = ['quiche', 'apple_pie', 'ratatouille'];

/**
 * Deep-merges the reference messages under the locale messages,
 * so that a key translated only in some recipes still resolves.
 * Locale files may be partial (see {@link getRecipeExamples}),
 * and this mirrors the per-key fallback that svelte-i18n applies for `$_`.
 */
function mergeWithFallback(
	localeMessages: Record<string, unknown>,
	fallbackMessages: Record<string, unknown>
): Record<string, unknown> {
	const merged: Record<string, unknown> = { ...fallbackMessages };
	for (const [key, value] of Object.entries(localeMessages)) {
		const fallbackValue = merged[key];
		const bothAreObjects =
			typeof value === 'object' &&
			value !== null &&
			typeof fallbackValue === 'object' &&
			fallbackValue !== null;
		merged[key] = bothAreObjects
			? mergeWithFallback(
					value as Record<string, unknown>,
					fallbackValue as Record<string, unknown>
				)
			: value;
	}
	return merged;
}

/**
 * Resolve the example recipes for a given locale, reading each recipe's name
 * and ingredient text from the loaded i18n dictionary.
 *
 * The locale is the full svelte-i18n code (e.g. "en-US", "fr-FR").
 * Locale files are partial: a recipe may have only its `content` translated,
 * so the fallback locale is merged per key underneath the requested locale
 * instead of being used only when the locale has no messages at all.
 * Recipes still missing either a name or a content after the merge are skipped.
 *
 * @param locale Full locale code (eg. "en-US")
 * @param dictionaries The loaded i18n dictionaries. Defaults to the current
 *   svelte-i18n `$dictionary` value; pass the reactive `$dictionary` from a
 *   component so callers re-resolve when a locale's messages finish loading.
 * @returns the examples that have both a name and a content translation
 */
export function getRecipeExamples(
	locale: string,
	dictionaries: Record<string, unknown> = get(dictionary)
): RecipeExample[] {
	const messages = mergeWithFallback(
		(dictionaries[locale] ?? {}) as Record<string, unknown>,
		(dictionaries[FALLBACK_LOCALE] ?? {}) as Record<string, unknown>
	);
	const recipes = (messages['recipes'] ?? {}) as Record<string, unknown>;

	return recipeExampleIds
		.map((id) => {
			const entry = recipes[id];
			if (entry == null || typeof entry !== 'object') return null;
			const { name, content } = entry as Record<string, string>;
			if (name == null || content == null) return null;
			return { id, name, text: content };
		})
		.filter((ex): ex is RecipeExample => ex !== null);
}
