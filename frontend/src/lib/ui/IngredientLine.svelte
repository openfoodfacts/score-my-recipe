<!--
  IngredientLine.svelte
  
  A single row component representing one ingredient in the recipe editor.
  Contains fields for: name, weight, codified ingredient, labels, seasonality, origin, and delete action.
  
  Props:
  - ingredient: The ingredient data object (bindable - changes propagate to parent)
  - isLastItem: Whether this is the last item in the list (controls new line creation)
  - onDelete: Callback when delete button is clicked
-->
<script lang="ts">
	import { _ } from '$lib/i18n';
	import Tags from './Tags.svelte';
	import IconMdiDelete from '@iconify-svelte/mdi/delete';
	import type { Ingredient } from '$lib/types/ingredient';
	import { isIngredientEmpty, isIngredientNotEmpty } from '$lib/types/ingredient';

	type Props = {
		// The ingredient data object (bindable): name, weight, etc.
		ingredient: Ingredient;
		isLastItem?: boolean;
		onDelete?: (id: string) => void;
		onNotEmpty?: () => void; // Optional callback for when line becomes non-empty
	};

	let {
		ingredient = $bindable(),
		isLastItem = false,
		onDelete,
		onNotEmpty,
	}: Props = $props();

	// Track if this ingredient was empty when the component was created
	// This is used to detect when user starts typing in an empty last line
	let wasEmptyOnMount = $state(ingredient.name === '');
	let isNotEmpty = $derived(wasEmptyOnMount && isIngredientNotEmpty(ingredient));

	// trigger onNotEmpty when isNoteEmpty becomes true
	$effect(() => {
		if (isNotEmpty && onNotEmpty) {
			onNotEmpty();
		}
	});

	/**
	 * Handle delete button click
	 */
	function handleDelete() {
		onDelete?.(ingredient.id);
	}
</script>

<div class="bg-base-200 flex flex-col gap-2 rounded-lg p-3 sm:flex-row sm:items-start">

	<!-- Codified Ingredient name -->
	<div class="w-40">
		<label class="label py-1" for="ingredient-codified-{ingredient.id}">
			<span class="label-text text-xs"
				>{$_('recipe.codified_ingredient', { default: 'Codified' })}</span
			>
		</label>
		<Tags
			tagtype="ingredients"
			required={true}
			allowUserOptions={false}
			id="ingredient-codified-{ingredient.id}"
			bind:tag={ingredient.codifiedIngredient}
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
			min="0"
		/>
	</div>

	<!-- Labels -->
	<div class="w-48">
		<label class="label py-1" for="ingredient-labels-{ingredient.id}">
			<span class="label-text text-xs" id="ingredient-labels-label-{ingredient.id}"
				>{$_('recipe.labels', { default: 'Labels' })}</span
			>
		</label>
		<Tags
			id="ingredient-labels-{ingredient.id}"
			tagtype="labels"
			bind:tags={ingredient.labels}
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
			id="ingredient-origin-{ingredient.id}"
			tagtype="countries"
			bind:tags={ingredient.origin}
		/>
	</div>

	<!-- Delete Button -->
	<div class="flex w-12 items-end justify-center pb-1">
		{#if !(isLastItem && isIngredientEmpty(ingredient))}
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
