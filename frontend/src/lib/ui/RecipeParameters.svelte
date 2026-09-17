<!--
  RecipeParameters.svelte

  Optional recipe configuration for Ecobalyse food2 simulator:
  - Preparation technique (cuisson / préparation)
  - Distribution / Storage conditions (température ambiante, frais, surgelé)
  - Number of portions / servings
-->
<script lang="ts">
	import { _ } from '$lib/i18n';
	import type { RecipeEcobalyseParameters } from '$lib/api/recipe';

	type Props = {
		parameters?: RecipeEcobalyseParameters;
		onchange?: (params: RecipeEcobalyseParameters) => void;
	};

	let {
		parameters = $bindable<RecipeEcobalyseParameters>({
			distribution: 'ambient',
			preparation: [],
			servings: 1
		}),
		onchange
	}: Props = $props();

	let isOpen = $state(false);

	let selectedDistribution = $state(parameters.distribution ?? 'ambient');
	let selectedPreparation = $state(parameters.preparation?.[0] ?? '');
	let servings = $state(parameters.servings ?? 1);

	function updateParams() {
		const newParams: RecipeEcobalyseParameters = {
			distribution: selectedDistribution,
			preparation: selectedPreparation ? [selectedPreparation] : [],
			servings: Math.max(1, Number(servings) || 1)
		};
		parameters = newParams;
		onchange?.(newParams);
	}
</script>

<div class="collapse-arrow bg-base-200 border-base-300 collapse mb-6 rounded-xl border">
	<input type="checkbox" bind:checked={isOpen} />
	<div class="collapse-title flex items-center gap-2 text-sm font-semibold">
		<span>⚙️</span>
		<span
			>{$_('recipe.advanced_parameters', {
				default: 'Paramètres avancés de la recette (Écobalyse)'
			})}</span
		>
	</div>

	<div class="collapse-content space-y-4 pt-2">
		<div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
			<!-- Distribution / Storage -->
			<div class="form-control">
				<label class="label text-xs font-semibold" for="distribution-select">
					{$_('recipe.distribution_mode', { default: 'Conservation / Distribution' })}
				</label>
				<select
					id="distribution-select"
					class="select select-bordered select-sm w-full"
					bind:value={selectedDistribution}
					onchange={updateParams}
				>
					<option value="ambient">{$_('recipe.storage_ambient', { default: 'Ambiant' })}</option>
					<option value="fresh"
						>{$_('recipe.storage_fresh', { default: 'Frais / Réfrigéré' })}</option
					>
					<option value="frozen">{$_('recipe.storage_frozen', { default: 'Surgelé' })}</option>
				</select>
			</div>

			<!-- Preparation / Cooking -->
			<div class="form-control">
				<label class="label text-xs font-semibold" for="preparation-select">
					{$_('recipe.preparation_technique', { default: 'Mode de préparation / Cuisson' })}
				</label>
				<select
					id="preparation-select"
					class="select select-bordered select-sm w-full"
					bind:value={selectedPreparation}
					onchange={updateParams}
				>
					<option value="">{$_('recipe.prep_none', { default: 'Aucune / Cru' })}</option>
					<option value="pan-cooking"
						>{$_('recipe.prep_pan', { default: 'Poêle / Casserole' })}</option
					>
					<option value="oven">{$_('recipe.prep_oven', { default: 'Four' })}</option>
					<option value="microwave"
						>{$_('recipe.prep_microwave', { default: 'Micro-ondes' })}</option
					>
					<option value="frying">{$_('recipe.prep_frying', { default: 'Friture' })}</option>
					<option value="refrigeration"
						>{$_('recipe.prep_chilling', { default: 'Réfrigération' })}</option
					>
				</select>
			</div>

			<!-- Servings -->
			<div class="form-control">
				<label class="label text-xs font-semibold" for="servings-input">
					{$_('recipe.servings_count', { default: 'Nombre de portions' })}
				</label>
				<input
					id="servings-input"
					type="number"
					min="1"
					max="100"
					step="1"
					class="input input-bordered input-sm w-full"
					bind:value={servings}
					oninput={updateParams}
				/>
			</div>
		</div>
	</div>
</div>
