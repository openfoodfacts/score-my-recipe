<!--
  Tags.svelte

  A Svelte component for managing a list of tags with autocomplete suggestions.
  It supports adding new tags, editing existing ones, and removing tags.
  The component uses Fuse.js for fuzzy searching through the autocomplete options and provides keyboard navigation for accessibility.

  Props:
    - tagtype: A string representing the type of tags (e.g., "labels", "origins")
	  for fetching relevant autocomplete suggestions.
	- tags: An array of strings representing the current tags.
	- autocomplete: An array of strings for autocomplete suggestions.
	- onChange: A callback function that is called whenever the tags change.

  Features:
	- Add new tags by typing and pressing Enter or comma.
	- Edit existing tags by double-clicking them.
	- Remove tags using a close button.
	- Autocomplete suggestions appear when typing, with keyboard navigation support (ArrowUp/Down).
-->
<script lang="ts">
	import { fade } from 'svelte/transition';
	import {debounce} from 'lodash.debounce';
	import { getMatchingTags } from '$lib/api/taxonomy';

	import IconMdiClose from '@iconify-svelte/mdi/close';

	type Props = {
		tagtype: string;
		tags?: string[];
		autocomplete?: readonly string[];
		onChange?: (tags: string[]) => void;
	};

	let { tagtype, tags = $bindable([]), autocomplete = [], onChange }: Props = $props();

	let autoCompleteIndex = $state(-1);
	// suggestions returned by API
	let currentSuggestions = $state<string[]>([]);

	// tracking input values for both adding new tags and editing existing ones
	let newValue = $state('');
	let editingIndex = $state(-1);
	let editingValue = $state('');

	// Track active search value (newValue for additions, editingValue for inline edits)
	let activeSearchValue = $derived(editingIndex === -1 ? newValue : editingValue);

	// Reactive bounds check: reset suggestion index to -1 if list shrinks under it
	$effect(() => {
		if (autoCompleteIndex >= currentSuggestions.length) {
			autoCompleteIndex = -1;
		}
	});

	// fetch suggestion as soon as inputValue changes
	$effect(() => {
		fetchSuggestions(activeSearchValue);
	});

	const fetchSuggestions = debounce(async (value: string) => {
		if (value.trim() === '') {
			currentSuggestions = [];
			return;
		}
		const resp = await getMatchingTags(tagtype, value);
		// see later how to show synonyms in the UI
		currentSuggestions = resp.suggestions;
	}, 200);

	/**
	 * Handle keyboard navigation (ArrowUp/Down) through autocomplete suggestions
	 * @param {KeyboardEvent} event
	 * @returns true if the event was handled, false otherwise
	 */
	function handleNavigationKeys(event: KeyboardEvent): boolean {
		if (currentSuggestions.length === 0) return false;

		if (event.key === 'ArrowDown') {
			event.preventDefault();
			if (autoCompleteIndex === -1) {
				autoCompleteIndex = 0;
			} else if (autoCompleteIndex < currentSuggestions.length - 1) {
				autoCompleteIndex += 1;
			}
			return true;
		} else if (event.key === 'ArrowUp') {
			event.preventDefault();
			if (autoCompleteIndex === -1) {
				autoCompleteIndex = currentSuggestions.length - 1;
			} else if (autoCompleteIndex > 0) {
				autoCompleteIndex -= 1;
			}
			return true;
		}
		return false;
	}

	/**
	 * Handle key events in the main input for adding tags. Enter or comma will add the tag, Backspace will remove the last tag if input is empty, and Arrow keys will navigate suggestions.
	 * @param event
	 */
	function inputHandler(event: KeyboardEvent) {
		if (event.key === 'Enter' || event.key === ',') {
			if (autoCompleteIndex !== -1 && currentSuggestions[autoCompleteIndex]) {
				newValue = currentSuggestions[autoCompleteIndex].item;
			}

			const tag = newValue.trim();

			newValue = '';
			autoCompleteIndex = -1;
			event.preventDefault();

			addTag(tag);
		} else if (newValue.length === 0 && event.key === 'Backspace') {
			tags = tags.slice(0, -1);
			onChange?.(tags);
		} else {
			handleNavigationKeys(event);
		}
	}

	/**
	 * Add a new tag if it doesn't already exist.
	 *
	 * Trims whitespace and ignores empty tags. Logs a warning if the tag already exists.
	 * @param tag
	 */
	function addTag(tag: string) {
		if (tags.includes(tag)) {
			console.warn(`Tag "${tag}" already exists.`);
			return;
		}
		tags = [...tags, tag];
		onChange?.(tags);
	}

	/**
	 * Remove a tag by filtering it out of the tags array.
	 * @param tag
	 */
	function removeTag(tag: string) {
		tags = tags.filter((t) => t !== tag);
		onChange?.(tags);
	}

	/**
	 * Start editing a tag by setting the editing index and value. Also resets the autocomplete index to prevent stale suggestions.
	 * @param index
	 * @param tag
	 */
	function startEditing(index: number, tag: string) {
		editingIndex = index;
		editingValue = tag;
		autoCompleteIndex = -1;
	}

	/**
	 * Save the edited tag by updating the tags array if the value has changed and is not empty. Resets editing state and autocomplete index afterward.
	 * @param index
	 */
	function saveEdit(index: number) {
		const trimmedValue = editingValue.trim();
		if (trimmedValue !== '' && trimmedValue !== tags[index]) {
			tags = tags.map((tag, i) => (i === index ? trimmedValue : tag));
			onChange?.(tags);
		}
		editingIndex = -1;
		editingValue = '';
		autoCompleteIndex = -1;
	}

	/**
	 * Cancel editing by resetting the editing index and value,
	 * as well as the autocomplete index to prevent stale suggestions.
	 */
	function cancelEdit() {
		editingIndex = -1;
		editingValue = '';
		autoCompleteIndex = -1;
	}

	/**
	 * Handle key events in the edit input:
	 * Enter will save the edit,
	 * Escape will cancel it,
	 * and Arrow keys will navigate suggestions.
	 * @param event
	 * @param index
	 */
	function handleEditKeydown(event: KeyboardEvent, index: number) {
		if (event.key === 'Enter') {
			if (autoCompleteIndex !== -1 && currentSuggestions[autoCompleteIndex]) {
				editingValue = currentSuggestions[autoCompleteIndex].item;
				autoCompleteIndex = -1;
				event.preventDefault();
				return;
			}
			event.preventDefault();
			saveEdit(index);
		} else if (event.key === 'Escape') {
			event.preventDefault();
			cancelEdit();
		} else {
			handleNavigationKeys(event);
		}
	}

	/**
	 * Handle selection of a suggestion from the autocomplete dropdown list.
	 * Selecting it from known values, or adding the value as a new value.
	 * @param key
	 */
	function selectSuggestion(key: string) {
		if (editingIndex !== -1) {
			editingValue = key;
			const idx = editingIndex;
			setTimeout(() => saveEdit(idx), 0);
		} else {
			newValue = '';
			autoCompleteIndex = -1;
			addTag(key);
		}
	}

	/**
	 * Focus and select the content of an input element.
	 * @param element
	 */
	function focus(element: HTMLInputElement) {
		element.focus();
		element.select();
	}
