<script lang="ts">
	import { resolve } from '$app/paths';
	import { _ } from '$lib/i18n';
</script>

<svelte:head>
	<title>{$_('homepage.title')}</title>
</svelte:head>

<section class="relative overflow-hidden px-6 py-20 lg:py-32">
	<div
		class="bg-primary/10 absolute top-0 right-0 -mt-20 -mr-20 h-96 w-96 rounded-full opacity-60 blur-3xl"
	></div>
	<div
		class="bg-secondary/20 absolute bottom-0 left-0 -mb-20 -ml-20 h-80 w-80 rounded-full opacity-50 blur-3xl"
	></div>

	<div
		class="animate-in fade-in slide-in-from-bottom-8 relative z-10 mx-auto max-w-4xl text-center duration-1000"
	>
		<div
			class="badge badge-outline badge-lg border-primary text-primary bg-base-100 mb-8 gap-2 px-4 py-4 text-sm font-bold shadow-sm"
		>
			<span aria-hidden="true">*</span>
			{$_('homepage.badge')}
		</div>
		<h1 class="mb-8 text-5xl leading-[1.1] font-extrabold md:text-6xl">
			{$_('homepage.hero_title')} <br />
			<span class="text-primary">{$_('homepage.hero_title_highlight')}</span>
		</h1>
		<p class="text-base-content/70 mx-auto mb-12 max-w-2xl text-xl leading-relaxed font-medium">
			{$_('homepage.hero_description')}
		</p>
		<div class="flex items-center justify-center">
			<a href={resolve('/score')} class="btn btn-primary btn-lg">
				{$_('homepage.cta_recipe_calculator')}
			</a>
		</div>
	</div>
</section>

<section class="bg-base-100 border-base-300 border-t px-6 py-24">
	<div class="mx-auto max-w-6xl">
		<div class="mb-16 text-center">
			<h2 class="mb-4 text-3xl font-extrabold">{$_('homepage.section2_title')}</h2>
			<p class="text-base-content/70 text-lg font-medium">{$_('homepage.section2_description')}</p>
		</div>

		<div class="grid gap-12 md:grid-cols-3">
			<div class="text-center">
				<div
					class="bg-base-200 text-primary mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl text-3xl font-bold"
				>
					1
				</div>
				<h3 class="mb-3 text-xl font-bold">{$_('homepage.feature1_title')}</h3>
				<p class="text-base-content/70 leading-relaxed font-medium">
					{$_('homepage.feature1_description')}
				</p>
			</div>

			<div class="text-center">
				<div
					class="bg-success/15 text-success mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl text-3xl font-bold"
				>
					2
				</div>
				<h3 class="mb-3 text-xl font-bold">{$_('homepage.feature2_title')}</h3>
				<p class="text-base-content/70 leading-relaxed font-medium">
					{$_('homepage.feature2_description')}
				</p>
			</div>

			<div class="text-center">
				<div
					class="bg-info/15 text-info mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl text-3xl font-bold"
				>
					3
				</div>
				<h3 class="mb-3 text-xl font-bold">{$_('homepage.feature3_title')}</h3>
				<p class="text-base-content/70 leading-relaxed font-medium">
					{$_('homepage.feature3_description')}
				</p>
			</div>
		</div>
	</div>
</section>

<footer class="bg-primary text-primary-content px-6 py-12 text-center">
	<div class="mx-auto flex max-w-4xl flex-col items-center">
		<p class="text-primary-content/80 mb-3 font-medium">{$_('homepage.footer_text')}</p>
		<div
			class="badge badge-outline border-primary-content/30 text-primary-content mb-6 px-4 py-4 text-sm font-semibold"
		>
			{$_('homepage.footer_badge')}
		</div>
		<a
			href="https://github.com/openfoodfacts/score-my-recipe/"
			class="text-primary-content font-bold hover:underline">{$_('homepage.footer_github_link')}</a
		>
	</div>
</footer>
