<script lang="ts">
	import { _ } from '$lib/i18n';
	import { parseRecipeText } from '$lib/api/recipe';
	import type { RecipeParseResponse } from '$lib/api/recipe';

	let recipeText = $state('');
	let isLoading = $state(false);
	let result = $state<RecipeParseResponse | null>(null);
	let error = $state<string | null>(null);

	async function handleSubmit(event: Event) {
		event.preventDefault();
		isLoading = true;
		error = null;
		result = null;

		try {
			result = await parseRecipeText(recipeText, 'fr');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Une erreur est survenue';
		} finally {
			isLoading = false;
		}
	}
</script>

<svelte:head>
	<title>{$_('add.title', { default: 'Ajouter une recette' })}</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-8">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold">{$_('add.title', { default: 'Ajouter une recette' })}</h1>
		<p class="text-base-content/70 mt-2">
			{$_('add.description', { default: 'Entrez votre recette ci-dessous' })}
		</p>
	</div>

	<!-- Recipe Form -->
	<form onsubmit={handleSubmit} class="space-y-6">
		<div class="form-control w-full">
			<label class="label justify-start" for="recipe-text">
				<span class="label-text font-medium"
					>{$_('add.recipe_label', { default: 'Votre recette' })}</span
				>
			</label>
			<textarea
				id="recipe-text"
				bind:value={recipeText}
				class="textarea textarea-bordered min-h-64 w-full text-base"
				placeholder={$_('add.recipe_placeholder', {
					default: 'Entrez votre recette ici...\n\nExemple:\n200g de farine\n3 œufs\n100g de sucre'
				})}
				required
			></textarea>
		</div>

		<button type="submit" class="btn btn-primary btn-lg" disabled={isLoading}>
			{#if isLoading}
				<span class="loading loading-spinner"></span>
				{$_('add.loading', { default: 'Calcul en cours...' })}
			{:else}
				{$_('add.score_button', { default: 'Score recipe' })}
			{/if}
		</button>
	</form>

	<!-- Error Display -->
	{#if error}
		<div class="alert alert-error mt-6">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-6 w-6 shrink-0 stroke-current"
				fill="none"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
				/>
			</svg>
			<span>{error}</span>
		</div>
	{/if}

	<!-- Result Display -->
	{#if result}
		<div class="mt-8">
			<h2 class="mb-4 text-xl font-bold">
				{$_('add.result_title', { default: 'Ingrédients détectés' })}
			</h2>
			<div class="overflow-x-auto">
				<table class="table-zebra table">
					<thead>
						<tr>
							<th>{$_('add.table_ingredient', { default: 'Ingrédient' })}</th>
							<th>{$_('add.table_taxonomy', { default: 'Dans la taxonomie' })}</th>
							<th>{$_('add.table_quantity', { default: 'Quantité (g)' })}</th>
						</tr>
					</thead>
					<tbody>
						{#each result.ingredients as ingredient, index (index)}
							<tr>
								<td>{ingredient.codified_ingredient}</td>
								<td>
									{#if ingredient.is_in_taxonomy}
										<span class="badge badge-success">{$_('add.yes', { default: 'Oui' })}</span>
									{:else}
										<span class="badge badge-warning">{$_('add.no', { default: 'Non' })}</span>
									{/if}
								</td>
								<td>{ingredient.quantity_g ?? '-'}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}
</div>
