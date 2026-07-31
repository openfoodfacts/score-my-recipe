<!--
  RecipeRowEditor.svelte

  Handles the edition of the ingredient rows: it renders one `IngredientLine` per
  ingredient and takes care of deleting a row or adding a new empty line when the
  last one becomes non-empty.

  The ingredients array is bindable so that the shared state stays in the parent
  page (which also uses it to compute the score).

  Props:
  - ingredients: The full list of ingredients (bindable, owned by the parent page).
-->
<script lang="ts">
	import IngredientLine from './IngredientLine.svelte';
	import { removeIngredientFromList, addEmptyIngredientIfNeeded } from '$lib/types/ingredientsList';
	import type { IngredientsList } from '$lib/types/ingredientsList';

	type Props = {
		ingredients: IngredientsList;
		/** Ingredient ids flagged as missing in the last computed green-score. */
		missingIngredientIds?: string[];
	};

	let { ingredients = $bindable(), missingIngredientIds = [] }: Props = $props();

	/** Handle delete of an ingredient by id. */
	function handleIngredientDelete(id: string) {
		ingredients = removeIngredientFromList(ingredients, id);
	}

	/** Ensure a new empty line exists when the last line is no longer empty. */
	function addIngredientLine() {
		ingredients = addEmptyIngredientIfNeeded(ingredients);
	}
</script>

<div class="space-y-4">
	{#each ingredients as ingredient, index (ingredient.id)}
		<IngredientLine
			bind:ingredient={ingredients[index]}
			isLastItem={index === ingredients.length - 1}
			isFirstItem={index === 0}
			onDelete={handleIngredientDelete}
			onNotEmpty={addIngredientLine}
			{missingIngredientIds}
		/>
	{/each}
</div>
