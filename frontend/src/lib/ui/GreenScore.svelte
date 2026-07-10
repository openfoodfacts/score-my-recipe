<!--
  GreenScore.svelte

  Displays the computed green-score of a recipe: the score logo (matching the
  letter grade returned by the backend) together with the number of ignored
  ingredients and the percentage of the total weight they represent.

  Props:
  - letterGrade: The letter grade ("A+", "A", ... "F"), or null if unavailable.
  - numericScore: The numeric score (0-100), or null.
  - ignoredIngredientIds: The ids of ingredients that were ignored.
  - totalIngredientCount: The total number of ingredients sent to the backend.
  - ignoredWeight: The total weight (in grams) of the ignored ingredients.
  - totalWeight: The total weight (in grams) of all sent ingredients.
  - isLoading: Whether the score is currently being computed.
  - error: An error message, if the computation failed.
-->
<script lang="ts">
	import { _ } from '$lib/i18n';

	type Props = {
		letterGrade?: string | null;
		numericScore?: number | null;
		ignoredIngredientIds?: string[];
		totalIngredientCount?: number;
		ignoredWeight?: number;
		totalWeight?: number;
		isLoading?: boolean;
		error?: string | null;
	};

	let {
		letterGrade = null,
		numericScore = null,
		ignoredIngredientIds = [],
		totalIngredientCount = 0,
		ignoredWeight = 0,
		totalWeight = 0,
		isLoading = false,
		error = null
	}: Props = $props();

	// Map each green-score SVG asset to its letter grade key.
	// Keys use a lowercase, hyphenated form of the grade (e.g. "A+" -> "a-plus").
	const scoreLogos = import.meta.glob<string>('$lib/assets/green-score/green-score-*.svg', {
		eager: true,
		query: '?url',
		import: 'default'
	});

	/**
	 * Convert a letter grade to the asset key used in the file names.
	 * @param grade - The letter grade (e.g. "A+", "B").
	 * @returns The asset key (e.g. "a-plus", "b").
	 */
	function gradeToAssetKey(grade: string): string {
		return grade.toLowerCase().replace('+', '-plus');
	}

	/** Resolve the SVG URL for the current letter grade, falling back to "unknown". */
	let scoreLogoUrl = $derived.by(() => {
		const key = letterGrade ? gradeToAssetKey(letterGrade) : 'unknown';
		const matching = Object.entries(scoreLogos).find(([path]) =>
			path.endsWith(`green-score-${key}.svg`)
		);
		return matching?.[1] ?? scoreLogos['green-score-unknown.svg'] ?? '';
	});

	/** Number of ignored ingredients. */
	let ignoredCount = $derived(ignoredIngredientIds.length);

	/** Percentage of the total weight that the ignored ingredients represent. */
	let ignoredWeightPercent = $derived(
		totalWeight > 0 ? Math.round((ignoredWeight / totalWeight) * 100) : 0
	);
</script>

<div class="bg-base-200 rounded-lg p-4">
	<h2 class="text-lg font-semibold">
		{$_('recipe.green_score', { default: 'Green Score' })}
	</h2>

	{#if isLoading}
		<div class="flex items-center gap-3 py-4">
			<span class="loading loading-spinner loading-lg"></span>
			<span>{$_('recipe.computing', { default: 'Computing score...' })}</span>
		</div>
	{:else if error}
		<div class="alert alert-error mt-2">
			<span>{error}</span>
		</div>
	{:else if letterGrade}
		<!-- Score logo -->
		<div class="mt-2 flex flex-col items-center gap-2">
			<img src={scoreLogoUrl} alt={letterGrade} class="h-32" />
			{#if numericScore !== null}
				<span class="text-base-content/70 text-sm">
					{$_('recipe.numeric_score', { default: 'Score' })}: {numericScore.toFixed(1)}/100
				</span>
			{/if}
		</div>

		<!-- Ignored ingredients summary -->
		{#if totalIngredientCount > 0}
			<div class="text-base-content/70 mt-3 text-sm">
				<p>
					<strong>{ignoredCount}</strong>
					{$_('recipe.ignored_ingredients', { default: 'ingredient(s) ignored' })}
				</p>
				<p>
					<strong>{ignoredWeightPercent}%</strong>
					{$_('recipe.ignored_weight', { default: 'of total weight' })}
				</p>
			</div>
		{/if}
	{:else}
		<p class="text-base-content/70 mt-2 text-sm">
			{$_('recipe.no_score', {
				default: 'No score available. Add ingredients with weights to compute the score.'
			})}
		</p>
	{/if}
</div>
