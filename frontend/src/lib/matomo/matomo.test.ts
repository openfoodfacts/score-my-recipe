import { describe, it, expect } from 'vitest';
import { get } from 'svelte/store';
import { tracker, type Tracker } from './tracker';
import { MATOMO_HOST, MATOMO_SITE_ID, MATOMO_URL } from '$lib/const';

describe('matomo tracker', () => {
	it('defaults to empty/disabled constants when env vars are not set', () => {
		expect(MATOMO_URL).toBe('');
		expect(MATOMO_HOST).toBe('');
		expect(MATOMO_SITE_ID).toBe(0);
	});

	it('initializes with undefined and allows setting a tracker', () => {
		expect(get(tracker)).toBeUndefined();

		const mockTracker = {
			trackPageView: () => {},
			trackEvent: () => {},
			setCustomUrl: () => {}
		} as unknown as Tracker;

		tracker.set(mockTracker);
		expect(get(tracker)).toBe(mockTracker);

		tracker.set(undefined);
		expect(get(tracker)).toBeUndefined();
	});
});
