<!--
SPDX-FileCopyrightText:  Andreas Nüßlein <andreas@nuessle.in>
SPDX-FileCopyrightText:  Mikkel Eide Eriksen <mikkel.eriksen@gmail.com>
SPDX-FileCopyrightText:  VaiTon <eyadlorenzo@gmail.com>

SPDX-License-Identifier: AGPL-3.0-or-later

Initially taken from https://github.com/sinnwerkstatt/sveltekit-matomo
-->

<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { get } from 'svelte/store';

	import { dev } from '$app/environment';
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/state';
	import { env } from '$env/dynamic/public';

	import { tracker, type Tracker } from './tracker';

	interface Props {
		url?: string;
		siteId?: number;
		enabled?: boolean;
		disableCookies?: boolean;
		requireConsent?: boolean;
		doNotTrack?: boolean;
		enableCrossDomainLinking?: boolean;
		domains?: string[];
		heartBeat?: number | null;
		linkTracking?: boolean | null;
		onTrackerReady?: (tracker: Tracker) => void;
		onError?: (error: Error) => void;
	}

	let {
		url = '',
		siteId = 0,
		enabled = !dev || env.PUBLIC_MATOMO_ENABLE_DEV === 'true',
		disableCookies = false,
		requireConsent = false,
		doNotTrack = false,
		enableCrossDomainLinking = false,
		domains = [],
		heartBeat = 15,
		linkTracking = null,
		onTrackerReady,
		onError
	}: Props = $props();

	let scriptElement = $state<HTMLScriptElement | null>(null);
	let scriptLoadError = $state(false);
	let isInitialized = false;

	const cleanUrl = $derived(url ? url.replace(/\/+$/, '') : '');
	const isConfigured = $derived(Boolean(enabled && cleanUrl && siteId && siteId > 0));

	function isMatomoLoaded(): boolean {
		return typeof window !== 'undefined' && 'Matomo' in window && window.Matomo !== undefined;
	}

	function initializeMatomo() {
		if (isInitialized || !isConfigured || !isMatomoLoaded()) {
			return;
		}

		try {
			const matomo = window.Matomo;
			if (!matomo) return;

			const track = matomo.getTracker(`${cleanUrl}/matomo.php`, siteId);
			if (!track) return;

			if (disableCookies) track.disableCookies();
			if (requireConsent) track.requireConsent();
			if (doNotTrack) track.setDoNotTrack(true);
			if (heartBeat) track.enableHeartBeatTimer(heartBeat);
			if (enableCrossDomainLinking) track.enableCrossDomainLinking();
			if (domains.length) track.setDomains(domains);
			if (linkTracking !== null) track.enableLinkTracking(linkTracking);

			tracker.set(track);

			// Allow custom initialization before first page view
			if (onTrackerReady) {
				onTrackerReady(track);
			}

			track.setCustomUrl(page.url.href);
			track.trackPageView();
			isInitialized = true;
		} catch (error) {
			const err = error instanceof Error ? error : new Error(String(error));
			if (onError) {
				onError(err);
			} else {
				console.error('Matomo initialization error:', err);
			}
		}
	}

	function handleScriptLoad() {
		initializeMatomo();
	}

	function handleScriptError() {
		scriptLoadError = true;
		const error = new Error('Failed to load Matomo script');
		if (onError) {
			onError(error);
		} else {
			console.error(error);
		}
	}

	onMount(() => {
		if (!isConfigured || scriptLoadError) return;

		// Check if Matomo is already loaded (e.g., from cache or loaded before onMount)
		if (isMatomoLoaded()) {
			initializeMatomo();
			return;
		}

		if (scriptElement) {
			scriptElement.addEventListener('load', handleScriptLoad);
			scriptElement.addEventListener('error', handleScriptError);
		}
	});

	onDestroy(() => {
		if (scriptElement) {
			scriptElement.removeEventListener('load', handleScriptLoad);
			scriptElement.removeEventListener('error', handleScriptError);
			scriptElement = null;
		}
		tracker.set(undefined);
		isInitialized = false;
	});

	afterNavigate(async ({ from, to }) => {
		if (!isConfigured) return;

		// Initial navigation is handled by initializeMatomo()
		if (!from) return;

		const currentTracker = get(tracker);
		if (!currentTracker) return;

		if (to?.url.href) {
			try {
				currentTracker.setCustomUrl(to.url.href);
				currentTracker.trackPageView();
			} catch (error) {
				const err = error instanceof Error ? error : new Error(String(error));
				if (onError) {
					onError(err);
				} else {
					console.error('Matomo navigation tracking error:', err);
				}
			}
		}
	});
</script>

<svelte:head>
	{#if isConfigured}
		<script
			async
			defer
			src={`${cleanUrl}/matomo.js`}
			onload={handleScriptLoad}
			onerror={handleScriptError}
			bind:this={scriptElement}
		></script>
	{/if}
</svelte:head>
