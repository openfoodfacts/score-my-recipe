<!--
  EcobalyseScore.svelte

  Visual component to display the Coût Environnemental score (from Ecobalyse food2 engine).
  Displays the main environmental cost in points (Pts), per-kg / per-portion values,
  sub-impact indicators (climate, water, biodiversity), and a link to the Ecobalyse simulator.
-->
<script lang="ts">
	import { _ } from '$lib/i18n';
	import type { EcobalyseScoreResponse } from '$lib/api/recipe';

	type Props = {
		score: EcobalyseScoreResponse;
	};

	let { score }: Props = $props();

	/** Formatted total environmental cost */
	let formattedCost = $derived(
		score.environmentalCost !== null && score.environmentalCost !== undefined
			? score.environmentalCost.toFixed(score.environmentalCost < 1 ? 2 : 1)
			: '-'
	);

	/** Formatted cost per kg */
	let formattedCostPerKg = $derived(
		score.environmentalCostPerKg !== null && score.environmentalCostPerKg !== undefined
			? score.environmentalCostPerKg.toFixed(1)
			: null
	);

	/** Formatted cost per serving */
	let formattedCostPerServing = $derived(
		score.environmentalCostPerServing !== null && score.environmentalCostPerServing !== undefined
			? score.environmentalCostPerServing.toFixed(1)
			: null
	);

	/** Key impact breakdown values */
	let climateImpact = $derived(score.impacts?.cch);
	let biodiversityImpact = $derived(score.impacts?.bvi);
	let waterImpact = $derived(score.impacts?.wtu);
</script>

<div class="space-y-4">
	<!-- Primary Cost Badge / Metric -->
	<div
		class="bg-base-100 border-base-300 flex flex-col items-center justify-between gap-4 rounded-xl border p-5 shadow-sm md:flex-row"
	>
		<div class="flex items-center gap-4">
			<div
				class="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-2xl font-bold text-emerald-700 shadow-inner"
			>
				🌱
			</div>
			<div>
				<div class="text-base-content/60 text-xs font-semibold tracking-wider uppercase">
					{$_('recipe.environmental_cost', { default: 'Coût Environnemental' })}
				</div>
				<div class="flex items-baseline gap-2">
					<span class="text-3xl font-extrabold text-emerald-800 dark:text-emerald-400">
						{formattedCost}
					</span>
					<span class="text-base-content/70 text-sm font-semibold">
						{$_('recipe.points_unit', { default: 'points d’impact' })}
					</span>
				</div>
			</div>
		</div>

		<!-- Per-unit metrics -->
		<div
			class="border-base-300 flex items-center gap-6 border-t pt-3 text-sm md:border-t-0 md:border-l md:pt-0 md:pl-6"
		>
			{#if formattedCostPerKg !== null}
				<div>
					<span class="text-base-content/60 block text-xs">
						{$_('recipe.per_kg', { default: 'Par kg' })}
					</span>
					<span class="text-base font-bold">
						{formattedCostPerKg} <span class="text-xs font-normal">pts/kg</span>
					</span>
				</div>
			{/if}

			{#if formattedCostPerServing !== null}
				<div>
					<span class="text-base-content/60 block text-xs">
						{$_('recipe.per_serving', { default: 'Par portion' })}
					</span>
					<span class="text-base font-bold">
						{formattedCostPerServing} <span class="text-xs font-normal">pts/portion</span>
					</span>
				</div>
			{/if}
		</div>
	</div>

	<!-- Multi-criteria Breakdown -->
	{#if score.impacts}
		<div class="bg-base-100 border-base-300 rounded-lg border p-4">
			<h3 class="text-base-content/80 mb-3 text-sm font-semibold">
				{$_('recipe.impacts_breakdown', { default: 'Détail des impacts environnementaux' })}
			</h3>
			<div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
				<!-- Climate -->
				{#if climateImpact !== undefined}
					<div class="bg-base-200/60 rounded-lg p-3">
						<span class="text-base-content/60 block text-xs">
							{$_('recipe.climate_impact', { default: 'Climat / Carbone' })}
						</span>
						<span class="text-sm font-bold">
							{climateImpact.toFixed(2)} <span class="text-xs font-normal">kg CO₂ eq</span>
						</span>
					</div>
				{/if}

				<!-- Biodiversity -->
				{#if biodiversityImpact !== undefined}
					<div class="bg-base-200/60 rounded-lg p-3">
						<span class="text-base-content/60 block text-xs">
							{$_('recipe.biodiversity_impact', { default: 'Biodiversité' })}
						</span>
						<span class="text-sm font-bold">
							{biodiversityImpact.toFixed(3)} <span class="text-xs font-normal">BVI</span>
						</span>
					</div>
				{/if}

				<!-- Water -->
				{#if waterImpact !== undefined}
					<div class="bg-base-200/60 rounded-lg p-3">
						<span class="text-base-content/60 block text-xs">
							{$_('recipe.water_impact', { default: 'Ressources en eau' })}
						</span>
						<span class="text-sm font-bold">
							{waterImpact.toFixed(2)} <span class="text-xs font-normal">m³</span>
						</span>
					</div>
				{/if}
			</div>
		</div>
	{/if}

	<!-- Simulator link & warnings -->
	<div class="text-base-content/70 flex flex-wrap items-center justify-between gap-2 text-xs">
		<span>
			{$_('recipe.ecobalyse_methodology_note', {
				default:
					'Calculé selon le modèle Food2 d’Écobalyse (ADEME / Ministère de la Transition Écologique).'
			})}
		</span>
		{#if score.webUrl}
			<a
				href={score.webUrl}
				target="_blank"
				rel="noopener noreferrer"
				class="link link-primary inline-flex items-center gap-1 font-medium"
			>
				{$_('recipe.view_on_ecobalyse', { default: 'Ouvrir dans Écobalyse' })} ↗
			</a>
		{/if}
	</div>

	<!-- Warnings -->
	{#if score.warnings && score.warnings.length > 0}
		<div class="alert alert-warning mt-2 text-xs">
			<span>{score.warnings.join('. ')}</span>
		</div>
	{/if}
</div>
