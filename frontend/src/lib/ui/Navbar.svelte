<script>
	import { _ } from '$lib/i18n';
	import Logo from '$lib/ui/Logo.svelte';
	import { offLinks } from '$lib/offLink';

	const navItems = $state([
		{ name: 'navbar.score_recipe', href: '/score' },
		{ name: 'navbar.join_community', href: offLinks.website },
		{ name: 'navbar.methodology', href: `${offLinks.website}/green-score` }
	]);
</script>



  <nav class="bg-base-200 border-b border-base-300 sticky top-0 z-50">
    <div class="px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 max-w-7xl mx-auto w-full">
	  <Logo/>
      <div class="hidden md:flex gap-4">
        <button class="btn btn-primary font-bold">
          Rejoindre la communauté de pratique
        </button>
      </div>
    </div>
  </nav>

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
