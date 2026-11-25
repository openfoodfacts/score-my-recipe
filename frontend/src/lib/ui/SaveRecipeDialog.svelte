<!--
  SaveRecipeDialog.svelte

  Modal shown whenever the user clicks "Save recipe" on the score view.

  It lets the user adjust the title before saving, warns (without blocking) when
  the drafted title is already used by another saved recipe, and offers
  "Save as new" only when the title of an opened saved recipe has been changed.
  The title is bound to the parent's draft state so cancelling leaves the editor
  untouched.
-->
<script lang="ts">
	import { _ } from '$lib/i18n';

	type SavingAction = 'save' | 'saveAsNew' | null;

	type Props = {
		/** Title draft, bound so the parent can commit it on save. */
		title?: string;
		/** Whether to offer "Save as new" (opened recipe with an edited title). */
		showSaveAsNew?: boolean;
		/** Whether another saved recipe already uses the drafted title. */
		hasDuplicateTitle?: boolean;
		/** Whether a save is currently in progress. */
		isSaving?: boolean;
		/** Which action is in progress, used to show the spinner on the right button. */
		savingAction?: SavingAction;
		/** Save error to display inside the dialog. */
		error?: string | null;
		/** Update the opened recipe using the drafted title. */
		onsave: () => void;
		/** Create a new recipe using the drafted title. */
		onsaveasnew: () => void;
		/** Close the dialog without saving. */
		oncancel: () => void;
	};

	let {
		title = $bindable(''),
		showSaveAsNew = false,
		hasDuplicateTitle = false,
		isSaving = false,
		savingAction = null,
		error = null,
		onsave,
		onsaveasnew,
		oncancel
	}: Props = $props();

	let dialogEl = $state<HTMLDialogElement | null>(null);
	let titleInput = $state<HTMLInputElement | null>(null);

	/** A save requires a title once surrounding whitespace is removed. */
	let canSubmit = $derived(title.trim() !== '');

	// Show the native modal once the dialog element is mounted. Native dialogs
	// provide the focus trap and Escape handling for free.
	$effect(() => {
		if (dialogEl && !dialogEl.open) {
			dialogEl.showModal();
			titleInput?.focus();
			titleInput?.select();
		}
	});

	/** Close the dialog when the backdrop (the dialog element itself) is clicked. */
	function handleBackdropClick(event: MouseEvent) {
		if (event.target === dialogEl) oncancel();
	}
</script>

<dialog
	bind:this={dialogEl}
	class="modal"
	aria-labelledby="save-recipe-dialog-title"
	onclose={oncancel}
	onclick={handleBackdropClick}
>
	<div class="modal-box">
		<h2 id="save-recipe-dialog-title" class="text-lg font-bold">
			{$_('save_recipe.title', { default: 'Save recipe' })}
		</h2>
		<p class="text-base-content/70 mt-1 text-sm">
			{$_('save_recipe.description', { default: 'Choose a title for this recipe.' })}
		</p>

		<div class="form-control mt-4">
			<label class="label" for="save-recipe-title">
				<span class="label-text">{$_('recipe.title_label', { default: 'Recipe title' })}</span>
			</label>
			<input
				id="save-recipe-title"
				type="text"
				class="input input-bordered w-full"
				maxlength={120}
				bind:this={titleInput}
				bind:value={title}
				placeholder={$_('recipe.title_placeholder', { default: 'e.g. Quiche Lorraine' })}
			/>
		</div>

		{#if hasDuplicateTitle}
			<div class="alert alert-warning mt-3" role="status" aria-live="polite">
				<span>
					{$_('save_recipe.duplicate_title', {
						default: 'A saved recipe already uses this title.'
					})}
				</span>
			</div>
		{/if}

		{#if error}
			<div class="alert alert-error mt-3" role="alert">
				<span>{error}</span>
			</div>
		{/if}

		<div
			class="modal-action flex flex-col-reverse items-stretch gap-2 sm:flex-row sm:items-end sm:justify-end"
		>
			<button type="button" class="btn btn-ghost" onclick={oncancel}>
				{$_('save_recipe.cancel', { default: 'Cancel' })}
			</button>

			{#if showSaveAsNew}
				<div class="flex flex-col items-stretch gap-1 sm:items-end">
					<button
						type="button"
						class="btn btn-secondary"
						onclick={onsaveasnew}
						disabled={isSaving || !canSubmit}
					>
						{#if savingAction === 'saveAsNew'}
							<span class="loading loading-spinner loading-sm"></span>
						{/if}
						{$_('save_recipe.save_as_new', { default: 'Save as new' })}
					</button>
					<span class="text-base-content/60 text-xs">
						{$_('save_recipe.save_as_new_hint', {
							default: 'Creates another recipe with this title.'
						})}
					</span>
				</div>
			{/if}

			<button
				type="button"
				class="btn btn-primary"
				onclick={onsave}
				disabled={isSaving || !canSubmit}
			>
				{#if savingAction === 'save'}
					<span class="loading loading-spinner loading-sm"></span>
				{/if}
				{$_('save_recipe.save', { default: 'Save' })}
			</button>
		</div>
	</div>
</dialog>
