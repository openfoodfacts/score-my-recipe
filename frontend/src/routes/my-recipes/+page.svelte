<!--
  My Recipes page

  Lists the recipes saved in the browser's localStorage. Each card shows the
  last saved score and metadata, opens the recipe in the score view, or can be
  deleted after confirmation. The list is sorted either by last update (the
  default) or alphabetically by title.
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { locale } from 'svelte-i18n';
	import { resolve } from '$app/paths';
	import { _, getLocale } from '$lib/i18n';
	import IconMdiDelete from '@iconify-svelte/mdi/delete';
	import GreenScore from '$lib/ui/GreenScore.svelte';
	import { savedRecipes } from '$lib/stores/savedRecipes.svelte';
	import type { SavedRecipe } from '$lib/types/savedRecipe';
	import { countNonEmptyIngredients } from '$lib/types/ingredientsList';

	type SortMode = 'updated' | 'title';

	/** Recipes are loaded from localStorage after hydration. */
	let isLoading = $state(true);
	let sortMode = $state<SortMode>('updated');

	/** Recipe pending deletion, or null when the confirmation dialog is closed. */
	let recipeToDelete = $state<SavedRecipe | null>(null);
	let deleteError = $state<string | null>(null);
	let deleteDialogEl = $state<HTMLDialogElement | null>(null);

	onMount(() => {
		savedRecipes.init();
		isLoading = false;
	});

	/** Recipes in the selected order; title sorting is locale-aware. */
	let sortedRecipes = $derived.by(() => {
		const currentLocale = $locale ?? getLocale();
		const list = [...savedRecipes.recipes];
		if (sortMode === 'title') {
			list.sort((a, b) => a.title.localeCompare(b.title, currentLocale, { sensitivity: 'base' }));
		} else {
			list.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
		}
		return list;
	});

	/** Format an ISO timestamp for the card's metadata line. */
	function formatDate(iso: string): string {
		const date = new Date(iso);
		if (Number.isNaN(date.getTime())) return '';
		return new Intl.DateTimeFormat($locale ?? getLocale(), { dateStyle: 'medium' }).format(date);
	}

	/** Link to the score view for a saved recipe. */
	function recipeHref(recipe: SavedRecipe): string {
		return `${resolve('/score')}?recipe=${encodeURIComponent(recipe.id)}`;
	}

	/** Number of non-empty ingredient lines in a saved recipe. */
	function ingredientCount(recipe: SavedRecipe): number {
		return countNonEmptyIngredients(recipe.ingredients);
	}

	/** Open the delete confirmation dialog for a recipe. */
	function openDeleteDialog(recipe: SavedRecipe) {
		recipeToDelete = recipe;
		deleteError = null;
	}

	/** Close the delete confirmation dialog. */
	function closeDeleteDialog() {
		recipeToDelete = null;
		deleteError = null;
	}

	/** Delete the pending recipe, keeping the dialog open if the write fails. */
	function confirmDelete() {
		if (!recipeToDelete) return;
		try {
			savedRecipes.delete(recipeToDelete.id);
			closeDeleteDialog();
		} catch (e) {
			deleteError =
				e instanceof Error
					? e.message
					: $_('my_recipes.delete_error', {
							default: 'Could not delete the recipe on this device.'
						});
		}
	}

	/** Close the dialog when the backdrop (the dialog element itself) is clicked. */
	function handleDeleteBackdropClick(event: MouseEvent) {
		if (event.target === deleteDialogEl) closeDeleteDialog();
	}

	// Show the native modal once the delete dialog has been mounted.
	$effect(() => {
		if (deleteDialogEl && !deleteDialogEl.open) {
			deleteDialogEl.showModal();
		}
	});
</script>

<svelte:head>
	<title>{$_('my_recipes.title', { default: 'My recipes' })}</title>
</svelte:head>

