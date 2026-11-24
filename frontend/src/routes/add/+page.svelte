<script lang="ts">
	import { _, getLocale } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import { parseRecipeText, apiIngredientsToIngredients } from '$lib/api/recipe';
	import OnboardingBanner from '$lib/ui/OnboardingBanner.svelte';
	import HelperTooltip from '$lib/ui/HelperTooltip.svelte';
	import RecipeExamples from '$lib/ui/RecipeExamples.svelte';
	import RecipeDetailsFields from '$lib/ui/RecipeDetailsFields.svelte';
	import type { RecipeDraft } from '$lib/types/recipe';
	import SpreadsheetImport from '$lib/ui/SpreadsheetImport.svelte';

	let title = $state('');
	let description = $state('');

	let activeTab = $state<'text' | 'spreadsheet'>('text');
	let recipeText = $state('');
	let isLoading = $state(false);
	let error = $state<string | null>(null);

	let onboardingRef = $state<ReturnType<typeof OnboardingBanner> | null>(null);
	let isOnboardingDismissed = $state(true);

	async function handleSubmit(event: Event) {
		event.preventDefault();
		isLoading = true;
		error = null;

		try {
			// the recipe text is most likely written in the language of the
			// interface, the API expects a 2-letter language code (eg. "fr")
			const lang = getLocale().split('-')[0];
			const result = await parseRecipeText(recipeText, lang);
			const ingredients = apiIngredientsToIngredients(result.ingredients);
			const state: RecipeDraft = { title, description, ingredients };
			await goto('/score', { state });
		} catch (e) {
			error = e instanceof Error ? e.message : 'Une erreur est survenue';
			isLoading = false;
		}
	}
</script>

<svelte:head>
	<title>{$_('add.title', { default: 'Ajouter une recette' })}</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-8">
	<!-- Onboarding Callout -->
	<OnboardingBanner bind:this={onboardingRef} bind:isDismissed={isOnboardingDismissed} />

	<!-- Header -->
	<div class="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
		<div>
			<h1 class="text-3xl font-bold">{$_('add.title', { default: 'Ajouter une recette' })}</h1>
			<p class="text-base-content/70 mt-2">
				{$_('add.description', { default: 'Entrez votre recette ci-dessous' })}
				{$_('add.or', { default: 'ou utilisez la' })}
				<a href="/score" class="link link-primary"
					>{$_('add.guided_entry', { default: 'saisie guidée' })}</a
				>.
			</p>
		</div>

		{#if isOnboardingDismissed}
			<button
				type="button"
				class="btn btn-ghost btn-sm text-primary gap-1.5 self-start sm:self-auto"
				onclick={() => onboardingRef?.show()}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="h-4 w-4"
				>
					<path
						fill-rule="evenodd"
						d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z"
						clip-rule="evenodd"
					/>
				</svg>
				<span>{$_('onboarding.help_button', { default: 'How does it work?' })}</span>
			</button>
		{/if}
	</div>

	<!-- Input mode tabs -->
	<div
		role="tablist"
		class="tabs tabs-box mb-6 w-fit"
		aria-label={$_('add.tabs.label', { default: 'Recipe input mode' })}
	>
		<button
			type="button"
			role="tab"
			id="tab-text"
			aria-controls="panel-text"
			aria-selected={activeTab === 'text'}
			class="tab"
			class:tab-active={activeTab === 'text'}
			onclick={() => (activeTab = 'text')}
		>
			{$_('add.tabs.text', { default: 'Text' })}
		</button>
		<button
			type="button"
			role="tab"
			id="tab-spreadsheet"
			aria-controls="panel-spreadsheet"
			aria-selected={activeTab === 'spreadsheet'}
			class="tab"
			class:tab-active={activeTab === 'spreadsheet'}
			onclick={() => (activeTab = 'spreadsheet')}
		>
			{$_('add.tabs.spreadsheet', { default: 'Spreadsheet' })}
		</button>
	</div>

	<div id="panel-text" role="tabpanel" aria-labelledby="tab-text" hidden={activeTab !== 'text'}>
		<!-- Recipe Form -->
		<form onsubmit={handleSubmit} class="space-y-6">
			<!-- Optional recipe metadata, carried to the edit view -->
			<RecipeDetailsFields bind:title bind:description />

			<div class="form-control w-full space-y-2">
				<!-- Field label -->
				<div class="flex items-center justify-between">
					<label class="label justify-start p-0" for="recipe-text">
						<span class="flex items-center gap-2 text-sm font-medium sm:text-base">
							<span>{$_('add.recipe_label', { default: 'Votre recette' })}</span>
							<HelperTooltip
								tip={$_('helpers.recipe_text', {
									default:
										'Enter each ingredient on a new line with its quantity (e.g. 200g flour, 3 eggs, 100g sugar).'
								})}
								ariaLabel={$_('helpers.more_info', { default: 'More information' })}
							/>
						</span>
					</label>
				</div>

				<!-- Example recipe shortcuts (honors UI language) -->
				<RecipeExamples onselect={(text) => (recipeText = text)} />

				<textarea
					id="recipe-text"
					bind:value={recipeText}
					class="textarea textarea-bordered min-h-64 w-full text-base"
					placeholder={$_('add.recipe_placeholder', {
						default:
							'Entrez votre recette ici...\n\nExemple:\n200g de farine\n3 œufs\n100g de sucre'
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
>>>>>>> main

		<!-- Error Display -->
		{#if error}
			<div class="alert alert-error mt-6" role="alert">
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
	</div>

	<div
		id="panel-spreadsheet"
		role="tabpanel"
		aria-labelledby="tab-spreadsheet"
		hidden={activeTab !== 'spreadsheet'}
	>
		<SpreadsheetImport />
	</div>
</div>
