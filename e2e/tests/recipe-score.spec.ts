import { test, expect } from '@playwright/test';

/**
 * The exact recipe text exercised by this test.
 * Keep in sync with server/tests/data/capture_parse_text.py.
 */
const RECIPE_TEXT = `1 pâte brisée (150g)
4 pommes bio
50g de sucre
30g de beurre origine France`;

/** Optional recipe metadata entered on the add view. */
const RECIPE_TITLE = 'Tarte aux pommes';
const RECIPE_DESCRIPTION = 'Une tarte aux pommes simple pour tester le titre et la description.';

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
		// Keep the fixture-based flow independent of third-party assets and telemetry.
		await page.route('**/*', async (route) => {
			const { hostname } = new URL(route.request().url());
			if (hostname === 'localhost' || hostname === '127.0.0.1') {
				await route.continue();
			} else {
				await route.abort();
			}
		});

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

		// 4. Fill the optional recipe metadata and the recipe text.
		await page.locator('#recipe-title').fill(RECIPE_TITLE);
		await page.locator('#recipe-description').fill(RECIPE_DESCRIPTION);
		await page.locator('#recipe-text').fill(RECIPE_TEXT);

		// 5. Submit the recipe (button label is French after the locale switch).
		await page.getByRole('button', { name: 'Noter la recette' }).click();

		// 6. Verify navigation to /score (client-side goto with ingredient state).
		await expect(page).toHaveURL(/\/score$/);

		// 7. Verify the recipe metadata carried over and drives the tab title.
		await expect(page).toHaveTitle(RECIPE_TITLE);
		await expect(page.locator('#recipe-title')).toHaveValue(RECIPE_TITLE);
		await expect(page.locator('#recipe-description')).toHaveValue(RECIPE_DESCRIPTION);

		// 8. Wait for the green-score logo to render.
		//    The GreenScore component renders an <img> whose alt attribute is the
		//    letter grade.  The score auto-computes after a 3s inactivity timer,
		//    so allow extra time for that plus the API round-trip.
		const scoreLogo = page.locator('img.h-32');
		await expect(scoreLogo).toBeVisible({ timeout: 15_000 });

		// 9. Assert a valid letter grade is shown and matches the pinned value.
		const letterGrade = await scoreLogo.getAttribute('alt');
		expect(letterGrade).toMatch(/^(A\+|[A-F])$/);
		expect(letterGrade).toBe(EXPECTED_LETTER_GRADE);

		// A free-text certification is retained, but the score does not use it.
		const labels = page.locator('label[for^="ingredient-labels-"]').first().locator('..');
		const unsupportedLabel = 'Certification inventée';
		await labels.locator('input').fill(unsupportedLabel);
		await labels.locator('input').press('Enter');
		// The warning lives in a tooltip on a sign next to the labels label:
		// its screen-reader text carries the note message.
		const warning = page.locator('span.sr-only', {
			hasText: `Le label ${unsupportedLabel} n’a pas été pris en compte dans le Green-Score.`
		});
		await expect(warning).toBeAttached({ timeout: 15_000 });
		await labels.getByRole('button', { name: `Remove tag "${unsupportedLabel}"` }).click();
		await expect(warning).toHaveCount(0);

		// 9. Assert the numeric score is also displayed (format: "XX.X/100").
		await expect(page.getByText(/\d+\.\d+\/100/)).toBeVisible();

		// 11. Verify the metadata is still editable on the edit view and that the
		//     tab title follows the edited value.
		const editedTitle = `${RECIPE_TITLE} (éditée)`;
		await page.locator('#recipe-title').fill(editedTitle);
		await expect(page.locator('#recipe-title')).toHaveValue(editedTitle);
		await expect(page).toHaveTitle(editedTitle);
	});

	test('a delayed blur cannot save the next edit of a codified ingredient', async ({ page }) => {
		await page.route('**/*', (route) => {
			const { hostname } = new URL(route.request().url());
			return hostname === 'localhost' || hostname === '127.0.0.1'
				? route.continue()
				: route.abort();
		});
		await page.goto('/');
		await page.waitForLoadState('networkidle');
		await page.locator('.locale-selector select').selectOption('fr-FR');
		await page.getByRole('link', { name: 'Notez une recette' }).click();
		await page.locator('#recipe-text').fill(RECIPE_TEXT);
		await page.getByRole('button', { name: 'Noter la recette' }).click();
		await expect(page).toHaveURL(/\/score$/);
		await expect(page.locator('img.h-32')).toBeVisible({ timeout: 15_000 });

		// Keep the second edit inside the first one's blur delay without racing the test runner.
		const clockStart = new Date('2030-01-01T00:00:00Z');
		await page.clock.install({ time: clockStart });
		await page.clock.pauseAt(new Date(clockStart.getTime() + 1000));

		// The fixture's sugar row already uses grams, which remain valid when the tag changes.
		const ingredient = page.locator('[id^="ingredient-codified-"]').nth(2);
		const ingredientFieldId = await ingredient.evaluate((element) => element.id);
		const ingredientId = ingredientFieldId.slice('ingredient-codified-'.length);
		const missingWarning = page
			.locator(`label[for="${ingredientFieldId}"]`)
			.getByText('Non comptabilisé', { exact: true });
		const tag = ingredient.locator('span[title="Double-click to edit"]');

		async function selectIngredient(label: string) {
			await tag.dispatchEvent('dblclick');
			const input = ingredient.locator('input:focus');
			await input.fill(label);
			await page.clock.runFor(180); // the previous edit's deferred blur save would have fired
			await expect(input).toBeFocused({ timeout: 1000 });
			await page.clock.runFor(340); // finish the autocomplete debounce
			const suggestion = ingredient
				.locator('.dropdown-content button')
				.filter({ has: page.getByText(label, { exact: true }) })
				.first();
			// The tag widget commits a suggestion on mousedown, before input blur.
			await suggestion.dispatchEvent('mousedown', undefined, { timeout: 5000 });
			await page.clock.runFor(130); // finish the outgoing edit's fade
			await expect(tag).toHaveText(label);
		}

		async function recompute() {
			const response = page.waitForResponse(
				(res) => res.url().endsWith('/v1/green-score') && res.request().method() === 'POST'
			);
			await page.getByRole('button', { name: 'Calculer le score' }).dispatchEvent('click');
			const result = await response;
			expect(result.ok()).toBe(true);
			return result;
		}

		await selectIngredient('crème fraîche');
		const creamScore = await recompute();
		expect((await creamScore.json()).missingIngredientIds).toContain(ingredientId);
		await expect(missingWarning).toBeAttached();

		await selectIngredient('œuf');
		const eggScore = await recompute();
		expect((await eggScore.json()).missingIngredientIds).not.toContain(ingredientId);
		await expect(missingWarning).toHaveCount(0);
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