<div class="mx-auto max-w-7xl px-4 py-8">
	<!-- Header -->
	<div class="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
		<div>
			<h1 class="text-3xl font-bold">{$_('my_recipes.title', { default: 'My recipes' })}</h1>
			<p class="text-base-content/70 mt-2">
				{$_('my_recipes.description', {
					default: 'Your saved recipes are stored in this browser.'
				})}
			</p>
		</div>
		<a href={resolve('/add')} class="btn btn-primary">
			{$_('my_recipes.new_recipe', { default: 'Score a new recipe' })}
		</a>
	</div>

	{#if isLoading}
		<div class="flex justify-center py-20">
			<span class="loading loading-spinner loading-lg"></span>
		</div>
	{:else if sortedRecipes.length === 0}
		<!-- Empty state -->
		<div class="bg-base-200 rounded-lg p-10 text-center">
			<h2 class="text-xl font-semibold">
				{$_('my_recipes.empty_title', { default: 'No saved recipes yet' })}
			</h2>
			<p class="text-base-content/70 mt-2">
				{$_('my_recipes.empty_description', {
					default: 'Save a recipe from the score view and it will appear here.'
				})}
			</p>
			<a href={resolve('/add')} class="btn btn-primary mt-6">
				{$_('my_recipes.new_recipe', { default: 'Score a new recipe' })}
			</a>
		</div>
	{:else}
		<!-- Sort control -->
		<div class="mb-4 flex items-center justify-end gap-2">
			<label class="text-sm" for="recipe-sort">
				{$_('my_recipes.sort_label', { default: 'Sort by' })}
			</label>
			<select id="recipe-sort" class="select select-bordered select-sm w-44" bind:value={sortMode}>
				<option value="updated">{$_('my_recipes.sort_updated', { default: 'Last updated' })}</option
				>
				<option value="title">{$_('my_recipes.sort_title', { default: 'Title' })}</option>
			</select>
		</div>

		<!-- Recipe cards -->
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each sortedRecipes as recipe (recipe.id)}
				<div
					class="card bg-base-100 border-base-300 relative border shadow-sm transition-shadow hover:shadow-md"
				>
					<a href={recipeHref(recipe)} class="block h-full p-5 pr-12">
						<h2 class="line-clamp-2 text-lg font-semibold">{recipe.title}</h2>

						{#if recipe.description.trim()}
							<p class="text-base-content/70 mt-2 line-clamp-2 text-sm">{recipe.description}</p>
						{/if}

						<div class="mt-4 flex items-end justify-between gap-3">
							<div class="min-w-0">
								{#if recipe.score?.letterGrade}
									<GreenScore
										letterGrade={recipe.score.letterGrade}
										showNumeric={false}
										size="sm"
									/>
								{:else}
									<span class="badge badge-ghost badge-sm">
										{$_('my_recipes.not_scored', { default: 'Not scored' })}
									</span>
								{/if}
							</div>

							<div class="text-base-content/60 shrink-0 text-right text-xs">
								<p>
									{ingredientCount(recipe)}
									{$_('my_recipes.ingredients', { default: 'ingredient(s)' })}
								</p>
								<p>
									{$_('my_recipes.updated', { default: 'Updated' })}
									{formatDate(recipe.updatedAt)}
								</p>
							</div>
						</div>
					</a>

					<button
						type="button"
						class="btn btn-circle btn-ghost btn-sm absolute top-2 right-2"
						aria-label={`${$_('my_recipes.delete_recipe', {
							default: 'Delete recipe'
						})}: ${recipe.title}`}
						onclick={() => openDeleteDialog(recipe)}
					>
						<IconMdiDelete class="h-5 w-5" />
					</button>
				</div>
			{/each}
		</div>
	{/if}
</div>

{#if recipeToDelete}
	<dialog
		bind:this={deleteDialogEl}
		class="modal"
		aria-labelledby="delete-recipe-dialog-title"
		onclose={closeDeleteDialog}
		onclick={handleDeleteBackdropClick}
	>
		<div class="modal-box">
			<h2 id="delete-recipe-dialog-title" class="text-lg font-bold">
				{$_('my_recipes.delete_title', { default: 'Delete this recipe?' })}
			</h2>
			<p class="text-base-content/70 mt-1 text-sm">
				{$_('my_recipes.delete_message', {
					default: 'This recipe will be removed from this browser. This cannot be undone.'
				})}
			</p>
			<p class="mt-3 font-semibold">{recipeToDelete.title}</p>

			{#if deleteError}
				<div class="alert alert-error mt-3" role="alert">
					<span>{deleteError}</span>
				</div>
			{/if}

			<div class="modal-action">
				<button type="button" class="btn btn-ghost" onclick={closeDeleteDialog}>
					{$_('my_recipes.delete_cancel', { default: 'Cancel' })}
				</button>
				<button type="button" class="btn btn-error" onclick={confirmDelete}>
					{$_('my_recipes.delete_confirm', { default: 'Delete' })}
				</button>
			</div>
		</div>
	</dialog>
{/if}
