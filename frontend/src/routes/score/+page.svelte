<!--
  Recipe Editor Page

  Main page for creating and editing recipes.
  Holds the shared state (recipe metadata + ingredients + green-score) and
  orchestrates the computation. The row edition logic lives in
  `RecipeRowEditor` and the score display (logo + limitations) lives in
  `ScoreDisplay`.

  Features:
  - Editable recipe title and description at the top (metadata only, not scored)
  - Dynamic ingredient lines (adds new line when typing in the last empty line)
  - Computes the green-score automatically after a delay of inactivity or on demand
  - Saves recipes to localStorage through the save action, and can open a saved
    recipe from `/score?recipe=<id>` (loading handled by `createSavedRecipeSession`)
-->
<script lang="ts">
	import { _ } from '$lib/i18n';
	import { page } from '$app/state';
	import { replaceState } from '$app/navigation';
	import RecipeRowEditor from '$lib/ui/RecipeRowEditor.svelte';
	import ScoreDisplay from '$lib/ui/ScoreDisplay.svelte';
	import CountrySelect from '$lib/ui/CountrySelect.svelte';
	import RecipeDetailsFields from '$lib/ui/RecipeDetailsFields.svelte';
	import SaveRecipeAction from '$lib/ui/SaveRecipeAction.svelte';
	import { createEmptyIngredient } from '$lib/types/ingredient';
	import { addEmptyIngredientIfNeeded, countNonEmptyIngredients } from '$lib/types/ingredientsList';
	import type { IngredientsList } from '$lib/types/ingredientsList';
	import type { RecipeDraft } from '$lib/types/recipe';
	import type { SavedRecipe } from '$lib/types/savedRecipe';
	import { isIngredientNotEmpty, ingredientSignature } from '$lib/types/ingredient';
	import { computeGreenScore, type GreenScoreResponse } from '$lib/api/recipe';
	import { getLocale as getLocaleKey } from '$lib/i18n';
	import { createSavedRecipeSession } from '$lib/stores/savedRecipeSession.svelte';

	/**
	 * Draft recipe coming from the `/add` page (passed via `goto` state).
	 * Empty when the editor is opened directly.
	 */
	const initialDraft = (page.state ?? {}) as Partial<RecipeDraft>;

	/**
	 * Initial ingredients from the draft. Falls back to a single empty line
	 * when no state is provided.
	 */
	function getInitialIngredients(): IngredientsList {
		const stateIngredients = initialDraft.ingredients;
		if (stateIngredients && stateIngredients.length > 0) {
			// we need an empty line at the end for the user to add new ingredients
			return addEmptyIngredientIfNeeded(stateIngredients);
		}
		return [createEmptyIngredient()];
	}

	// --- Shared state -------------------------------------------------------
	// Recipe metadata: editable here and pre-filled from /add. It is not sent
	// to the score API and does not trigger a recomputation.
	let title = $state(initialDraft.title ?? '');
	let description = $state(initialDraft.description ?? '');

	// Recipe state - starts with one empty ingredient line, or with parsed ingredients from /add
	let ingredients = $state<IngredientsList>(getInitialIngredients());

	// Country the recipe is being cooked in (ISO 3166-1 alpha-2 code, or null).
	// Used to compute the distance modifier in the green-score.
	let country = $state<string | null>(null);

	// --- Green-score state -------------------------------------------------
	// The latest computed score response (null until computed or while loading).
	let greenScore = $state<GreenScoreResponse | null>(null);
	let isScoreLoading = $state(false);
	let scoreError = $state<string | null>(null);
	let currentScoreRequestController = $state<AbortController | null>(null);

	/**
	 * Signature of the ingredients' relevant fields plus the selected country,
	 * used to detect changes and reset the inactivity timer. The country is
	 * included because it influences the distance modifier (and thus the score).
	 */
	let ingredientsSignature = $derived(
		`${ingredients.map(ingredientSignature).join('|')}@${country ?? ''}`
	);

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
	 * Ingredient ids flagged as missing in the last computed score.
	 *
	 * Cleared while a recomputation is in flight (see `isScoreLoading`) so the
	 * highlight always reflects the currently displayed score, never a stale one.
	 */
	let missingIngredientIds = $derived(
		isScoreLoading || !greenScore ? [] : greenScore.missingIngredientIds
	);

	/**
	 * Signature of the last successful score computation. Used by the
	 * inactivity effect to skip a recomputation that would duplicate a fresh
	 * result (for example right after opening or saving a recipe).
	 */
	let lastComputedSignature: string | null = null;

	/** Inactivity delay (in ms) before the green-score is recomputed automatically. */
	const SCORE_INACTIVITY_DELAY = 3000;

	// --- Saved-recipe session ----------------------------------------------

	/** Apply a stored recipe to the editor and request a fresh score. */
	function onRecipeLoaded(recipe: SavedRecipe) {
		title = recipe.title;
		description = recipe.description;
		ingredients =
			recipe.ingredients.length > 0
				? addEmptyIngredientIfNeeded(recipe.ingredients)
				: [createEmptyIngredient()];
		country = recipe.country;
		greenScore = null;
		scoreError = null;
		lastComputedSignature = null;
		void fetchGreenScore();
	}

	/** Reset the editor to a blank draft when no saved recipe is selected. */
	function onBlankDraft() {
		// Stop an in-flight score so it cannot populate the new blank draft.
		currentScoreRequestController?.abort();
		currentScoreRequestController = null;
		isScoreLoading = false;
		title = '';
		description = '';
		ingredients = [createEmptyIngredient()];
		country = null;
		greenScore = null;
		scoreError = null;
		lastComputedSignature = null;
	}

	/**
	 * Tracks which saved recipe is open (`?recipe=<id>`) and exposes its id and
	 * title to the save action.
	 */
	const savedRecipeSession = createSavedRecipeSession({ onRecipeLoaded, onBlankDraft });

	// --- Score computation -------------------------------------------------

	/**
	 * Compute the green-score for the current ingredients.
	 *
	 * Guards against concurrent computations: only the result of the most recent
	 * call is applied, earlier (stale) results are discarded. Captures errors
	 * from the latest call only.
	 *
	 * @returns The fresh score response, or null when there is nothing to score,
	 *   the request failed, or it was aborted.
	 */
	async function fetchGreenScore(): Promise<GreenScoreResponse | null> {
		currentScoreRequestController?.abort(); // abort previous request
		// Only compute when there is at least one non-empty ingredient
		if (!ingredients.some(isIngredientNotEmpty)) {
			currentScoreRequestController = null;
			isScoreLoading = false;
			greenScore = null;
			scoreError = null;
			return null;
		}
		const requestController = new AbortController();
		currentScoreRequestController = requestController;
		isScoreLoading = true;
		scoreError = null;
		const signature = ingredientsSignature;
		try {
			const result = await computeGreenScore(ingredients, {
				country: country ?? undefined,
				lang: getLocaleKey(),
				signal: requestController.signal
			});
			greenScore = result;
			lastComputedSignature = signature;
			return result;
		} catch (e) {
			if (e instanceof DOMException && e.name === 'AbortError') return null;
			scoreError = e instanceof Error ? e.message : 'An error occurred';
			greenScore = null;
			return null;
		} finally {
			if (currentScoreRequestController === requestController) {
				currentScoreRequestController = null;
				isScoreLoading = false;
			}
		}
	}

	/**
	 * Compute the score that will be persisted with the recipe.
	 *
	 * Unlike `fetchGreenScore`, this is awaited by the save action and reports
	 * failures so the recipe can still be saved without a score.
	 */
	async function computeScoreForSave(signal: AbortSignal): Promise<{
		score: GreenScoreResponse | null;
		failed: boolean;
		aborted: boolean;
	}> {
		// Cancel an automatic recomputation: its result could otherwise arrive
		// after the fresh score and replace it.
		currentScoreRequestController?.abort();
		currentScoreRequestController = null;
		isScoreLoading = false;

		if (!ingredients.some(isIngredientNotEmpty)) {
			greenScore = null;
			scoreError = null;
			lastComputedSignature = ingredientsSignature;
			return { score: null, failed: false, aborted: false };
		}

		const signature = ingredientsSignature;
		try {
			const score = await computeGreenScore(ingredients, {
				country: country ?? undefined,
				lang: getLocaleKey(),
				signal
			});
			greenScore = score;
			scoreError = null;
			lastComputedSignature = signature;
			return { score, failed: false, aborted: false };
		} catch (e) {
			if (e instanceof DOMException && e.name === 'AbortError') {
				return { score: null, failed: false, aborted: true };
			}
			greenScore = null;
			scoreError = e instanceof Error ? e.message : 'An error occurred';
			return { score: null, failed: true, aborted: false };
		}
	}

	// Reset the inactivity timer whenever the ingredients change.
	// After the delay without edits, the score is recomputed automatically.
	$effect(() => {
		// Read the signature so the effect re-runs on any ingredient change
		void ingredientsSignature;
		const timer = setTimeout(() => {
			// Skip when the displayed score already matches the current content
			// (e.g. immediately after opening or saving a recipe).
			if (ingredientsSignature !== lastComputedSignature) {
				void fetchGreenScore();
			}
		}, SCORE_INACTIVITY_DELAY);
		return () => clearTimeout(timer);
	});

	// Abort any in-flight score computation when leaving the page.
	$effect(() => {
		return () => currentScoreRequestController?.abort();
	});

	// --- Save flow ---------------------------------------------------------

	/**
	 * Sync the page after a successful save.
	 *
	 * The session now identifies the saved recipe, the dialog title becomes the
	 * editor title, and the URL points at the recipe so a refresh reopens it.
	 */
	function handleSaved(recipe: SavedRecipe) {
		savedRecipeSession.markSaved(recipe);
		title = recipe.title;
		replaceState(`/score?recipe=${encodeURIComponent(recipe.id)}`, {});
	}
