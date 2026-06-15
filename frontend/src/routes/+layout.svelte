<script lang="ts">

	import '../app.css';
	import '@fontsource-variable/plus-jakarta-sans';
	import type { LayoutProps } from './$types';
	import Navbar from '$lib/ui/Navbar.svelte';
	import Footer from '$lib/ui/Footer.svelte';
	import { navigating } from '$app/state';

	import { _ } from '$lib/i18n';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<title>Open Food Facts for recipes</title>
	<meta name="description" content="Open Food Facts for recipes" />
	<meta name="viewport" content="width=device-width, initial-scale=1" />
</svelte:head>

<!-- progress bar when navigating between pages -->
{#if navigating.to != null}
	<progress class="progress progress-secondary fixed top-0 left-0 z-50 h-1 w-full rounded-none"
	></progress>
{/if}

<div class="min-h-screen bg-base-100 text-base-content font-sans">

	<Navbar />
	<div class="w-full">
		{@render children?.()}
	</div>

</div>

<Footer />
