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
	import { onMount } from 'svelte';
	import MultiSelect from 'svelte-multiselect';
	import { _ } from '$lib/i18n';
	import { getMatchingTags } from '$lib/api/taxonomy';

	type Option = { label: string; value: string };

	type Props = {
		id: string;
		tagtype: string;
		tags?: string[] | null;
		tag?: string | null; // use for single values selection
		required?: boolean; // If true, at least one tag is required
		allowUserOptions?: boolean; // If true, users can add custom tags not in the autocomplete list
		onChange?: (tags: string[]) => void;
	};

	let { id, tagtype, tags = $bindable(null), tag = $bindable(null), required = false, allowUserOptions = true, onChange }: Props = $props();

	if (tags !== null && tag !== null) {
		throw new Error("Tags component: 'tags' and 'tag' props are mutually exclusive. Please provide only one of them.");
	} else if (tag === null && tags === null) {
		throw new Error("Tags component: Either 'tags' or 'tag' prop must be provided.");
	}
	const single = tags === null; // whether we are in single tag mode or multiple tags mode

	// Initialize selected from props on mount
	let selected = $state<Option[]>([]);
	let initialized = $state(false);
	let isInternalUpdate = $state(false);
	$inspect(id, selected, initialized, isInternalUpdate, tag, tags);

	onMount(() => {
		if (tags !== null) {
			selected = tags.map(t => ({ label: t, value: t }));
		} else if (tag !== null) {
			selected = tag ? [{ label: tag, value: tag }] : [];
		}
		initialized = true;
	});

	// Sync selected when tags/tag props change from parent (only if not internal update)
	$effect(() => {
		if (!initialized || isInternalUpdate) return;

		if (tags !== null) {
			const newSelected = tags.map(t => ({ label: t, value: t }));
			if (JSON.stringify(selected) !== JSON.stringify(newSelected)) {
				selected = newSelected;
			}
		} else if (tag !== null) {
			const newSelected = tag ? [{ label: tag, value: tag }] : [];
			if (JSON.stringify(selected) !== JSON.stringify(newSelected)) {
				selected = newSelected;
			}
		}
	});

	// Handle selection changes - propagate to parent
	function onSelect(newSelected: Option[]) {
		isInternalUpdate = true;
		try {
			if (single) {
				// Single tag mode
				const newTag = newSelected.length > 0 ? newSelected[0].value : "";
				tag = newTag;
				onChange?.([newTag]);
			} else {
				// Multiple tags mode
				const newTags = newSelected.map(item => item.value);
				tags = newTags;
				onChange?.(newTags);
			}
		} finally {
			isInternalUpdate = false;
		}
	}

	async function loadOptions({search, limit}: {search: string, limit: number}) {
		const response = await getMatchingTags(tagtype, search, limit);
		return {
			options: response.suggestions.map(
				suggestion => (
					{ label: suggestion, value: suggestion }
				)
		),
			hasMore: false,
		};
	}

</script>

<MultiSelect
 	--sms-border-radius="1rem"
	--sms-open-z-index="1"
    {id}
	{selected}
	placeholder={$_("tag.add_tag_" + tagtype)}
	loadOptions={{ fetch: loadOptions, debounceMs: 300, batchSize: 20 }}
	maxSelect={single ? 1 : null}
	{required}
	{allowUserOptions}
	loading={true}
	on:change={(e) => onSelect(e.detail as Option[])}
	>
</MultiSelect>