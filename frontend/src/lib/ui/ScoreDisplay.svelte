<!--
  ScoreDisplay.svelte

  Displays the computed scores for a recipe with a methodology switcher:
  - Green-Score (PEF-based, 0-100 scale, letter grades A+ to F)
  - Coût Environnemental (Ecobalyse food2 engine, impact points)

  Props:
  - greenScore: The Green-Score response from the backend, or null.
  - ecobalyseScore: The Ecobalyse score response from the backend, or null.
  - score: Backward-compatible alias for greenScore.
  - activeMethod: Currently selected methodology ('green-score' | 'ecobalyse').
  - totalIngredientCount: The total number of ingredients sent to the backend.
  - ignoredWeight: The total weight (in grams) of the ignored ingredients (for Green-Score).
  - totalWeight: The total weight (in grams) of all sent ingredients.
  - isLoading: Whether scores are currently being computed.
  - error: An error message, if the computation failed.
-->
<script lang="ts">
	import { _ } from '$lib/i18n';
	import GreenScore from './GreenScore.svelte';
	import EcobalyseScore from './EcobalyseScore.svelte';
	import type { GreenScoreResponse, EcobalyseScoreResponse } from '$lib/api/recipe';

	type Methodology = 'green-score' | 'ecobalyse';

	type Props = {
		greenScore?: GreenScoreResponse | null;
		ecobalyseScore?: EcobalyseScoreResponse | null;
		score?: GreenScoreResponse | null; // backward compatibility
		activeMethod?: Methodology;
		totalIngredientCount?: number;
		ignoredWeight?: number;
		totalWeight?: number;
		isLoading?: boolean;
		error?: string | null;
	};

	let {
		greenScore = null,
		ecobalyseScore = null,
		score = null,
		activeMethod = $bindable<Methodology>('green-score'),
		totalIngredientCount = 0,
		ignoredWeight = 0,
		totalWeight = 0,
		isLoading = false,
		error = null
	}: Props = $props();

	/** Resolve active green-score (supporting either greenScore or score prop) */
	let resolvedGreenScore = $derived(greenScore ?? score);

	/** Number of ingredients ignored by Green-Score */
	let greenScoreIgnoredCount = $derived(resolvedGreenScore?.missingIngredientIds.length ?? 0);

	/** Percentage of total weight ignored by Green-Score */
	let greenScoreIgnoredWeightPercent = $derived(
		totalWeight > 0 ? Math.round((ignoredWeight / totalWeight) * 100) : 0
	);

	/** Number of ingredients ignored by Ecobalyse */
	let ecobalyseIgnoredCount = $derived(ecobalyseScore?.missingIngredientIds.length ?? 0);
</script>

