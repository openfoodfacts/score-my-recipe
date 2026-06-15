<script lang="ts">
	import { resolve } from '$app/paths';
	import { _ } from '$lib/i18n';
</script>

<svelte:head>
	<title>{$_('landing.title')}</title>
</svelte:head>

<section class="relative px-6 py-20 lg:py-32 overflow-hidden">
  <div class="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-primary/10 rounded-full blur-3xl opacity-60"></div>
  <div class="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 bg-secondary/20 rounded-full blur-3xl opacity-50"></div>

  <div class="max-w-4xl mx-auto text-center relative z-10 animate-in fade-in slide-in-from-bottom-8 duration-1000">
    <div class="badge badge-outline badge-lg gap-2 px-4 py-4 text-sm font-bold mb-8 border-primary text-primary bg-base-100 shadow-sm">
      <span aria-hidden="true">*</span>
      L'outil open-source de la restauration collective
    </div>
    <h1 class="text-5xl md:text-6xl font-extrabold mb-8 leading-[1.1]">
      Calculez l'impact de vos recettes <br />
      <span class="text-primary">en temps réel.</span>
    </h1>
    <p class="text-xl text-base-content/70 max-w-2xl mx-auto font-medium leading-relaxed mb-12">
      Saisissez vos ingrédients naturellement. Notre outil structure vos fiches techniques, calcule instantanément le Green-Score et vous accompagne vers des menus plus durables.
    </p>
    <div class="flex items-center justify-center">
      <a href={resolve('/score')} class="btn btn-primary btn-lg">
        Ouvrir le calculateur de recettes
      </a>
    </div>
  </div>
</section>

<section class="bg-base-100 border-t border-base-300 py-24 px-6">
  <div class="max-w-6xl mx-auto">
    <div class="text-center mb-16">
      <h2 class="text-3xl font-extrabold mb-4">La boussole des professionnels</h2>
      <p class="text-base-content/70 font-medium text-lg">Améliorez facilement vos fiches techniques avec des données fiables.</p>
    </div>
    
  <div class="grid md:grid-cols-3 gap-12">
    <div class="text-center">
      <div class="w-16 h-16 mx-auto bg-base-200 text-primary rounded-2xl flex items-center justify-center mb-6 text-3xl font-bold">
        1
      </div>
      <h3 class="text-xl font-bold mb-3">Calcul en temps réel</h3>
      <p class="text-base-content/70 font-medium leading-relaxed">Ajustez facilement l'impact d'une recette en "jammant" sur les quantités ou en testant des substitutions d'ingrédients à la volée.</p>
    </div>
    
    <div class="text-center">
      <div class="w-16 h-16 mx-auto bg-success/15 text-success rounded-2xl flex items-center justify-center mb-6 text-3xl font-bold">
        2
      </div>
      <h3 class="text-xl font-bold mb-3">Transparence & Agribalyse</h3>
      <p class="text-base-content/70 font-medium leading-relaxed">Une méthodologie de calcul transparente, qui s'appuie sur la rigueur de la base publique Agribalyse portée par l'ADEME.</p>
    </div>

    <div class="text-center">
      <div class="w-16 h-16 mx-auto bg-info/15 text-info rounded-2xl flex items-center justify-center mb-6 text-3xl font-bold">
        3
      </div>
      <h3 class="text-xl font-bold mb-3">Score à forte notoriété</h3>
      <p class="text-base-content/70 font-medium leading-relaxed">Misez sur un indicateur validé et déjà identifié par des millions de consommateurs sur Open Food Facts et Yuka.</p>
    </div>
  </div>
</section>

<footer class="bg-primary text-primary-content py-12 px-6 text-center">
  <div class="max-w-4xl mx-auto flex flex-col items-center">
    <img src="https://static.openfoodfacts.org/images/logos/off-logo-horizontal-light.svg" alt="Open Food Facts" class="h-10 opacity-50 mb-6 grayscale" />
    <p class="text-primary-content/80 font-medium mb-3">Un projet open-source porté par Open Food Facts, conçu pour transformer l'impact de la restauration.</p>
    <div class="badge badge-outline border-primary-content/30 text-primary-content text-sm font-semibold px-4 py-4 mb-6">
      Projet réalisé de manière collaborative grâce au soutien de l'Appel à Communs de l'ADEME
    </div>
    <a href="https://github.com/openfoodfacts/score-my-recipe/" class="text-primary-content font-bold hover:underline">Découvrir le projet sur GitHub</a>
  </div>
</footer>
