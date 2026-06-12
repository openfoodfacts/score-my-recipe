<script lang="ts">
	import { _ } from '$lib/i18n';
</script>

<svelte:head>
	<title>{$_('landing.title')}</title>
</svelte:head>
<main class="mx-auto flex w-full max-w-7xl flex-col gap-12 px-6 py-10 md:py-16">
	<section class="hero bg-base-200 rounded-2xl px-6 py-12 md:px-10">
		<div class="hero-content w-full max-w-4xl px-0 text-left">
			<div class="space-y-6">
				<p class="badge badge-outline">{$_('landing.badge')}</p>
				<h1 class="text-4xl font-bold md:text-5xl">{$_('landing.hero_title')}</h1>
				<p class="text-base-content/75 max-w-2xl text-lg">
					{$_('landing.hero_description')}
				</p>
				<div class="flex flex-wrap gap-3">
					<a class="btn btn-primary" href="#demonstration">{$_('landing.cta_demo')}</a>
					<a class="btn btn-outline" href="https://world.openfoodfacts.org/green-score"
						>{$_('landing.cta_methodology')}</a
					>
				</div>
			</div>
		</div>
	</section>

	<section id="demonstration" class="grid gap-6 md:grid-cols-3">
		<article class="card bg-base-100 shadow-sm">
			<div class="card-body">
				<h2 class="card-title">{$_('landing.step_1_title')}</h2>
				<p>{$_('landing.step_1_description')}</p>
			</div>
		</article>
		<article class="card bg-base-100 shadow-sm">
			<div class="card-body">
				<h2 class="card-title">{$_('landing.step_2_title')}</h2>
				<p>{$_('landing.step_2_description')}</p>
			</div>
		</article>
		<article class="card bg-base-100 shadow-sm">
			<div class="card-body">
				<h2 class="card-title">{$_('landing.step_3_title')}</h2>
				<p>{$_('landing.step_3_description')}</p>
			</div>
		</article>
	</section>
</main>
