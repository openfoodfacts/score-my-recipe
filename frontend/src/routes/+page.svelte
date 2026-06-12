<script lang="ts">
	import { resolve } from '$app/paths';
	import { _ } from '$lib/i18n';

  // --- DONNÉES SIMULÉES ---
  const ingredientsDB = {
    'Bœuf (Haché)': { co2: 28.0, price: 12.50, nutriscore: 'C' },
    'Poulet (Filet)': { co2: 6.0, price: 9.80, nutriscore: 'B' },
    'Lentilles Vertes': { co2: 0.9, price: 3.20, nutriscore: 'A' },
    'Tomates (Saison)': { co2: 0.4, price: 2.50, nutriscore: 'A' },
    'Crème Entière': { co2: 5.5, price: 4.50, nutriscore: 'D' },
    'Crème de Soja': { co2: 1.2, price: 3.80, nutriscore: 'B' },
    'Pâtes (Blé)': { co2: 1.4, price: 1.80, nutriscore: 'A' },
    'Carottes': { co2: 0.3, price: 1.20, nutriscore: 'A' },
    'Oignons': { co2: 0.4, price: 1.50, nutriscore: 'A' },
    'Beurre Doux': { co2: 8.0, price: 9.00, nutriscore: 'E' }
  };

  const ingredientsList = Object.keys(ingredientsDB);

  // --- UTILITAIRES ---
  const getEcoScoreGrade = (score) => {
    if (score < 1.5) return 'a';
    if (score < 3.0) return 'b';
    if (score < 5.0) return 'c';
    if (score < 8.0) return 'd';
    return 'e';
  };

  const calculateRecipeNutriScore = (ingredients, totalWeight) => {
    if (totalWeight === 0) return 'c';
    const scoreMap = { 'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5 };
    const reverseMap = [null, 'a', 'b', 'c', 'd', 'e'];
    let totalScore = 0;
    ingredients.forEach(ing => {
      const weight = scoreMap[ing.nutriscore] || 3;
      totalScore += weight * (parseFloat(ing.qty) || 0);
    });
    const avg = totalScore / totalWeight;
    return reverseMap[Math.round(avg)] || 'c';
  };

  // --- ÉTATS ---
  let lines = [
    { id: 1, ingredient: 'Bœuf (Haché)', qty: '1.5', unit: 'kg', origin: 'France', label: 'Conventionnel' },
    { id: 2, ingredient: 'Pommes de terre', qty: '0.8', unit: 'kg', origin: 'France', label: 'Bio' },
    { id: 3, ingredient: '', qty: '', unit: 'kg', origin: '', label: '' }
  ];

  let isFeaturesOpen = false;

  // --- ACTIONS ---
  const handleInput = (index, field, value) => {
    lines[index][field] = value;
    lines = lines; // Déclenche la réactivité Svelte

    // Ajout automatique d'une ligne vide si on remplit la dernière
    if (index === lines.length - 1 && (lines[index].ingredient.trim() !== '' || lines[index].qty !== '')) {
      lines = [...lines, { 
        id: Date.now(),
        ingredient: '', 
        qty: '', 
        unit: 'kg', 
        origin: '', 
        label: '' 
      }];
    }
  };

  const removeLine = (idToRemove) => {
    if (lines.length > 1) {
      lines = lines.filter(line => line.id !== idToRemove);
    }
  };

  // --- CALCULS DYNAMIQUES ---
  $: validLines = lines.filter(line => line.ingredient.trim() !== '' && parseFloat(line.qty) > 0);
  
  $: totalWeight = validLines.reduce((sum, line) => {
    let multiplier = line.unit === 'g' ? 0.001 : 1;
    return sum + ((parseFloat(line.qty) || 0) * multiplier);
  }, 0);

  $: totalCO2 = validLines.reduce((sum, line) => {
    let multiplier = line.unit === 'g' ? 0.001 : 1;
    const qtyKg = (parseFloat(line.qty) || 0) * multiplier;
    const co2PerKg = ingredientsDB[line.ingredient] ? ingredientsDB[line.ingredient].co2 : 1.5; // Fallback
    return sum + (qtyKg * co2PerKg);
  }, 0);

  $: scorePerKg = totalWeight > 0 ? totalCO2 / totalWeight : 0;
  $: ecoGrade = validLines.length === 0 ? 'unknown' : getEcoScoreGrade(scorePerKg);
  $: nutriGrade = validLines.length === 0 ? 'unknown' : calculateRecipeNutriScore(validLines, totalWeight);

</script>

<svelte:head>
	<title>{$_('landing.title')}</title>
</svelte:head>

<div class="min-h-screen bg-base-100 text-base-content font-sans">
  
  <datalist id="ingredients-list">
    {#each ingredientsList as item}
      <option value={item}></option>
    {/each}
  </datalist>
  <datalist id="origins-list">
    <option value="France"></option>
    <option value="Europe"></option>
    <option value="Monde"></option>
  </datalist>
  <datalist id="labels-list">
    <option value="Conventionnel"></option>
    <option value="Bio"></option>
    <option value="Label Rouge"></option>
    <option value="AOP/AOC"></option>
  </datalist>

  <nav class="bg-base-200 border-b border-base-300 sticky top-0 z-50">
    <div class="px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 max-w-7xl mx-auto w-full">
      <div class="flex items-center gap-4">
        <img src="https://static.openfoodfacts.org/images/logos/off-logo-horizontal-light.svg" alt="Open Food Facts" class="h-10" />
        <span class="font-bold text-xl border-l border-base-content/20 pl-4">pour les recettes</span>
      </div>
      <div class="hidden md:flex gap-4">
        <button class="btn btn-primary font-bold">
          Rejoindre la communauté de pratique
        </button>
      </div>
    </div>
  </nav>

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

<!--
  <section class="px-6 pb-24 relative z-20">
    <div class="max-w-6xl mx-auto bg-white rounded-3xl shadow-2xl border border-gray-100 overflow-hidden flex flex-col lg:flex-row animate-in fade-in zoom-in-95 duration-1000 delay-200">
      
      <div class="flex-1 p-8 lg:p-10 border-b lg:border-b-0 lg:border-r border-gray-100">
        <div class="flex justify-between items-center mb-6">
          <div>
            <h2 class="text-2xl font-bold text-black flex items-center">
              Mon Hachis Parmentier
            </h2>
            <p class="text-sm font-medium text-gray-500 flex items-center mt-1">
              <Zap size={14} class="mr-1 text-yellow-500" /> 
              Modifiez les lignes ci-dessous, la suivante s'ajoute toute seule !
            </p>
          </div>
        </div>

        <div class="grid grid-cols-12 gap-3 pb-3 border-b border-gray-100 text-xs font-bold text-gray-400 uppercase tracking-wider">
          <div class="col-span-5">Ingrédient</div>
          <div class="col-span-3">Quantité</div>
          <div class="col-span-3">Origine</div>
          <div class="col-span-1"></div>
        </div>

        <div class="space-y-1 mt-3">
          {#each lines as line, i (line.id)}
            <div class="grid grid-cols-12 gap-3 items-center p-2 -mx-2 rounded-xl hover:bg-[#f2e9e4]/30 transition-colors group">
              <div class="col-span-5">
                <input 
                  type="text" 
                  list="ingredients-list"
                  value={line.ingredient} 
                  on:input={(e) => handleInput(i, 'ingredient', e.target.value)}
                  placeholder="Tapez un ingrédient..."
                  class="w-full bg-transparent border-b-2 border-transparent hover:border-gray-200 focus:border-[#341100] outline-none py-1.5 text-black font-bold placeholder-gray-300 transition"
                />
              </div>
              <div class="col-span-3 flex items-center gap-1">
                <input 
                  type="number" 
                  min="0" step="0.1"
                  value={line.qty} 
                  on:input={(e) => handleInput(i, 'qty', e.target.value)}
                  placeholder="0"
                  class="w-full bg-transparent border-b-2 border-transparent hover:border-gray-200 focus:border-[#341100] outline-none py-1.5 text-black font-bold text-right transition"
                />
                <select 
                  value={line.unit}
                  on:change={(e) => handleInput(i, 'unit', e.target.value)}
                  class="bg-transparent border-b-2 border-transparent hover:border-gray-200 focus:border-[#341100] outline-none py-1.5 text-gray-500 font-medium cursor-pointer transition appearance-none"
                >
                  <option value="kg">kg</option>
                  <option value="g">g</option>
                </select>
              </div>
              <div class="col-span-3">
                <input 
                  type="text" 
                  list="origins-list"
                  value={line.origin}
                  on:input={(e) => handleInput(i, 'origin', e.target.value)}
                  placeholder="Auto"
                  class="w-full bg-transparent border-b-2 border-transparent hover:border-gray-200 focus:border-[#341100] outline-none py-1.5 text-gray-500 font-medium transition"
                />
              </div>
              <div class="col-span-1 flex justify-end">
                {#if lines.length > 1}
                  <button 
                    on:click={() => removeLine(line.id)}
                    class="text-gray-300 hover:text-red-500 p-1.5 opacity-0 group-hover:opacity-100 transition-opacity rounded-md hover:bg-red-50"
                  >
                    <Trash2 size={16} />
                  </button>
                {/if}
              </div>
            </div>
          {/each}
        </div>
        
        <div class="mt-8 flex justify-end">
          <button class="text-[#341100] font-bold text-sm flex items-center hover:underline">
            <Sparkles size={16} class="mr-1" />
            Essayer l'outil
          </button>
        </div>
      </div>

      <div class="lg:w-80 bg-[#f2e9e4]/40 p-8 lg:p-10 flex flex-col justify-center items-center text-center">
        
        <h3 class="text-sm font-bold text-[#341100] uppercase tracking-wider mb-8">Résultat en direct</h3>
        
        {#if ecoGrade === 'unknown'}
          <div class="space-y-6">
            <div class="w-32 h-32 mx-auto rounded-xl bg-white border-2 border-dashed border-[#e0d6d0] flex items-center justify-center">
              <span class="text-4xl text-[#e0d6d0] font-bold">?</span>
            </div>
            <p class="text-gray-500 font-medium text-sm">Ajoutez des ingrédients pour voir l'impact.</p>
          </div>
        {:else}
          <div class="space-y-10 animate-in fade-in zoom-in-95 duration-300 w-full">
            
            <div class="flex flex-col items-center">
              <img 
                src={`https://static.openfoodfacts.org/images/attributes/dist/green-score-${ecoGrade}.svg`} 
                alt={`Green-Score ${ecoGrade.toUpperCase()}`} 
                class="h-28 transition-all duration-300 transform hover:scale-105" 
              />
              <div class="mt-4 bg-white px-4 py-2 rounded-xl shadow-sm border border-gray-100 w-full">
                <p class="text-xl font-extrabold text-[#341100]">{scorePerKg.toFixed(2)} <span class="text-xs font-semibold text-gray-500">kg CO₂e/kg</span></p>
                <p class="text-xs font-bold text-gray-400 mt-1">Total : ({totalCO2.toFixed(2)} kg CO₂e)</p>
              </div>
            </div>

            <div class="flex flex-col items-center">
              <img 
                src={`https://static.openfoodfacts.org/images/attributes/dist/nutriscore-${nutriGrade}-new-fr.svg`} 
                alt={`Nutri-Score ${nutriGrade.toUpperCase()}`} 
                class="h-16 transition-all duration-300" 
              />
            </div>

          </div>
        {/if}
        
        <button class="mt-12 w-full bg-[#341100] text-white py-4 rounded-xl font-bold shadow-lg hover:bg-black transition flex items-center justify-center">
          Sauvegarder ma recette <ArrowRight size={18} class="ml-2" />
        </button>
      </div>

    </div>
  </section>
-->

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
<!--
      <div class="mt-20">
        <button 
          on:click={() => setIsFeaturesOpen(!isFeaturesOpen)}
          class="flex items-center justify-between w-full p-6 bg-[#faf9f8] hover:bg-[#f2e9e4]/40 border border-gray-200 rounded-2xl transition-all duration-300"
        >
          <div class="flex items-center gap-3">
            <Sparkles size={24} class="text-[#341100]" />
            <span class="font-extrabold text-xl text-black">Fonctionnalités avancées (En discussion)</span>
          </div>
          {#if isFeaturesOpen}
            <ChevronUp size={24} class="text-gray-400" />
          {:else}
            <ChevronDown size={24} class="text-gray-400" />
          {/if}
        </button>

        {#if isFeaturesOpen}
          <div class="grid md:grid-cols-3 gap-6 mt-6 animate-in slide-in-from-top-4 fade-in duration-300">
            <div class="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
              <div class="flex items-center gap-3 mb-3">
                <Zap size={20} class="text-[#341100]" />
                <h4 class="font-bold text-black">Saisie Zéro Friction</h4>
              </div>
              <p class="text-sm text-gray-500 font-medium leading-relaxed">Fini les formulaires complexes. Notre interface s'adapte à vous : saisie magique, import massif de fichiers Excel, et même scan de photos via l'IA.</p>
            </div>

            <div class="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
              <div class="flex items-center gap-3 mb-3">
                <Target size={20} class="text-[#341100]" />
                <h4 class="font-bold text-black">Pilotage EGalim & Climat</h4>
              </div>
              <p class="text-sm text-gray-500 font-medium leading-relaxed">Suivez vos objectifs réglementaires (Bio, Durable) en un coup d'œil, et assurez-vous de rester sous les limites planétaires (2t de CO2 par an).</p>
            </div>

            <div class="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
              <div class="flex items-center gap-3 mb-3">
                <BookOpen size={20} class="text-[#341100]" />
                <h4 class="font-bold text-black">Pédagogie Actionnable</h4>
              </div>
              <p class="text-sm text-gray-500 font-medium leading-relaxed">Ne soyez plus seul face aux chiffres. Notre coach suggère des substitutions intelligentes pour améliorer vos scores sans exploser vos coûts matières.</p>
            </div>
          </div>
        {/if}
      </div>-->
    </div>
  </section>

  <footer class="bg-primary text-primary-content py-12 px-6 text-center">
    <div class="max-w-4xl mx-auto flex flex-col items-center">
      <img src="https://static.openfoodfacts.org/images/logos/off-logo-horizontal-light.svg" alt="Open Food Facts" class="h-10 opacity-50 mb-6 grayscale" />
      <p class="text-primary-content/80 font-medium mb-3">Un projet open-source porté par Open Food Facts, conçu pour transformer l'impact de la restauration.</p>
      <div class="badge badge-outline border-primary-content/30 text-primary-content text-sm font-semibold px-4 py-4 mb-6">
        Projet réalisé de manière collaborative grâce au soutien de l'Appel à Communs de l'ADEME
      </div>
      <a href="#" class="text-primary-content font-bold hover:underline">Découvrir le projet sur GitHub</a>
    </div>
  </footer>

</div>
