<script>
	import { _ } from '$lib/i18n';
	import { offLinks } from '$lib/offLink';

	const navItems = $state([
		{ name: 'navbar.score_recipe', href: '/score' },
		{ name: 'navbar.join_community', href: offLinks.website },
		{ name: 'navbar.open_food_facts', href: offLinks.website },
		{ name: 'navbar.methodology', href: `${offLinks.website}/green-score` }
	]);
</script>

<nav class="bg-secondary mt-2 mb-8 px-4">
	<ul class="flex w-full justify-evenly">
		{#each navItems as item (item.name)}
			<li class="px-4 py-2">
				<a href={item.href} class="text-secondary-content font-medium hover:underline">
					{$_(item.name)}
				</a>
			</li>
		{/each}
	</ul>
</nav>