</script>

<svelte:head>
	<title>{title.trim() || $_('recipe.title', { default: 'Recipe Editor' })}</title>
</svelte:head>

{#if savedRecipeSession.isLoading}
	<div class="mx-auto flex max-w-7xl justify-center px-4 py-20">
		<span class="loading loading-spinner loading-lg"></span>
	</div>
{:else}
	<div class="mx-auto max-w-7xl px-4 py-8">
		{#if savedRecipeSession.missingRecipe}
			<div class="alert alert-warning mb-6" role="alert">
				<span>
					{$_('recipe.saved_not_found', {
						default: 'This saved recipe could not be found. It may have been deleted.'
					})}
				</span>
			</div>
		{/if}

		<!-- Recipe details (replace the former static header) -->
		<div class="mb-8">
			<h1 class="sr-only">{title.trim() || $_('recipe.title', { default: 'Recipe Editor' })}</h1>
			<RecipeDetailsFields bind:title bind:description headingTitle />
		</div>

		<!-- Ingredients List (row edition logic delegated to RecipeRowEditor) -->
		<RecipeRowEditor bind:ingredients {missingIngredientIds} />

		<!-- Actions -->
		<div class="mt-6 flex flex-wrap items-end gap-4">
			<CountrySelect bind:value={country} />
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
			<SaveRecipeAction
				{title}
				{description}
				{ingredients}
				{country}
				savedRecipeId={savedRecipeSession.savedRecipeId}
				savedRecipeTitle={savedRecipeSession.savedRecipeTitle}
				computeFreshScore={computeScoreForSave}
				onsaved={handleSaved}
			/>
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
{/if}
