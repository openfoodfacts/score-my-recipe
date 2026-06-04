import { sentrySvelteKit } from '@sentry/sveltekit';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { version as packageVersion } from './package.json';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
	plugins: [
		sveltekit(), // must be first
		tailwindcss(),
		sentrySvelteKit({
			sourceMapsUploadOptions: {
				org: 'openfoodfacts',
				project: 'score-my-recipe-frontend'
			}
		}),
	],
	define: {
		'import.meta.env.PACKAGE_VERSION': JSON.stringify(packageVersion)
	},
	optimizeDeps: {
		exclude: ['@iconify-svelte/simple-icons', '@iconify-svelte/material-symbols', '@iconify-svelte/mdi', ''],
	}
});
