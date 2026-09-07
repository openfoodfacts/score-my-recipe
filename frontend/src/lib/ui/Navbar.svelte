<script>
	import { _ } from '$lib/i18n';
	import Logo from '$lib/ui/Logo.svelte';
	import { offLinks } from '$lib/offLink';
	import { locales, locale } from "svelte-i18n";

	const navItems = $state([
		{ name: 'navbar.score_recipe', href: '/add' },
		{ name: 'navbar.methodology', href: `${offLinks.website}/green-score` }
	]);

	let { value } = $props();
	function updateLanguage(event) {
		locale.set(event.target.value);
	}
</script>

<nav class="bg-base-200 border-base-300 sticky top-0 z-50 border-b">
	<div
		class="mx-auto flex w-full max-w-7xl flex-row justify-between gap-4 px-6 py-4 md:items-center"
	>
		<Logo class="flex-2"/>
		<ul class="hidden justify-evenly md:flex md:flex-2">
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
			<!--  
				TODO make not overlap with join comunity button
				TODO make me readable
				TODO should we keep fr-FR or change to only FR?
			-->
		<div class="locale-selector flex flex-1">
			<div class="select">
				<select value={value} onchange={updateLanguage}>
					{#each $locales as locale }
						<option value={locale}>{locale}</option>
					{/each}
				</select>
			</div>
		</div>
	</div>
</nav>

<nav class="bg-secondary mt-2 mb-8 px-4"></nav>
