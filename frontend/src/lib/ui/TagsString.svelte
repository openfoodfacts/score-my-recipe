<!--
  TagsString.svelte

  A Svelte component for managing a list of tags represented as a single string with a specified separator.
  It uses the Tags.svelte component internally to handle tag addition, editing, and removal.

  Props:
	- tagsString: A string representing the current tags, separated by the specified separator.
	- separator: A string used to separate tags in the tagsString. Defaults to ','.
	- autocomplete: An array of strings for autocomplete suggestions.
-->
<script lang="ts">
	import Tags from './Tags.svelte';

	type Props = {
		tagsString: string;
		separator?: string;
		autocomplete?: readonly string[];
	};

	let { tagsString = $bindable(), separator = ',', autocomplete = [] }: Props = $props();
</script>

<Tags
	{autocomplete}
	tags={tagsString?.split(separator)?.filter((str) => str !== '') ?? []}
	onChange={(tags) => (tagsString = tags.join(separator))}
/>
