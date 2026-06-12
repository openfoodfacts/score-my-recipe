<script lang="ts">
	import { resolve } from '$app/paths';

	import { _ } from '$lib/i18n';
</script>

<svelte:head>
	<title>{$_('landing.title')}</title>
</svelte:head>


import React, { useState, useMemo } from 'react';
import { Leaf, Sparkles, ArrowRight, Zap, Target, BookOpen, Trash2, Activity, Database, Award, ChevronDown, ChevronUp } from 'lucide-react';

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
    totalScore += weight * ing.qty;
  });
  const avg = totalScore / totalWeight;
  return reverseMap[Math.round(avg)] || 'c';
};

// --- COMPOSANT PRINCIPAL ---
export default function App() {
  // Lignes de la recette interactives
  const [lines, setLines] = useState([
    { id: 1, ingredient: 'Bœuf (Haché)', qty: '1.5', unit: 'kg', origin: 'France', label: 'Conventionnel' },
    { id: 2, ingredient: 'Pommes de terre', qty: '0.8', unit: 'kg', origin: 'France', label: 'Bio' },
    { id: 3, ingredient: '', qty: '', unit: 'kg', origin: '', label: '' }
  ]);

  const [isFeaturesOpen, setIsFeaturesOpen] = useState(false);

  const handleInput = (index, field, value) => {
    const newLines = [...lines];
    newLines[index][field] = value;
    setLines(newLines);

    // Ajout automatique d'une ligne vide si on remplit la dernière
    if (index === lines.length - 1 && (newLines[index].ingredient.trim() !== '' || newLines[index].qty !== '')) {
      setLines([...newLines, { 
        id: Date.now(),
        ingredient: '', 
        qty: '', 
        unit: 'kg', 
        origin: '', 
        label: '' 
      }]);
    }
  };

  const removeLine = (idToRemove) => {
    if (lines.length > 1) {
      setLines(lines.filter(line => line.id !== idToRemove));
    }
  };

  // Calculs dynamiques
  const validLines = useMemo(() => lines.filter(line => line.ingredient.trim() !== '' && parseFloat(line.qty) > 0), [lines]);
  
  const totalWeight = useMemo(() => validLines.reduce((sum, line) => {
    let multiplier = line.unit === 'g' ? 0.001 : 1;
    return sum + ((parseFloat(line.qty) || 0) * multiplier);
  }, 0), [validLines]);

  const totalCO2 = useMemo(() => validLines.reduce((sum, line) => {
    let multiplier = line.unit === 'g' ? 0.001 : 1;
    const qtyKg = (parseFloat(line.qty) || 0) * multiplier;
    const co2PerKg = ingredientsDB[line.ingredient] ? ingredientsDB[line.ingredient].co2 : 1.5; // Fallback
    return sum + (qtyKg * co2PerKg);
  }, 0), [validLines]);

  const scorePerKg = totalWeight > 0 ? totalCO2 / totalWeight : 0;
  const ecoGrade = validLines.length === 0 ? 'unknown' : getEcoScoreGrade(scorePerKg);
  const nutriGrade = validLines.length === 0 ? 'unknown' : calculateRecipeNutriScore(validLines, totalWeight);

  return (
    <div className="min-h-screen bg-[#faf9f8] text-gray-800 font-sans" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
      <style dangerouslySetInnerHTML={{__html: `@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap');`}} />
      
      {/* Datalists pour l'autocomplétion */}
      <datalist id="ingredients-list">{ingredientsList.map(item => <option key={item} value={item} />)}</datalist>
      <datalist id="origins-list"><option value="France"/><option value="Europe"/><option value="Monde"/></datalist>
      <datalist id="labels-list"><option value="Conventionnel"/><option value="Bio"/><option value="Label Rouge"/><option value="AOP/AOC"/></datalist>

      {/* NAVBAR */}
      <nav className="bg-[#f2e9e4] border-b border-[#e0d6d0] sticky top-0 z-50">
        <div className="px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 max-w-7xl mx-auto w-full">
          <div className="flex items-center gap-4">
            <img src="https://static.openfoodfacts.org/images/logos/off-logo-horizontal-light.svg" alt="Open Food Facts" className="h-10" />
            <span className="font-bold text-black text-xl border-l border-black/20 pl-4">pour les recettes</span>
          </div>
          <div className="hidden md:flex gap-4">
            <button className="bg-[#341100] text-white font-bold px-6 py-2 rounded-lg hover:bg-black transition shadow-sm">
              Rejoindre la communauté de pratique
            </button>
          </div>
        </div>
      </nav>

      {/* HERO SECTION */}
      <section className="relative px-6 py-20 lg:py-32 overflow-hidden">
        {/* Background blobs */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-[#f2e9e4] rounded-full blur-3xl opacity-60"></div>
        <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 bg-emerald-100 rounded-full blur-3xl opacity-50"></div>

        <div className="max-w-4xl mx-auto text-center relative z-10 animate-in fade-in slide-in-from-bottom-8 duration-1000">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-white shadow-sm border border-gray-100 text-[#341100] rounded-full text-sm font-bold mb-8">
            <Sparkles size={16} className="text-yellow-500" />
            L'outil open-source de la restauration collective
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold text-black mb-8 leading-[1.1]">
            Calculez l'impact de vos recettes <br />
            <span className="text-[#341100]">en temps réel.</span>
          </h1>
          <p className="text-xl text-gray-500 max-w-2xl mx-auto font-medium leading-relaxed mb-12">
            Saisissez vos ingrédients naturellement. Notre outil structure vos fiches techniques, calcule instantanément le Green-Score et vous accompagne vers des menus plus durables.
          </p>
        </div>
      </section>

      {/* INTERACTIVE DEMO SECTION */}
      <section className="px-6 pb-24 relative z-20">
        <div className="max-w-6xl mx-auto bg-white rounded-3xl shadow-2xl border border-gray-100 overflow-hidden flex flex-col lg:flex-row animate-in fade-in zoom-in-95 duration-1000 delay-200">
          
          {/* LEFT: RECIPE EDITOR */}
          <div className="flex-1 p-8 lg:p-10 border-b lg:border-b-0 lg:border-r border-gray-100">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-bold text-black flex items-center">
                  Mon Hachis Parmentier
                </h2>
                <p className="text-sm font-medium text-gray-500 flex items-center mt-1">
                  <Zap size={14} className="mr-1 text-yellow-500" /> 
                  Modifiez les lignes ci-dessous, la suivante s'ajoute toute seule !
                </p>
              </div>
            </div>

            {/* Table Header */}
            <div className="grid grid-cols-12 gap-3 pb-3 border-b border-gray-100 text-xs font-bold text-gray-400 uppercase tracking-wider">
              <div className="col-span-5">Ingrédient</div>
              <div className="col-span-3">Quantité</div>
              <div className="col-span-3">Origine</div>
              <div className="col-span-1"></div>
            </div>

            {/* Table Rows */}
            <div className="space-y-1 mt-3">
              {lines.map((line, i) => (
                <div key={line.id} className="grid grid-cols-12 gap-3 items-center p-2 -mx-2 rounded-xl hover:bg-[#f2e9e4]/30 transition-colors group">
                  <div className="col-span-5">
                    <input 
                      type="text" 
                      list="ingredients-list"
                      value={line.ingredient} 
                      onChange={(e) => handleInput(i, 'ingredient', e.target.value)}
                      placeholder="Tapez un ingrédient..."
                      className="w-full bg-transparent border-b-2 border-transparent hover:border-gray-200 focus:border-[#341100] outline-none py-1.5 text-black font-bold placeholder-gray-300 transition"
                    />
                  </div>
                  <div className="col-span-3 flex items-center gap-1">
                    <input 
                      type="number" 
                      min="0" step="0.1"
                      value={line.qty} 
                      onChange={(e) => handleInput(i, 'qty', e.target.value)}
                      placeholder="0"
                      className="w-full bg-transparent border-b-2 border-transparent hover:border-gray-200 focus:border-[#341100] outline-none py-1.5 text-black font-bold text-right transition"
                    />
                    <select 
                      value={line.unit}
                      onChange={(e) => handleInput(i, 'unit', e.target.value)}
                      className="bg-transparent border-b-2 border-transparent hover:border-gray-200 focus:border-[#341100] outline-none py-1.5 text-gray-500 font-medium cursor-pointer transition appearance-none"
                    >
                      <option value="kg">kg</option>
                      <option value="g">g</option>
                    </select>
                  </div>
                  <div className="col-span-3">
                    <input 
                      type="text" 
                      list="origins-list"
                      value={line.origin}
                      onChange={(e) => handleInput(i, 'origin', e.target.value)}
                      placeholder="Auto"
                      className="w-full bg-transparent border-b-2 border-transparent hover:border-gray-200 focus:border-[#341100] outline-none py-1.5 text-gray-500 font-medium transition"
                    />
                  </div>
                  <div className="col-span-1 flex justify-end">
                    {lines.length > 1 && (
                      <button 
                        onClick={() => removeLine(line.id)}
                        className="text-gray-300 hover:text-red-500 p-1.5 opacity-0 group-hover:opacity-100 transition-opacity rounded-md hover:bg-red-50"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-8 flex justify-end">
              <button className="text-[#341100] font-bold text-sm flex items-center hover:underline">
                <Sparkles size={16} className="mr-1" />
                Essayer l'outil
              </button>
            </div>
          </div>

          {/* RIGHT: REAL TIME RESULTS */}
          <div className="lg:w-80 bg-[#f2e9e4]/40 p-8 lg:p-10 flex flex-col justify-center items-center text-center">
            
            <h3 className="text-sm font-bold text-[#341100] uppercase tracking-wider mb-8">Résultat en direct</h3>
            
            {ecoGrade === 'unknown' ? (
              <div className="space-y-6">
                <div className="w-32 h-32 mx-auto rounded-xl bg-white border-2 border-dashed border-[#e0d6d0] flex items-center justify-center">
                  <span className="text-4xl text-[#e0d6d0] font-bold">?</span>
                </div>
                <p className="text-gray-500 font-medium text-sm">Ajoutez des ingrédients pour voir l'impact.</p>
              </div>
            ) : (
              <div className="space-y-10 animate-in fade-in zoom-in-95 duration-300 w-full">
                
                {/* GREEN SCORE */}
                <div className="flex flex-col items-center">
                  <img 
                    src={`https://static.openfoodfacts.org/images/attributes/dist/green-score-${ecoGrade}.svg`} 
                    alt={`Green-Score ${ecoGrade.toUpperCase()}`} 
                    className="h-28 transition-all duration-300 transform hover:scale-105" 
                  />
                  <div className="mt-4 bg-white px-4 py-2 rounded-xl shadow-sm border border-gray-100 w-full">
                    <p className="text-xl font-extrabold text-[#341100]">{scorePerKg.toFixed(2)} <span className="text-xs font-semibold text-gray-500">kg CO₂e/kg</span></p>
                    <p className="text-xs font-bold text-gray-400 mt-1">Total : ({totalCO2.toFixed(2)} kg CO₂e)</p>
                  </div>
                </div>

                {/* NUTRI SCORE */}
                <div className="flex flex-col items-center">
                  <img 
                    src={`https://static.openfoodfacts.org/images/attributes/dist/nutriscore-${nutriGrade}-new-fr.svg`} 
                    alt={`Nutri-Score ${nutriGrade.toUpperCase()}`} 
                    className="h-16 transition-all duration-300" 
                  />
                </div>

              </div>
            )}
            
            <button className="mt-12 w-full bg-[#341100] text-white py-4 rounded-xl font-bold shadow-lg hover:bg-black transition flex items-center justify-center">
              Sauvegarder ma recette <ArrowRight size={18} className="ml-2" />
            </button>
          </div>

        </div>
      </section>

      {/* VALUE PROPOSITION SECTION */}
      <section className="bg-white border-t border-gray-200 py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-extrabold text-black mb-4">La boussole des professionnels</h2>
            <p className="text-gray-500 font-medium text-lg">Améliorez facilement vos fiches techniques avec des données fiables.</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto bg-[#f2e9e4] text-[#341100] rounded-2xl flex items-center justify-center mb-6">
                <Activity size={32} />
              </div>
              <h3 className="text-xl font-bold text-black mb-3">Calcul en temps réel</h3>
              <p className="text-gray-500 font-medium leading-relaxed">Ajustez facilement l'impact d'une recette en "jammant" sur les quantités ou en testant des substitutions d'ingrédients à la volée.</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 mx-auto bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mb-6">
                <Database size={32} />
              </div>
              <h3 className="text-xl font-bold text-black mb-3">Transparence & Agribalyse</h3>
              <p className="text-gray-500 font-medium leading-relaxed">Une méthodologie de calcul transparente, qui s'appuie sur la rigueur de la base publique Agribalyse portée par l'ADEME.</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 mx-auto bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mb-6">
                <Award size={32} />
              </div>
              <h3 className="text-xl font-bold text-black mb-3">Score à forte notoriété</h3>
              <p className="text-gray-500 font-medium leading-relaxed">Misez sur un indicateur validé et déjà identifié par des millions de consommateurs sur Open Food Facts et Yuka.</p>
            </div>
          </div>

          {/* ACCORDION : FEATURES IN DISCUSSION */}
          <div className="mt-20">
            <button 
              onClick={() => setIsFeaturesOpen(!isFeaturesOpen)}
              className="flex items-center justify-between w-full p-6 bg-[#faf9f8] hover:bg-[#f2e9e4]/40 border border-gray-200 rounded-2xl transition-all duration-300"
            >
              <div className="flex items-center gap-3">
                <Sparkles size={24} className="text-[#341100]" />
                <span className="font-extrabold text-xl text-black">Fonctionnalités avancées (En discussion)</span>
              </div>
              {isFeaturesOpen ? <ChevronUp size={24} className="text-gray-400" /> : <ChevronDown size={24} className="text-gray-400" />}
            </button>

            {isFeaturesOpen && (
              <div className="grid md:grid-cols-3 gap-6 mt-6 animate-in slide-in-from-top-4 fade-in duration-300">
                <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                  <div className="flex items-center gap-3 mb-3">
                    <Zap size={20} className="text-[#341100]" />
                    <h4 className="font-bold text-black">Saisie Zéro Friction</h4>
                  </div>
                  <p className="text-sm text-gray-500 font-medium leading-relaxed">Fini les formulaires complexes. Notre interface s'adapte à vous : saisie magique, import massif de fichiers Excel, et même scan de photos via l'IA.</p>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                  <div className="flex items-center gap-3 mb-3">
                    <Target size={20} className="text-[#341100]" />
                    <h4 className="font-bold text-black">Pilotage EGalim & Climat</h4>
                  </div>
                  <p className="text-sm text-gray-500 font-medium leading-relaxed">Suivez vos objectifs réglementaires (Bio, Durable) en un coup d'œil, et assurez-vous de rester sous les limites planétaires (2t de CO2 par an).</p>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                  <div className="flex items-center gap-3 mb-3">
                    <BookOpen size={20} className="text-[#341100]" />
                    <h4 className="font-bold text-black">Pédagogie Actionnable</h4>
                  </div>
                  <p className="text-sm text-gray-500 font-medium leading-relaxed">Ne soyez plus seul face aux chiffres. Notre coach suggère des substitutions intelligentes pour améliorer vos scores sans exploser vos coûts matières.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-[#341100] text-white py-12 px-6 text-center">
        <div className="max-w-4xl mx-auto flex flex-col items-center">
          <img src="https://static.openfoodfacts.org/images/logos/off-logo-horizontal-light.svg" alt="Open Food Facts" className="h-10 opacity-50 mb-6 grayscale" />
          <p className="text-[#f2e9e4]/70 font-medium mb-3">Un projet open-source porté par Open Food Facts, conçu pour transformer l'impact de la restauration.</p>
          <div className="inline-flex items-center text-[#f2e9e4] text-sm font-semibold bg-white/10 px-4 py-2 rounded-full mb-6">
            <Leaf size={14} className="mr-2 text-emerald-400" />
            Projet réalisé de manière collaborative grâce au soutien de l'Appel à Communs de l'ADEME
          </div>
          <a href="#" className="text-white font-bold hover:underline">Découvrir le projet sur GitHub</a>
        </div>
      </footer>

    </div>
  );
}
