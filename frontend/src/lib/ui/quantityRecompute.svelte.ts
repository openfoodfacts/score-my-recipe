/**
 * @fileoverview Reactive quantity-recompute and compatible-units logic.
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
import { recomputeQuantity } from '$lib/api/recipe';
import { getCompatibleUnits, getLocaleKey } from '$lib/api/taxonomy';
import { GRAM_UNIT_ID, isGramUnit, unitToApiString } from '$lib/api/units';

/** Debounce delay (ms) before firing the recompute-quantity API call. */
const RECOMPUTE_DELAY = 400;

/**
 * Owns the reference state and recompute lifecycle for a single
 * ingredient's quantity→grams conversion.
 *
 * Keeps the last known-good ``(quantity_g, value, unit)`` as reference
 * state, debounces API calls on value/unit changes (except the gram unit,
 * which is an identity), and aborts superseded requests.
 *
 * The returned object exposes reactive getters that the component can read
 * in its template for the loading/error UI.  Reactivity is preserved
 * through the getters: reading them inside a template or ``$derived``
 * tracks the underlying ``$state`` signals.
 *
 * @param ingredient - The bindable ingredient object (mutated in place).
 * @returns Reactive getters for ``isRecomputing`` and ``recomputeError``.
 */
export function createQuantityRecompute(ingredient: Ingredient) {
	// --- Reference state ---------------------------------------------------
	// The last known-good (quantity_g, value, unit) from which the current
	// grams were derived. Initialized from the parsed ingredient on mount,
	// and updated after each successful recompute (and by the gram-unit
	// local effect below). This is the "old" state sent to the recompute
	// API on the next edit.
	let refQuantityG = $state(ingredient.weight ?? 0);
	let refValue = $state(ingredient.quantityValue ?? 0);
	let refUnit = $state(unitToApiString(ingredient.quantityUnit));

	// --- Recompute state ---------------------------------------------------
	let isRecomputing = $state(false);
	let recomputeError = $state(false);
	let recomputeController: AbortController | null = null;
	let recomputeTimer: ReturnType<typeof setTimeout> | null = null;

	/**
	 * Keep the grams (weight) in sync with the quantity value when the unit
	 * is the gram unit. This is the only live conversion (no API call): for
	 * the gram unit, grams *are* the quantity value.
	 *
	 * Also updates the reference state so the next non-gram recompute has
	 * the correct baseline.
	 *
	 */
	$effect(() => {
		// Empty placeholder lines are skipped:
		// writing the weight would make the line count as "non-empty"
		// which in turn would trigger the addition of a new empty line
		// and so one without end.
		if (isIngredientEmpty(ingredient)) return;

		if (isGramUnit(ingredient.quantityUnit)) {
			ingredient.weight = ingredient.quantityValue;
			refQuantityG = ingredient.quantityValue ?? 0;
			refValue = ingredient.quantityValue ?? 0;
			refUnit = GRAM_UNIT_ID;
		}
	});

	/**
	 * Debounced recompute-quantity effect.
	 *
	 * Fires when the user changes the quantity value or the unit (except
	 * for the gram unit, handled by the local effect above). Skips when
	 * the current values match the reference state (nothing to recompute).
	 * When the quantity is cleared (null), sets grams to 0 immediately
	 * without an API call.
	 */
	$effect(() => {
		const currentValue = ingredient.quantityValue;
		const currentUnit = ingredient.quantityUnit;
		const currentUnitStr = unitToApiString(currentUnit);

		// Empty placeholder lines are skipped:
		// writing the weight would make the line count as "non-empty"
		// which in turn would trigger the addition of a new empty line
		// and so one without end.
		if (isIngredientEmpty(ingredient)) return;

		// Skip the gram-unit shortcut (handled by the local $effect above)
		if (isGramUnit(currentUnit)) return;

		// Cleared quantity: skip the API call, set grams to 0
		if (currentValue === null) {
			if (recomputeTimer) {
				clearTimeout(recomputeTimer);
				recomputeTimer = null;
			}
			ingredient.weight = 0;
			refQuantityG = 0;
			refValue = 0;
			refUnit = currentUnitStr;
			recomputeError = false;
			return;
		}

		// Skip if nothing changed from the reference state
		if (currentValue === refValue && currentUnitStr === refUnit) return;

		// Debounce the recompute
		if (recomputeTimer) clearTimeout(recomputeTimer);
		recomputeTimer = setTimeout(() => {
			recomputeTimer = null;
			void doRecompute();
		}, RECOMPUTE_DELAY);
	});

	/**
	 * Perform the recompute-quantity API call.
	 *
	 * Aborts any in-flight request, sends the reference state as "old" and
	 * the current values as "new". On success, updates the grams and
	 * reference state. On 422 (unsupported conversion), sets the error
	 * indicator and keeps grams frozen at the last good value. On abort
	 * (superseded by a newer request), does nothing.
	 */
	async function doRecompute() {
		recomputeController?.abort();

		const newValue = ingredient.quantityValue ?? 0;
		const newUnit = unitToApiString(ingredient.quantityUnit);

		// Guard: nothing to recompute
		if (newValue === refValue && newUnit === refUnit) return;

		const controller = new AbortController();
		recomputeController = controller;
		isRecomputing = true;
		recomputeError = false;

		try {
			const response = await recomputeQuantity(
				{
					lang: getLocaleKey(),
					quantityG: refQuantityG,
					oldValue: refValue,
					oldUnit: refUnit,
					newValue,
					newUnit
				},
				controller.signal
			);

			// Only apply if this is still the latest request
			if (recomputeController !== controller) return;

			ingredient.weight = response.quantityG;
			refQuantityG = response.quantityG;
			refValue = response.value;
			refUnit = response.unit;
			recomputeError = false;
		} catch (e) {
			if (e instanceof DOMException && e.name === 'AbortError') return;
			// Only set error if this is still the latest request
			if (recomputeController !== controller) return;
			recomputeError = true;
			// Grams stay frozen at the last good value (refQuantityG / ingredient.weight)
		} finally {
			if (recomputeController === controller) {
				recomputeController = null;
				isRecomputing = false;
			}
		}
	}

	// Clean up pending timers and in-flight requests on component destroy.
	// This $effect has no tracked dependencies, so it runs once on mount
	// and the returned cleanup function fires on destroy.
	$effect(() => {
		return () => {
			if (recomputeTimer) clearTimeout(recomputeTimer);
			recomputeController?.abort();
		};
	});

	return {
		get isRecomputing() {
			return isRecomputing;
		},
		get recomputeError() {
			return recomputeError;
		}
	};
}

