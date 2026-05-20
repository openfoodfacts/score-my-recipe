import { sentrySvelteKit } from '@sentry/sveltekit';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { version as packageVersion } from './package.json';
import { viteStaticCopy } from 'vite-plugin-static-copy';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
	server: {
	},
	plugins: [
		tailwindcss(),
		sentrySvelteKit({
			sourceMapsUploadOptions: {
				org: 'openfoodfacts',
				project: 'score-my-recipe-frontend'
			}
		}),
		sveltekit(),
		viteStaticCopy({
			targets: [
			]
		})
	],
	define: {
		'import.meta.env.PACKAGE_VERSION': JSON.stringify(packageVersion)
	}
});
