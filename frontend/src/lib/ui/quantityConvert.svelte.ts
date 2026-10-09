/**
 * @fileoverview Reactive quantity-convert and compatible-units logic.
 *
 * Extracted from IngredientLine.svelte to keep the component focused on
 * layout and presentation.
 *
 * Both factory functions must be called during component initialization
 * (they register ``$effect`` runes). In Svelte 5, ``$effect`` and ``$state``
 * are usable in ``.svelte.ts`` modules — the runes are scoped to the
 * function call, not the module, so each ingredient line gets its own
 * independent state.
 *
 * @see https://svelte.dev/docs/svelte/$state  — runes in .svelte.ts modules
 * @see https://svelte.dev/docs/svelte/$effect — cleanup via returned function
 */
import { isIngredientEmpty, type Ingredient, type TaxonomyItem } from '$lib/types/ingredient';
import { convertToG } from '$lib/api/recipe';
import { getCompatibleUnits, getLocaleKey } from '$lib/api/taxonomy';
import { GRAM_UNIT_ID, isGramUnit, unitToApiString } from '$lib/api/units';

/** Debounce delay (ms) before firing the convert-quantity API call. */
const CONVERT_DELAY = 400;

/**
 * Owns the convert lifecycle for a single ingredient's
 * quantity→grams conversion.
 *
 * Keeps the last converted ``(value, unit, ingredient_id)`` as a lightweight
 * guard to skip redundant API calls, debounces API calls on value/unit/
 * ingredient changes (except the gram unit, which is an identity), and aborts
 * superseded requests.
 *
 * The returned object exposes reactive getters that the component can read
 * in its template for the loading/error UI.  Reactivity is preserved
 * through the getters: reading them inside a template or ``$derived``
 * tracks the underlying ``$state`` signals.
 *
 * @param ingredient - The bindable ingredient object (mutated in place).
 * @returns Reactive getters for ``isConverting`` and ``convertError``.
 */
