<!--
  Recipe Editor Page

  Main page for creating and editing recipes.
  Holds the shared state (ingredients + green-score) and orchestrates the
  computation. The row edition logic lives in `RecipeRowEditor` and the score
  display (logo + limitations) lives in `ScoreDisplay`.

  Features:
  - Dynamic ingredient lines (adds new line when typing in the last empty line)
  - Computes the green-score automatically after a delay of inactivity or on demand
-->
<script lang="ts">
	import { _ } from '$lib/i18n';
	import { page } from '$app/state';
	import RecipeRowEditor from '$lib/ui/RecipeRowEditor.svelte';
	import ScoreDisplay from '$lib/ui/ScoreDisplay.svelte';
	import { createEmptyIngredient } from '$lib/types/ingredient';
	import { addEmptyIngredientIfNeeded, countNonEmptyIngredients } from '$lib/types/ingredientsList';
	import type { IngredientsList } from '$lib/types/ingredientsList';
	import {
		isIngredientNotEmpty,
		ingredientSignature,
		type Ingredient
	} from '$lib/types/ingredient';
	import { computeGreenScore, type GreenScoreResponse } from '$lib/api/recipe';
	import { createBouncer, SUPERSEDED } from '$lib/api/bouncer';

	/**
	 * Initial ingredients coming from the `/add` page (passed via `goto` state).
	 * Falls back to a single empty line when no state is provided.
	 */
	function getInitialIngredients(): IngredientsList {
		const state = (page.state ?? {}) as { ingredients?: Ingredient[] };
		const stateIngredients = state.ingredients;
		if (stateIngredients && stateIngredients.length > 0) {
			// we need an empty line at the end for the user to add new ingredients
			return addEmptyIngredientIfNeeded(stateIngredients);
		}
		return [createEmptyIngredient()];
	}

	// --- Shared state -------------------------------------------------------
	// Recipe state - starts with one empty ingredient line, or with parsed ingredients from /add
	let ingredients = $state<IngredientsList>(getInitialIngredients());

	// --- Green-score state -------------------------------------------------
	// The latest computed score response (null until computed or while loading).
	let greenScore = $state<GreenScoreResponse | null>(null);
	let isScoreLoading = $state(false);
	let scoreError = $state<string | null>(null);
	let currentScoreRequestController = $state<AbortController | null>(null);

	/**
	 * Guard ensuring only the most recent green-score request is applied.
	 *
	 * The score is recomputed automatically after an inactivity delay, so
	 * several requests can overlap. Without this guard, a slower earlier
	 * request could resolve after a faster later one and overwrite the fresher
	 * result with stale data.
	 */
	const scoreBouncer = createBouncer();

	/** Inactivity delay (in ms) before the green-score is recomputed automatically. */
	const SCORE_INACTIVITY_DELAY = 3000;

	/**
	 * Signature of the ingredients' relevant fields, used to detect changes and
	 * reset the inactivity timer.
	 */
	let ingredientsSignature = $derived(ingredients.map(ingredientSignature).join('|'));

	/**
	 * Total weight (in grams) of the non-empty ingredients sent to the backend.
	 */
	let totalWeight = $derived(
		ingredients.filter(isIngredientNotEmpty).reduce((sum, i) => sum + (i.weight ?? 0), 0)
	);

	/**
	 * Total weight (in grams) of the ingredients that were ignored by the
	 * backend (i.e. whose id appears in the missing list of the last response).
	 */
	let ignoredWeight = $derived.by(() => {
		if (!greenScore) return 0;
		const missing = new Set(greenScore.missingIngredientIds);
		return ingredients
			.filter((i) => missing.has(i.id))
			.reduce((sum, i) => sum + (i.weight ?? 0), 0);
	});

	/** Number of non-empty ingredients currently in the editor. */
	let nonEmptyIngredientCount = $derived(countNonEmptyIngredients(ingredients));

	/**
	 * Compute the green-score for the current ingredients.
	 *
	 * Guards against concurrent computations: only the result of the most recent
	 * call is applied, earlier (stale) results are discarded. Captures errors
	 * from the latest call only.
	 */
	async function fetchGreenScore() {
		currentScoreRequestController?.abort();  // abort previous request
		// Only compute when there is at least one non-empty ingredient
		if (!ingredients.some(isIngredientNotEmpty)) {
			currentScoreRequestController = null;
			isScoreLoading = false;
			greenScore = null;
			isScoreLoading = false;
			return;
		}
		const requestController = new AbortController();
		currentScoreRequestController = requestController;
		isScoreLoading = true;
		scoreError = null;
		try {
			greenScore = await computeGreenScore(ingredients, requestController.signal);
		} catch (e) {
			if (e instanceof DOMException && e.name === 'AbortError') return;
			scoreError = e instanceof Error ? e.message : 'An error occurred';
			greenScore = null;
		} finally {
			if (currentScoreRequestController === requestController) {
				currentScoreRequestController = null;
				isScoreLoading = false;
			}
		}
	}

	// Reset the inactivity timer whenever the ingredients change.
	// After the delay without edits, the score is recomputed automatically.
	$effect(() => {
		// Read the signature so the effect re-runs on any ingredient change
		void ingredientsSignature;
		const timer = setTimeout(fetchGreenScore, SCORE_INACTIVITY_DELAY);
		return () => clearTimeout(timer);
	});
</script>

<svelte:head>
	<title>{$_('recipe.title', { default: 'Recipe Editor' })}</title>
</svelte:head>

<div class="mx-auto max-w-7xl px-4 py-8">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold">{$_('recipe.title', { default: 'Recipe Editor' })}</h1>
		<p class="text-base-content/70 mt-2">
			{$_('recipe.description', { default: 'Add ingredients to your recipe' })}
		</p>
	</div>

	<!-- Ingredients List (row edition logic delegated to RecipeRowEditor) -->
	<RecipeRowEditor bind:ingredients />

	<!-- Actions -->
	<div class="mt-6 flex items-center gap-4">
		<button
			class="btn btn-primary"
			onclick={fetchGreenScore}
			disabled={isScoreLoading || !ingredients.some(isIngredientNotEmpty)}
		>
			{#if isScoreLoading}
				<span class="loading loading-spinner loading-sm"></span>
			{/if}
			{$_('recipe.compute_score', { default: 'Compute score' })}
		</button>
	</div>

	<!-- Summary -->
	<div class="bg-base-200 mt-8 rounded-lg p-4">
		<h2 class="text-lg font-semibold">{$_('recipe.summary', { default: 'Summary' })}</h2>
		<p class="text-base-content/70 mt-1">
			{nonEmptyIngredientCount}
			{$_('recipe.ingredients_count', { default: 'ingredient(s) added' })}
		</p>
	</div>

	<!-- Green Score display (logo + limitations) -->
	<ScoreDisplay
		score={greenScore}
		totalIngredientCount={nonEmptyIngredientCount}
		{totalWeight}
		{ignoredWeight}
		isLoading={isScoreLoading}
		error={scoreError}
	/>
</div>
