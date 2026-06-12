<!--
  IngredientLine.svelte
  
  A single row component representing one ingredient in the recipe editor.
  Contains fields for: name, weight, codified ingredient, labels, seasonality, origin, and delete action.
  
  Props:
  - ingredient: The ingredient data object (bindable - changes propagate to parent)
  - ingredientsTaxonomy: List of codified ingredient options
  - labelsTaxonomy: List of available labels for autocomplete
  - countriesTaxonomy: List of countries for origin autocomplete
  - isLastItem: Whether this is the last item in the list (controls new line creation)
  - onDelete: Callback when delete button is clicked
  - onNameFocus: Callback when user starts typing in an empty last line (for triggering new line)
-->
<script lang="ts">
	import { _ } from '$lib/i18n';
	import Tags from './Tags.svelte';
	import IconMdiDelete from '@iconify-svelte/mdi/delete';

	type Ingredient = {
		id: string;
		name: string;
		weight: number | null;
		codifiedIngredient: string;
		labels: string[];
		seasonality: boolean;
		origin: string[];
	};

	type Props = {
		ingredient: Ingredient;
		ingredientsTaxonomy: readonly string[];
		labelsTaxonomy: readonly string[];
		countriesTaxonomy: readonly string[];
		isLastItem?: boolean;
		onDelete?: (id: string) => void;
		onNameFocus?: () => void;
	};

	let {
		ingredient = $bindable(),
		ingredientsTaxonomy,
		labelsTaxonomy,
		countriesTaxonomy,
		isLastItem = false,
		onDelete,
		onNameFocus
	}: Props = $props();

	// Track if this ingredient was empty when the component was created
	// This is used to detect when user starts typing in an empty last line
	let wasEmptyOnMount = $state(ingredient.name === '');

	// Use effect to watch for changes and trigger new line when needed
	$effect(() => {
		// Only trigger if this is the last item, was empty on mount, and now has content
		if (isLastItem && wasEmptyOnMount && ingredient.name.trim() !== '') {
			// Mark that we've already triggered (to avoid multiple calls)
			wasEmptyOnMount = false;
			onNameFocus?.();
		}
	});

	/**
	 * Handle changes to ingredient fields
	 * With bind:ingredient, changes are automatically propagated to parent
	 */
	function handleChange() {
		// No-op: changes are automatically propagated via bind:ingredient
	}

	/**
	 * Handle delete button click
	 */
	function handleDelete() {
		onDelete?.(ingredient.id);
	}
</script>

<div class="bg-base-200 flex flex-col gap-2 rounded-lg p-3 sm:flex-row sm:items-start">
	<!-- Ingredient Name -->
	<div class="flex-1">
		<label class="label py-1" for="ingredient-name-{ingredient.id}">
			<span class="label-text text-xs"
				>{$_('recipe.ingredient_name', { default: 'Ingredient Name' })}</span
			>
		</label>
		<input
			id="ingredient-name-{ingredient.id}"
			type="text"
			class="input input-bordered w-full"
			placeholder={$_('recipe.ingredient_name_placeholder', { default: 'e.g., Tomato' })}
			bind:value={ingredient.name}
			oninput={handleChange}
		/>
	</div>

	<!-- Weight -->
	<div class="w-24">
		<label class="label py-1" for="ingredient-weight-{ingredient.id}">
			<span class="label-text text-xs">{$_('recipe.weight', { default: 'Weight (g)' })}</span>
		</label>
		<input
			id="ingredient-weight-{ingredient.id}"
			type="number"
			class="input input-bordered w-full"
			placeholder="0"
			bind:value={ingredient.weight}
			oninput={handleChange}
			min="0"
		/>
	</div>

	<!-- Codified Ingredient -->
	<div class="w-40">
		<label class="label py-1" for="ingredient-codified-{ingredient.id}">
			<span class="label-text text-xs"
				>{$_('recipe.codified_ingredient', { default: 'Codified' })}</span
			>
		</label>
		<select
			id="ingredient-codified-{ingredient.id}"
			class="select select-bordered w-full"
			bind:value={ingredient.codifiedIngredient}
			onchange={handleChange}
		>
			{#each ingredientsTaxonomy as taxonomyItem (taxonomyItem)}
				<option value={taxonomyItem}>
					{taxonomyItem === 'unknown' ? $_('recipe.unknown', { default: 'Unknown' }) : taxonomyItem}
				</option>
			{/each}
		</select>
	</div>

	<!-- Labels -->
	<div class="w-48">
		<label class="label py-1" for="ingredient-labels-{ingredient.id}">
			<span class="label-text text-xs" id="ingredient-labels-label-{ingredient.id}"
				>{$_('recipe.labels', { default: 'Labels' })}</span
			>
		</label>
		<Tags
			autocomplete={labelsTaxonomy}
			tags={ingredient.labels}
			onChange={(labels) => {
				ingredient.labels = labels;
				handleChange();
			}}
		/>
	</div>

	<!-- Seasonality -->
	<div class="flex w-20 flex-col">
		<label class="label py-1" for="ingredient-seasonality-{ingredient.id}">
			<span class="label-text text-xs" id="ingredient-seasonality-label-{ingredient.id}"
				>{$_('recipe.seasonality', { default: 'Seasonal' })}</span
			>
		</label>
		<div class="flex h-10 items-center">
			<input
				id="ingredient-seasonality-{ingredient.id}"
				type="checkbox"
				class="checkbox checkbox-primary"
				bind:checked={ingredient.seasonality}
				onchange={handleChange}
				aria-labelledby="ingredient-seasonality-label-{ingredient.id}"
			/>
		</div>
	</div>

	<!-- Origin -->
	<div class="w-48">
		<label class="label py-1" for="ingredient-origin-{ingredient.id}">
			<span class="label-text text-xs" id="ingredient-origin-label-{ingredient.id}"
				>{$_('recipe.origin', { default: 'Origin' })}</span
			>
		</label>
		<Tags
			autocomplete={countriesTaxonomy}
			tags={ingredient.origin}
			onChange={(origin) => {
				ingredient.origin = origin;
				handleChange();
			}}
		/>
	</div>

	<!-- Delete Button -->
	<div class="flex w-12 items-end justify-center pb-1">
		{#if !(isLastItem && ingredient.name === '')}
			<button
				class="btn btn-circle btn-ghost btn-sm text-error"
				onclick={handleDelete}
				aria-label={$_('recipe.delete_ingredient', { default: 'Delete ingredient' })}
			>
				<IconMdiDelete class="h-5 w-5" />
			</button>
		{/if}
	</div>
</div>
