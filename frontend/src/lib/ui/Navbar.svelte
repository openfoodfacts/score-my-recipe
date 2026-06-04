<script>
	import { _ } from '$lib/i18n';
	import { offLinks } from '$lib/offLink';

	const navItems = $state([
		{ name: 'navbar.score_recipe', href: '/score' },
		{ name: 'navbar.join_community', href: offLinks.website },
		{ name: 'navbar.open_food_facts', href: 'world.openfoodfacts.org' }
	]);
</script>

<nav class="bg-secondary mt-2 mb-8 px-4">
	<ul class="flex justify-center">
		<div class="m-2 flex w-3/4 items-center justify-evenly 2xl:w-[60%]">
			{#each navItems as item (item.name)}
				<li>
					<a href={item.href} class="text-secondary-content font-medium hover:underline">
						{$_(item.name)}
					</a>
				</li>
			{/each}
		</div>
	</ul>
</nav>
