<script>
	import { _ } from '$lib/i18n';
	import Logo from '$lib/ui/Logo.svelte';
	import { offLinks } from '$lib/offLink';
	import LanguageButton from './LanguageButton.svelte';
	import { resolve } from '$app/paths';
	import { savedRecipes } from '$lib/stores/savedRecipes.svelte';

	const navItems = $state([
		{ name: 'navbar.score_recipe', href: resolve('/add') },
		{ name: 'navbar.methodology', href: `${offLinks.website}/green-score` }
	]);

	// Shown only once the browser actually holds saved recipes. `recipes` is
	// reactive, so the link appears immediately after the first save.
	let hasSavedRecipes = $derived(savedRecipes.recipes.length > 0);
</script>

<nav class="bg-base-200 border-base-300 sticky top-0 z-50 border-b">
	<div
		class="mx-auto flex w-full max-w-7xl flex-row flex-wrap justify-between gap-4 px-6 py-4 md:items-center"
	>
		<Logo class="flex-2" />
		<ul
			class="order-3 flex w-full flex-wrap justify-evenly gap-x-4 gap-y-1 md:order-none md:w-auto md:flex-2"
		>
			{#if hasSavedRecipes}
				<li class="px-4 py-2">
					<a href={resolve('/my-recipes')} class="font-medium hover:underline">
						{$_('navbar.my_recipes', { default: 'My recipes' })}
					</a>
				</li>
			{/if}
			{#each navItems as item (item.name)}
				<li class="px-4 py-2">
					<a href={item.href} class="font-medium hover:underline">
						{$_(item.name)}
					</a>
				</li>
			{/each}
		</ul>

		<div class="hidden gap-4 lg:flex lg:flex-1">
			<button class="btn btn-primary font-bold">
				{$_('navbar.join_community')}
			</button>
		</div>

		<LanguageButton />
	</div>
</nav>

<nav class="bg-secondary mt-2 mb-8 px-4"></nav>
