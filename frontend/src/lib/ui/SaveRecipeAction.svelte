<!--
  SaveRecipeAction.svelte

  Save control for the score page: the "Save recipe" button, the save dialog
  and the post-save toast.

  The dialog lets the user adjust the title before saving. "Save" updates the
  opened saved recipe (or creates a new one for a draft); "Save as new" is
  offered only when an opened recipe's title has been changed. A duplicate-title
  warning is shown without blocking the save.

  The dialog and toast are fixed-position elements, so the component's only
  in-flow node is the button: it can be placed directly in the page's action row.
-->
<script lang="ts">
	import { _ } from '$lib/i18n';
	import SaveRecipeDialog from '$lib/ui/SaveRecipeDialog.svelte';
	import { savedRecipes } from '$lib/stores/savedRecipes.svelte';
	import { normalizeRecipeTitle } from '$lib/storage/savedRecipes';
	import type { IngredientsList } from '$lib/types/ingredientsList';
	import type { SavedRecipe } from '$lib/types/savedRecipe';

	/** Result of the fresh score computation performed before saving. */
	type SaveScoreResult = {
		score: { letterGrade?: string | null; numericScore?: number | null } | null;
		failed: boolean;
		aborted: boolean;
	};

	type Props = {
		/** Current editor title; prefills the dialog. */
		title: string;
		/** Current editor description. */
		description: string;
		/** Current editor ingredients. */
		ingredients: IngredientsList;
		/** Selected country code, or null. */
		country: string | null;
		/** Id of the opened saved recipe, or null for a new draft. */
		savedRecipeId?: string | null;
		/** Title of the opened saved recipe, or null for a new draft. */
		savedRecipeTitle?: string | null;
		/**
		 * Compute and apply a fresh score for the current content.
		 * Implemented by the page, which owns the score display state.
		 */
		computeFreshScore: (signal: AbortSignal) => Promise<SaveScoreResult>;
		/** Called after a successful save so the page can sync its state and URL. */
		onsaved: (recipe: SavedRecipe) => void;
		/** Extra classes for the button. */
		class?: string;
	};

	let {
		title,
		description,
		ingredients,
		country,
		savedRecipeId = null,
		savedRecipeTitle = null,
		computeFreshScore,
		onsaved,
		class: className = ''
	}: Props = $props();

	// --- Save dialog state -------------------------------------------------
	let saveDialogOpen = $state(false);
	let saveDialogTitle = $state('');
	let isSaving = $state(false);
	let savingAction = $state<'save' | 'saveAsNew' | null>(null);
	let saveError = $state<string | null>(null);
	let saveController: AbortController | null = null;

	// --- Toast state -------------------------------------------------------
	let saveToast = $state<{ message: string; type: 'success' | 'warning' } | null>(null);
	let toastTimer: ReturnType<typeof setTimeout> | null = null;

	/**
	 * Whether the dialog title differs from the opened recipe's saved title.
	 * False for new recipes: "Save as new" only makes sense for saved ones.
	 */
	let saveDialogTitleModified = $derived(
		savedRecipeTitle !== null &&
			normalizeRecipeTitle(saveDialogTitle) !== normalizeRecipeTitle(savedRecipeTitle)
	);

	/** Offer "Save as new" only when an opened recipe's title has changed. */
	let showSaveAsNew = $derived(savedRecipeId !== null && saveDialogTitleModified);

	/**
	 * Whether another saved recipe already uses the title draft.
	 *
	 * New recipes always warn (saving creates a new entry). For an opened recipe
	 * the warning follows the Save as new action: it only applies when the title
	 * changed, since keeping the saved title is just an update.
	 */
	let saveTitleHasDuplicate = $derived.by(() => {
		if (saveDialogTitle.trim() === '') return false;
		if (savedRecipeId === null) return savedRecipes.hasTitle(saveDialogTitle);
		if (!saveDialogTitleModified) return false;
		return savedRecipes.hasTitle(saveDialogTitle, savedRecipeId);
	});

	/** Show a transient message after saving. */
	function showToast(message: string, type: 'success' | 'warning' = 'success') {
		saveToast = { message, type };
		if (toastTimer) clearTimeout(toastTimer);
		toastTimer = setTimeout(() => {
			saveToast = null;
			toastTimer = null;
		}, 4000);
	}

	/** Open the dialog with the current editor title. */
	function openSaveDialog() {
		saveDialogTitle = title;
		saveError = null;
		saveDialogOpen = true;
	}

	/** Close the dialog and abort an in-flight score computation. */
	function cancelSave() {
		saveController?.abort();
		saveController = null;
		isSaving = false;
		savingAction = null;
		saveDialogOpen = false;
		saveError = null;
	}

	/**
	 * Persist the recipe after obtaining a fresh score.
	 *
	 * @param createNew - When true, create a new recipe instead of updating the
	 *   recipe currently open.
	 */
	async function handleSave(createNew: boolean) {
		const trimmedTitle = saveDialogTitle.trim();
		if (!trimmedTitle || isSaving) return;

		isSaving = true;
		savingAction = createNew ? 'saveAsNew' : 'save';
		saveError = null;

		const controller = new AbortController();
		saveController = controller;
		const scoreResult = await computeFreshScore(controller.signal);

		if (scoreResult.aborted) {
			isSaving = false;
			savingAction = null;
			if (saveController === controller) saveController = null;
			return;
		}

		try {
			const recipe = savedRecipes.save(
				{
					id: savedRecipeId ?? undefined,
					title: trimmedTitle,
					description,
					ingredients,
					country,
					score: scoreResult.score?.letterGrade
						? {
								letterGrade: scoreResult.score.letterGrade,
								numericScore: scoreResult.score.numericScore ?? null
							}
						: null
				},
				{ createNew }
			);

			saveDialogOpen = false;
			saveError = null;
			onsaved(recipe);
			showToast(
				scoreResult.failed
					? $_('save_recipe.saved_without_score', {
							default: 'Recipe saved, but the score could not be computed.'
						})
					: createNew
						? $_('save_recipe.saved_as_new', { default: 'Saved as a new recipe.' })
						: $_('save_recipe.saved', { default: 'Recipe saved.' }),
				scoreResult.failed ? 'warning' : 'success'
			);
		} catch (e) {
			saveError =
				e instanceof Error
					? e.message
					: $_('save_recipe.save_error', {
							default: 'Could not save the recipe on this device.'
						});
		} finally {
			isSaving = false;
			savingAction = null;
			if (saveController === controller) saveController = null;
		}
	}

	// Clean up the toast timer and any in-flight save when leaving the page.
	$effect(() => {
		return () => {
			if (toastTimer) clearTimeout(toastTimer);
			saveController?.abort();
		};
	});
</script>

<button type="button" class="btn btn-secondary {className}" onclick={openSaveDialog}>
	{$_('recipe.save_recipe', { default: 'Save recipe' })}
</button>

{#if saveDialogOpen}
	<SaveRecipeDialog
		bind:title={saveDialogTitle}
		{showSaveAsNew}
		hasDuplicateTitle={saveTitleHasDuplicate}
		{isSaving}
		{savingAction}
		error={saveError}
		onsave={() => handleSave(false)}
		onsaveasnew={() => handleSave(true)}
		oncancel={cancelSave}
	/>
{/if}

{#if saveToast}
	<div class="toast toast-end toast-bottom z-50" role="status" aria-live="polite">
		<div class="alert {saveToast.type === 'success' ? 'alert-success' : 'alert-warning'} shadow-lg">
			<span>{saveToast.message}</span>
		</div>
	</div>
{/if}
