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
				<p class="badge badge-outline">Open Food Facts for recipes</p>
				<h1 class="text-4xl font-bold md:text-5xl">Calculez simplement l’impact de vos recettes</h1>
				<p class="text-base-content/75 max-w-2xl text-lg">
					Un format simple pour démarrer : renseignez vos ingrédients, obtenez votre Green-Score et
					améliorez vos menus.
				</p>
				<div class="flex flex-wrap gap-3">
					<a class="btn btn-primary" href="#demonstration">Voir la démonstration</a>
					<a class="btn btn-outline" href="https://world.openfoodfacts.org/green-score"
						>Découvrir la méthodologie</a
					>
				</div>
			</div>
		</div>
	</section>

	<section id="demonstration" class="grid gap-6 md:grid-cols-3">
		<article class="card bg-base-100 shadow-sm">
			<div class="card-body">
				<h2 class="card-title">1. Saisie claire</h2>
				<p>Entrez vos ingrédients et quantités dans une fiche recette lisible.</p>
			</div>
		</article>
		<article class="card bg-base-100 shadow-sm">
			<div class="card-body">
				<h2 class="card-title">2. Score instantané</h2>
				<p>Le Green-Score est calculé immédiatement à partir des données Open Food Facts.</p>
			</div>
		</article>
		<article class="card bg-base-100 shadow-sm">
			<div class="card-body">
				<h2 class="card-title">3. Action rapide</h2>
				<p>Identifiez les meilleures substitutions pour réduire l’impact carbone de vos menus.</p>
			</div>
		</article>
	</section>
</main>
