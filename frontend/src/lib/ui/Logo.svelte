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

<picture class="flex w-full items-center gap-4 {className}">
	<source
		srcset={mono
			? `https://static.openfoodfacts.org/images/logos/off-logo-horizontal-mono-white.svg`
			: `https://static.openfoodfacts.org/images/logos/off-logo-horizontal-dark.svg`}
		media="(prefers-color-scheme: dark)"
	/>
	<a href="/">
		<img
			src="https://static.openfoodfacts.org/images/logos/off-logo-horizontal-light.svg"
			alt="Open Food Facts"
			class="h-10"
		/>
	</a>
	<a href="/" class="border-base-content/20 border-l pl-4 text-xl font-bold">pour les recettes</a>
</picture>
