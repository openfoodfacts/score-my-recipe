<script lang="ts">
	import { onMount } from 'svelte';

	import '../app.css';
	import '@fontsource-variable/plus-jakarta-sans';
	import type { LayoutProps } from './$types';
	import Logo from '$lib/ui/Logo.svelte';
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

<!-- Header -->
<div>
	<div class="flex justify-center">
		<div class="bg-base-100 navbar flex max-w-7xl w-full px-10">
			<div class="navbar-start">
				<a href="/"> <Logo class="h-16" /> </a>
			</div>
			<div class="flex-none navbar-center">
				<Navbar />
			</div>
			<div class="navbar-end"></div>
		</div>
	</div>
</div>

<div class="w-full">
	{@render children?.()}
</div>

<Footer />