<div class="bg-base-200 border-base-300 rounded-xl border p-5">
	<!-- Methodology Switcher Tabs -->
	<div class="border-base-300 mb-4 flex flex-wrap items-center justify-between gap-2 border-b pb-3">
		<div class="flex items-center gap-2">
			<h2 class="text-lg font-bold">
				{$_('recipe.score_results', { default: 'Scores environnementaux' })}
			</h2>
		</div>

		<div class="join bg-base-100 border-base-300 rounded-lg border p-0.5">
			<button
				type="button"
				class="join-item btn btn-sm {activeMethod === 'green-score' ? 'btn-primary' : 'btn-ghost'}"
				onclick={() => (activeMethod = 'green-score')}
			>
				{$_('recipe.green_score', { default: 'Green Score' })}
			</button>
			<button
				type="button"
				class="join-item btn btn-sm {activeMethod === 'ecobalyse' ? 'btn-primary' : 'btn-ghost'}"
				onclick={() => (activeMethod = 'ecobalyse')}
			>
				{$_('recipe.ecobalyse_title', { default: 'Écobalyse (Coût Env.)' })}
			</button>
		</div>
	</div>

	{#if error}
		<div class="alert alert-error mt-2">
			<span>{error}</span>
		</div>
	{:else if activeMethod === 'green-score'}
		<!-- Green-Score View -->
		{#if resolvedGreenScore?.letterGrade}
			<div class="mt-2" class:opacity-50={isLoading}>
				<GreenScore
					letterGrade={resolvedGreenScore.letterGrade}
					numericScore={resolvedGreenScore.numericScore}
				/>
			</div>

			<!-- Ignored ingredients summary for Green-Score -->
			{#if totalIngredientCount > 0}
				<div class="text-base-content/70 bg-base-100/60 mt-4 rounded-lg p-3 text-sm">
					<p>
						<strong>{totalIngredientCount - greenScoreIgnoredCount}</strong>
						{$_('recipe.accounted_ingredients', { default: 'ingrédient(s) pris en compte.' })}
						<strong>{greenScoreIgnoredCount}</strong>
						{$_('recipe.ignored_ingredients', { default: 'ingrédient(s) ignoré(s).' })}
					</p>
					<p>
						<strong>{greenScoreIgnoredWeightPercent}%</strong>
						{$_('recipe.ignored_weight', { default: 'du poids total' })}
					</p>
					<p class="mt-2 text-xs opacity-75">
						{$_('recipe.error_contact', {
							default: 'En cas de question ou d’erreur, contactez contact@openfoodfacts.org'
						})}
					</p>
				</div>
			{/if}
		{:else if isLoading}
			<div class="flex items-center justify-center gap-3 py-6">
				<span class="loading loading-spinner loading-lg text-primary"></span>
				<span class="font-medium"
					>{$_('recipe.computing', { default: 'Calcul du score en cours...' })}</span
				>
			</div>
		{:else}
			<p class="text-base-content/70 mt-2 text-sm">
				{$_('recipe.no_score', {
					default:
						'Aucun score disponible. Ajoutez des ingrédients avec des poids pour calculer le score.'
				})}
			</p>
		{/if}
	{:else if activeMethod === 'ecobalyse'}
		<!-- Ecobalyse View -->
		{#if ecobalyseScore && ecobalyseScore.environmentalCost !== null && ecobalyseScore.environmentalCost !== undefined}
			<div class="mt-2" class:opacity-50={isLoading}>
				<EcobalyseScore score={ecobalyseScore} />
			</div>

			<!-- Ignored ingredients summary for Ecobalyse -->
			{#if totalIngredientCount > 0}
				<div class="text-base-content/70 bg-base-100/60 mt-4 rounded-lg p-3 text-sm">
					<p>
						<strong>{totalIngredientCount - ecobalyseIgnoredCount}</strong>
						{$_('recipe.accounted_ingredients', { default: 'ingrédient(s) pris en compte.' })}
						<strong>{ecobalyseIgnoredCount}</strong>
						{$_('recipe.ignored_ingredients', { default: 'ingrédient(s) ignoré(s).' })}
					</p>
				</div>
			{/if}
		{:else if isLoading}
			<div class="flex items-center justify-center gap-3 py-6">
				<span class="loading loading-spinner loading-lg text-primary"></span>
				<span class="font-medium"
					>{$_('recipe.computing', { default: 'Calcul du score en cours...' })}</span
				>
			</div>
		{:else}
			<p class="text-base-content/70 mt-2 text-sm">
				{$_('recipe.no_ecobalyse_score', {
					default:
						'Aucun résultat Écobalyse disponible. Vérifiez que les ingrédients sont reconnus dans la base.'
				})}
			</p>
		{/if}
	{/if}

	<!-- In-flight toast -->
	{#if isLoading && (resolvedGreenScore || ecobalyseScore)}
		<div class="toast toast-center z-50">
			<div class="alert bg-base-100 border-base-300 border shadow-lg">
				<span class="loading loading-spinner loading-sm"></span>
				<span>{$_('recipe.computing', { default: 'Calcul du score...' })}</span>
			</div>
		</div>
	{/if}
</div>
