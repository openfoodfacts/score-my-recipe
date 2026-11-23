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
 * The pasted spreadsheet exercised by the CSV scenario.
 *
 * The rows match the recorded `parse_csv_recipe.json` fixture, and the
 * label/origin columns carry the same metadata as the text recipe so the
 * pinned green-score grade stays valid.
 */
const SPREADSHEET_TEXT = `Ingrédient\tQuantité\tUnité\tOrigine\tLabels
Pâte brisée\t1\tpièce\t\t
Pommes\t4\tpièce\t\tBio
Sucre\t50\tg\t\t
Beurre\t30\tg\tFrance\t`;

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

	test('user pastes a spreadsheet, sees the detection preview and scores it', async ({ page }) => {
		// 1. Switch the UI to French, like the text scenario.
		await page.goto('/');
		await page.waitForLoadState('networkidle');
		await page.locator('.locale-selector select').selectOption('fr-FR');

		// 2. Open /add and select the spreadsheet tab.
		await page.getByRole('link', { name: 'Notez une recette' }).click();
		await expect(page).toHaveURL(/\/add$/);
		await page.getByRole('tab', { name: 'Tableur' }).click();

		// 3. Paste the table and parse it.
		await page.locator('#spreadsheet-text').fill(SPREADSHEET_TEXT);
		await page.getByRole('button', { name: 'Analyser le tableau' }).click();

		// 4. The detection report and preview are shown before scoring.
		await expect(page.getByRole('heading', { name: 'Tableau détecté' })).toBeVisible();

		// The separator and column detection details start collapsed:
		// they are only revealed by the "see details" summary.
		const columnsHeading = page.getByRole('heading', { name: 'Colonnes' });
		const showDetails = page.getByText('Voir les détails de la détection du tableau');
		const hideDetails = page.getByText('Masquer les détails de la détection du tableau');
		await expect(showDetails).toBeVisible();
		await expect(page.getByText('Tabulation')).toBeHidden();
		await expect(columnsHeading).toBeHidden();

		// 5. Unfold the details: the summary label flips and both sections appear.
		await showDetails.click();
		await expect(hideDetails).toBeVisible();
		await expect(page.getByText('Tabulation')).toBeVisible();
		await expect(columnsHeading).toBeVisible();

		// 6. The ingredient preview stays visible regardless of the fold state.
		await expect(page.getByRole('heading', { name: 'Ingrédients à noter' })).toBeVisible();
		// The item unit is labelled with the ingredient name, so scope the
		// first match to the ingredient-name column.
		await expect(
			page.getByRole('cell', { name: 'pâte brisée', exact: true }).first()
		).toBeVisible();
		await expect(page.getByRole('cell', { name: 'Bio', exact: true }).first()).toBeVisible();
		await expect(page.getByRole('cell', { name: 'France', exact: true }).first()).toBeVisible();

		// 7. Continue to the score editor and verify the pinned grade.
		await page.getByRole('button', { name: 'Continuer vers la notation' }).click();
		await expect(page).toHaveURL(/\/score$/);

		const scoreLogo = page.locator('img.h-32');
		await expect(scoreLogo).toBeVisible({ timeout: 15_000 });
		const letterGrade = await scoreLogo.getAttribute('alt');
		expect(letterGrade).toMatch(/^(A\+|[A-F])$/);
		expect(letterGrade).toBe(EXPECTED_LETTER_GRADE);
	});
});