/**
 * Owns the compatible-units list for a single ingredient.
 *
 * Whenever the ingredient's unit or codified ingredient changes, fetches
 * the list of compatible units from the backend. Falls back to null (all
 * units) when the source unit is null or the fetch fails, so the user is
 * never stuck with an empty dropdown.
 *
 * @param ingredient - The bindable ingredient object.
 * @returns A reactive getter for ``compatibleUnits``.
 */
export function createCompatibleUnits(ingredient: Ingredient) {
	// The filtered list of units compatible with the current ingredient's
	// unit. When null, the Tags component falls back to fetching all units.
	let compatibleUnits = $state<TaxonomyItem[] | null>(null);

	/**
	 * Fetch the compatible units list from the backend and update the state.
	 *
	 * On error, falls back to null (all units) so the user is not stuck
	 * with an empty dropdown.
	 */
	async function fetchCompatibleUnits(sourceUnit: string, ingredientId: string | null) {
		try {
			const units = await getCompatibleUnits(getLocaleKey(), sourceUnit, ingredientId);
			compatibleUnits = units;
		} catch (e) {
			console.error('Failed to fetch compatible units', e);
			compatibleUnits = null;
		}
	}

	/**
	 * Fetch compatible units whenever the source unit or codified
	 * ingredient changes. Falls back to null (all units) when the source
	 * unit is null.
	 */
	$effect(() => {
		const unit = ingredient.quantityUnit;
		// codifiedIngredient?.id is string | null | undefined; normalize to string | null
		const codifiedId = ingredient.codifiedIngredient?.id ?? null;

		const sourceUnit = unit ? unitToApiString(unit) : null;

		if (sourceUnit === null) {
			compatibleUnits = null;
			return;
		}

		// Fetch compatible units (async — the state updates when the fetch completes)
		void fetchCompatibleUnits(sourceUnit, codifiedId);
	});

	return {
		get compatibleUnits() {
			return compatibleUnits;
		}
	};
}