export function createQuantityConvert(ingredient: Ingredient) {
	// --- Last-converted guard ------------------------------------------------
	// The last (value, unit, ingredient_id) that was converted (or handled
	// locally). Initialized from the parsed ingredient so the first render
	// preserves the parser's quantity_g without an unnecessary API call.
	// Updated after each successful convert (and by the gram-unit local effect
	// and the null-quantity shortcut below).
	let lastValue = $state<number | null>(ingredient.quantityValue);
	let lastUnit = $state<string | null>(unitToApiString(ingredient.quantityUnit));
	let lastIngredientId = $state<string | null>(ingredient.codifiedIngredient?.id ?? null);

	// --- Convert state -------------------------------------------------------
	let isConverting = $state(false);
	let convertError = $state(false);
	let convertController: AbortController | null = null;
	let convertTimer: ReturnType<typeof setTimeout> | null = null;

	/**
	 * Keep the grams (weight) in sync with the quantity value when the unit
	 * is the gram unit. This is the only live conversion (no API call): for
	 * the gram unit, grams *are* the quantity value.
	 *
	 * Also updates the last-converted guard so the next non-gram convert
	 * has the correct baseline.
	 */
	$effect(() => {
		// Empty placeholder lines are skipped:
		// writing the weight would make the line count as "non-empty"
		// which in turn would trigger the addition of a new empty line
		// and so one without end.
		if (isIngredientEmpty(ingredient)) return;

		if (isGramUnit(ingredient.quantityUnit)) {
			ingredient.weight = ingredient.quantityValue;
			lastValue = ingredient.quantityValue;
			lastUnit = GRAM_UNIT_ID;
			lastIngredientId = ingredient.codifiedIngredient?.id ?? null;
		}
	});

	/**
	 * Debounced convert-quantity effect.
	 *
	 * Fires when the user changes the quantity value, the unit, or the
	 * codified ingredient (except for the gram unit, handled by the local
	 * effect above). Skips when the current values match the last-converted
	 * state (nothing to convert). When the quantity is cleared (null), sets
	 * grams to 0 immediately without an API call.
	 */
	$effect(() => {
		const currentValue = ingredient.quantityValue;
		const currentUnit = ingredient.quantityUnit;
		const currentUnitStr = unitToApiString(currentUnit);
		const currentIngredientId = ingredient.codifiedIngredient?.id ?? null;

		// Empty placeholder lines are skipped:
		// writing the weight would make the line count as "non-empty"
		// which in turn would trigger the addition of a new empty line
		// and so one without end.
		if (isIngredientEmpty(ingredient)) return;

		// Skip the gram-unit shortcut (handled by the local $effect above)
		if (isGramUnit(currentUnit)) return;

		// Cleared quantity: skip the API call, set grams to 0
		if (currentValue === null) {
			if (convertTimer) {
				clearTimeout(convertTimer);
				convertTimer = null;
			}
			ingredient.weight = 0;
			lastValue = null;
			lastUnit = currentUnitStr;
			lastIngredientId = currentIngredientId;
			convertError = false;
			return;
		}

		// Skip if nothing changed from the last-converted state
		if (
			currentValue === lastValue &&
			currentUnitStr === lastUnit &&
			currentIngredientId === lastIngredientId
		)
			return;

		// Debounce the conversion
		if (convertTimer) clearTimeout(convertTimer);
		convertTimer = setTimeout(() => {
			convertTimer = null;
			void doConvert();
		}, CONVERT_DELAY);
	});

	/**
	 * Perform the convert-quantity API call.
	 *
	 * Aborts any in-flight request, sends the current ``(value, unit,
	 * ingredient_id)`` to the stateless convert-to-g endpoint. On success,
	 * updates the grams and the last-converted guard. On 422 (unsupported
	 * conversion), sets the error indicator and keeps grams frozen at the
	 * last good value. On abort (superseded by a newer request), does nothing.
	 */
	async function doConvert() {
		convertController?.abort();

		const value = ingredient.quantityValue ?? 0;
		const unit = unitToApiString(ingredient.quantityUnit);
		const ingredientId = ingredient.codifiedIngredient?.id ?? null;

		// Guard: nothing to convert
		if (value === lastValue && unit === lastUnit && ingredientId === lastIngredientId) return;

		const controller = new AbortController();
		convertController = controller;
		isConverting = true;
		convertError = false;

		try {
			const quantityG = await convertToG(value, unit, ingredientId, controller.signal);

			// Only apply if this is still the latest request
			if (convertController !== controller) return;

			ingredient.weight = quantityG;
			lastValue = value;
			lastUnit = unit;
			lastIngredientId = ingredientId;
			convertError = false;
		} catch (e) {
			if (e instanceof DOMException && e.name === 'AbortError') return;
			// Only set error if this is still the latest request
			if (convertController !== controller) return;
			convertError = true;
			// Grams stay frozen at the last good value (ingredient.weight)
		} finally {
			if (convertController === controller) {
				convertController = null;
				isConverting = false;
			}
		}
	}

	// Clean up pending timers and in-flight requests on component destroy.
	// This $effect has no tracked dependencies, so it runs once on mount
	// and the returned cleanup function fires on destroy.
	$effect(() => {
		return () => {
			if (convertTimer) clearTimeout(convertTimer);
			convertController?.abort();
		};
	});

	return {
		get isConverting() {
			return isConverting;
		},
		get convertError() {
			return convertError;
		}
	};
}

/**
 * Owns the compatible-units list for a single ingredient.
 *
 * Whenever the ingredient's codified ingredient changes, fetches the list of
 * compatible units from the backend (driven by the ingredient's density and
 * average_weight_per_unit properties). Falls back to null (all units) when no
 * ingredient id is available or the fetch fails, so the user is never stuck
 * with an empty dropdown.
 *
 * @param ingredient - The bindable ingredient object.
 * @returns A reactive getter for ``compatibleUnits``.
 */
export function createCompatibleUnits(ingredient: Ingredient) {
	// The filtered list of units compatible with the current ingredient.
	// When null, the Tags component falls back to fetching all units.
	let compatibleUnits = $state<TaxonomyItem[] | null>(null);

	/**
	 * Fetch the compatible units list from the backend and update the state.
	 *
	 * On error, falls back to null (all units) so the user is not stuck
	 * with an empty dropdown.
	 */
	async function fetchCompatibleUnits(ingredientId: string | null) {
		try {
			const units = await getCompatibleUnits(getLocaleKey(), ingredientId);
			compatibleUnits = units;
		} catch (e) {
			console.error('Failed to fetch compatible units', e);
			compatibleUnits = null;
		}
	}

	/**
	 * Fetch compatible units whenever the codified ingredient changes.
	 * Falls back to null (all units) when no ingredient id is available.
	 */
	$effect(() => {
		// codifiedIngredient?.id is string | null | undefined; normalize to string | null
		const codifiedId = ingredient.codifiedIngredient?.id ?? null;

		if (codifiedId === null) {
			compatibleUnits = null;
			return;
		}

		// Fetch compatible units (async — the state updates when the fetch completes)
		void fetchCompatibleUnits(codifiedId);
	});

	return {
		get compatibleUnits() {
			return compatibleUnits;
		}
	};
}
