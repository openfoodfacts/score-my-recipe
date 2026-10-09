import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for the Score My Recipe e2e suite.
 *
 * A single webServer (start-servers.sh) launches both:
 *   - the test backend (real FastAPI, OFF mocked) on port 8800
 *   - the frontend dev server (vite) on port 5174
 *
 * See the project root AGENTS.md → "Integration tests" for details.
 */
export default defineConfig({
	testDir: './tests',
	// Run tests in files in parallel (safe for a single-browser, single-test suite).
	fullyParallel: false,
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 1 : 0,
	workers: 1,
	reporter: process.env.CI ? 'github' : 'list',
	use: {
		baseURL: 'http://localhost:5174',
		trace: 'on-first-retry',
		screenshot: 'only-on-failure'
	},
	projects: [
		{
			name: 'chromium',
			use: { ...devices['Desktop Chrome'] }
		}
	],
	webServer: {
		command: 'bash start-servers.sh',
		url: 'http://localhost:5174',
		reuseExistingServer: false,
		timeout: 60_000
	}
});
