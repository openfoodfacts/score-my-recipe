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

<picture class={className}>
	<source
		srcset={mono
			? `https://static.openfoodfacts.org/images/logos/off-logo-horizontal-mono-white.svg`
			: `https://static.openfoodfacts.org/images/logos/off-logo-horizontal-dark.svg`}
		media="(prefers-color-scheme: dark)"
	/>
	<img
		src={mono
			? `https://static.openfoodfacts.org/images/logos/off-logo-horizontal-mono-black.svg`
			: `https://static.openfoodfacts.org/images/logos/off-logo-horizontal-light.svg`}
		alt="OpenFoodFacts Explorer"
		class="h-full w-full object-contain"
	/>
</picture>
