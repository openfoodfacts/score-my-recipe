import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for the Score My Recipe e2e suite.
 *
 * Two webServer entries launch the servers with independent readiness checks,
 * so tests start only after BOTH are ready:
 *   - the test backend (real FastAPI, OFF mocked) on port 8800
 *     → http://localhost:8800/v1/health
 *   - the frontend dev server (vite) on port 5174
 *     → http://localhost:5174
 *
 * Array entries start sequentially in order, so the backend is ready before the
 * frontend dev server is even launched.
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
	webServer: [
		{
			command: 'bash start-backend.sh',
			url: 'http://localhost:8800/v1/health',
			name: 'Backend',
			reuseExistingServer: false,
			timeout: 60_000
		},
		{
			command: 'bash start-frontend.sh',
			url: 'http://localhost:5174',
			name: 'Frontend',
			reuseExistingServer: false,
			timeout: 60_000
		}
	]
});