</script>

<!-- Autocomplete Dropdown 
 Handles displaying autocomplete suggestions and keyboard navigation for both adding new tags and editing existing ones.
-->
{#snippet autocompleteDropdown()}
	{#if currentSuggestions.length > 0}
		<div
			class="dropdown-content bg-base-100 z-100 mt-1 w-full rounded-md shadow-lg focus:outline-none"
		>
			<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
			<ul tabindex="0" class="divide-base-200 divide-y">
				{#each currentSuggestions as suggestion, index (suggestion.item)}
					{@const key = suggestion.item}
					<li>
						<button
							type="button"
							class="bg-base-200 text-base-content hover:bg-primary hover:text-primary-content focus:bg-primary focus:text-primary-content w-full rounded-md px-4 py-2 text-left transition-colors duration-150"
							class:bg-primary={autoCompleteIndex === index}
							class:text-primary-content={autoCompleteIndex === index}
							onmousedown={(e) => {
								// Use mousedown instead of click to fire selectSuggestion before the input's blur event
								e.preventDefault();
								selectSuggestion(key);
							}}
						>
							<span class="block truncate">{key}</span>
						</button>
					</li>
				{/each}
			</ul>
		</div>
	{/if}
{/snippet}

<!-- Tag widget -->
<div
	class="bg-base-100 border-base-200 focus-within:border-primary focus-within:outline-primary flex h-auto min-h-12 w-full flex-wrap items-center gap-x-1.5 gap-y-1 rounded-md p-2"
>
	<!-- each value of the tag (multi valued) -->
	{#each tags as tag, index (tag)}
		<div class="badge badge-ghost flex h-min items-center py-2" transition:fade={{ duration: 100 }}>
			{#if editingIndex === index}
				<!-- Existing tag editing input with autocomplete dropdown -->
				<div class="dropdown">
					<input
						type="text"
						class="input w-full min-w-0 border bg-transparent outline-none"
						bind:value={editingValue}
						onkeydown={(e) => handleEditKeydown(e, index)}
						onblur={() => {
							setTimeout(() => {
								if (editingIndex === index) saveEdit(index);
							}, 150);
						}}
						use:focus
					/>
					{@render autocompleteDropdown()}
				</div>
			{:else}
				<!-- Tag already added, visible as a label -->
				<span
					class="cursor-pointer truncate"
					ondblclick={() => startEditing(index, tag)}
					title="Double-click to edit"
					role="button"
					tabindex="0"
					onkeydown={(e) => {
						if (e.key === 'Enter' || e.key === ' ') {
							e.preventDefault();
							startEditing(index, tag);
						}
					}}
				>
					{tag}
				</span>
			{/if}
			<!-- Remove tag button -->
			<button
				class="hover:bg-base-300 ml-1 cursor-pointer p-1 leading-0"
				onclick={() => removeTag(tag)}
				aria-label={`Remove tag "${tag}"`}
			>
				<IconMdiClose class="h-4 w-4" />
			</button>
		</div>
	{/each}

	<!-- add a tag -->
	<div class="dropdown grow">
		<input
			type="text"
			class="input input-bordered w-full bg-transparent outline-hidden"
			onkeydown={inputHandler}
			bind:value={newValue}
		/>
		{@render autocompleteDropdown()}
	</div>
</div>
