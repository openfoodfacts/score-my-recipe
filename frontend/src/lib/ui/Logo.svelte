<!--
@component A logo element displaying openfoodfacts logo

@property {boolean} mono puts the logo in mono (eg. for footer)
-->
<script lang="ts">
	let {
		class: className = '',
		mono = false
	}: {
		mono?: boolean;
		class?: string;
	} = $props();
</script>

<picture class="flex items-center gap-4 {className}">
    <source
		srcset={mono
			? `https://static.openfoodfacts.org/images/logos/off-logo-horizontal-mono-white.svg`
			: `https://static.openfoodfacts.org/images/logos/off-logo-horizontal-dark.svg`}
		media="(prefers-color-scheme: dark)"
	/>
	<img src="https://static.openfoodfacts.org/images/logos/off-logo-horizontal-light.svg" alt="Open Food Facts" class="h-10" />
	<span class="font-bold text-xl border-l border-base-content/20 pl-4">pour les recettes</span>
</picture>
