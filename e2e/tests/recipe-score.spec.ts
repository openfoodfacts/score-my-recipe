import { test, expect } from '@playwright/test';

/**
 * The exact recipe text exercised by this test.
 * Keep in sync with server/tests/data/capture_parse_text.py.
 */
const RECIPE_TEXT = `1 pâte brisée (150g)
4 pommes bio
50g de sucre
30g de beurre origine France`;

/**
 * Pinned expected letter grade.
 *
 * Captured against:
 *   - the recorded parse_text fixture (server/tests/data/parse_text_recipe.json)
 *   - the pinned OFF taxonomies (server/tests/data/taxonomies/)
 *   - the committed agribalyse.csv
 *
 * If this assertion fails after a fixture/taxonomy refresh, update the value
 * after verifying the new score is correct.
 */
const EXPECTED_LETTER_GRADE = 'A';

test.describe('Recipe green-score integration', () => {
	// The test switches locale, parses a recipe (async API), and waits for the
	// auto-computed score (3s timer) — give it generous headroom.
	test.setTimeout(60_000);

	test('user opens the page in French, parses a recipe and sees the green score', async ({
		page
	}) => {
		// 1. Open the home page (default locale is English).
		await page.goto('/');
		// Wait for SvelteKit hydration so the onchange handler is attached.
		await page.waitForLoadState('networkidle');

		// 2. Switch the UI to French via the navbar language selector.
		//    svelte-i18n loads the French messages asynchronously, so we wait
		//    for the navbar link text to switch to French before proceeding.
		await page.locator('.locale-selector select').selectOption('fr-FR');

		// 3. Navigate to /add by clicking the "Notez une recette" navbar link.
		await page.getByRole('link', { name: 'Notez une recette' }).click();
		await expect(page).toHaveURL(/\/add$/);

		// 4. Fill the recipe text.
		await page.locator('#recipe-text').fill(RECIPE_TEXT);

		// 5. Submit the recipe (button label is French after the locale switch).
		await page.getByRole('button', { name: 'Noter la recette' }).click();

		// 6. Verify navigation to /score (client-side goto with ingredient state).
		await expect(page).toHaveURL(/\/score$/);

		// 7. Wait for the green-score logo to render.
		//    The GreenScore component renders an <img> whose alt attribute is the
		//    letter grade.  The score auto-computes after a 3s inactivity timer,
		//    so allow extra time for that plus the API round-trip.
		const scoreLogo = page.locator('img.h-32');
		await expect(scoreLogo).toBeVisible({ timeout: 15_000 });

		// 8. Assert a valid letter grade is shown and matches the pinned value.
		const letterGrade = await scoreLogo.getAttribute('alt');
		expect(letterGrade).toMatch(/^(A\+|[A-F])$/);
		expect(letterGrade).toBe(EXPECTED_LETTER_GRADE);

		// 9. Assert the numeric score is also displayed (format: "XX.X/100").
		await expect(page.getByText(/\d+\.\d+\/100/)).toBeVisible();
	});
});
