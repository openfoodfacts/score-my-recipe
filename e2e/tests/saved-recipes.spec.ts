import { test, expect, type Page } from '@playwright/test';

/**
 * Recipe text exercised by the integration backend fixture.
 * Keep in sync with server/tests/data/capture_parse_text.py.
 */
const RECIPE_TEXT = `1 pâte brisée (150g)
4 pommes bio
50g de sucre
30g de beurre origine France`;

/** Title used for the saved recipe in this test. */
const RECIPE_TITLE = 'E2E Apple Pie';

/** Optional description used to verify metadata persistence. */
const RECIPE_DESCRIPTION = 'A simple apple pie saved by the e2e test.';

/** Manually versioned title used by the "Save as new" flow. */
const RECIPE_COPY_TITLE = `${RECIPE_TITLE} - v2`;

/**
 * Open /score through the /add form so the score page has a real parsed recipe.
 * The score auto-computes after the 3s inactivity timer; wait for its logo.
 */
async function scoreRecipe(page: Page, title: string, description: string) {
	await page.goto('/');
	await page.waitForLoadState('networkidle');

	await page.getByRole('link', { name: 'Score a recipe' }).click();
	await expect(page).toHaveURL(/\/add$/);

	await page.locator('#recipe-title').fill(title);
	await page.locator('#recipe-description').fill(description);
	await page.locator('#recipe-text').fill(RECIPE_TEXT);
	await page.getByRole('button', { name: 'Score recipe' }).click();

	await expect(page).toHaveURL(/\/score$/);
	await expect(page.locator('img.h-32')).toBeVisible({ timeout: 15_000 });
}

/** Open the save dialog and return it. */
async function openSaveDialog(page: Page) {
	await page.getByRole('button', { name: 'Save recipe' }).click();
	const dialog = page.getByRole('dialog');
	await expect(dialog).toBeVisible();
	return dialog;
}

test.describe('Saved recipes', () => {
	// Saving computes a fresh score before writing to localStorage, and the
	// test also opens/reopens recipes, so give it generous headroom.
	test.setTimeout(90_000);

	test('save, list, reopen, save as new and delete recipes', async ({ page }) => {
		// 1. Score a recipe.
		await scoreRecipe(page, RECIPE_TITLE, RECIPE_DESCRIPTION);

		// 2. Save it. The dialog opens every time and prefills the editor title.
		const saveDialog = await openSaveDialog(page);
		await expect(page.locator('#save-recipe-title')).toHaveValue(RECIPE_TITLE);
		await saveDialog.getByRole('button', { name: 'Save', exact: true }).click();

		// 3. The save writes the recipe, updates the URL and shows a toast.
		await expect(page).toHaveURL(/\/score\?recipe=/, { timeout: 15_000 });
		await expect(page.getByText('Recipe saved.', { exact: true })).toBeVisible();

		// 4. The navbar now exposes My Recipes, including on mobile.
		const myRecipesLink = page.getByRole('link', { name: 'My recipes' });
		await expect(myRecipesLink).toBeVisible();
		await page.setViewportSize({ width: 375, height: 812 });
		await expect(myRecipesLink).toBeVisible();
		await page.setViewportSize({ width: 1280, height: 720 });

		// 5. The list shows the recipe with its stored score badge.
		await myRecipesLink.click();
		await expect(page).toHaveURL(/\/my-recipes$/);
		await expect(page.getByRole('heading', { name: RECIPE_TITLE })).toBeVisible();
		await expect(page.getByText(RECIPE_DESCRIPTION, { exact: true })).toBeVisible();
		await expect(page.getByText('4 ingredient(s)', { exact: true })).toBeVisible();
		const firstCard = page.locator('a').filter({ hasText: RECIPE_TITLE }).first();
		await expect(firstCard.locator('img')).toHaveAttribute('alt', /^(A\+|[A-F])$/);

		// 6. Opening the card restores the saved recipe in the score view.
		await page.getByRole('heading', { name: RECIPE_TITLE }).click();
		await expect(page).toHaveURL(/\/score\?recipe=/);
		await expect(page.locator('#recipe-title')).toHaveValue(RECIPE_TITLE);
		await expect(page.locator('#recipe-description')).toHaveValue(RECIPE_DESCRIPTION);

		// 7. Save as new is offered only after the title changes. Edit the
		//    title in the dialog, then create a copy.
		const copyDialog = await openSaveDialog(page);
		await expect(copyDialog.getByRole('button', { name: 'Save as new' })).toHaveCount(0);
		await page.locator('#save-recipe-title').fill(RECIPE_COPY_TITLE);
		await expect(copyDialog.getByRole('button', { name: 'Save as new' })).toBeVisible();
		await expect(copyDialog.getByText('Creates another recipe with this title.')).toBeVisible();
		await copyDialog.getByRole('button', { name: 'Save as new' }).click();
		await expect(page.getByText('Saved as a new recipe.', { exact: true })).toBeVisible({
			timeout: 15_000
		});
		await expect(page.locator('#recipe-title')).toHaveValue(RECIPE_COPY_TITLE);
		await expect(page).toHaveURL(/\/score\?recipe=/);

		// 8. Both recipes are listed.
		await myRecipesLink.click();
		await expect(page.getByRole('heading', { name: RECIPE_TITLE, exact: true })).toBeVisible();
		await expect(page.getByRole('heading', { name: RECIPE_COPY_TITLE, exact: true })).toBeVisible();

		// 9. The sort control orders by title or by last update.
		await page.locator('#recipe-sort').selectOption('title');
		await expect(page.getByRole('heading', { level: 2 }).first()).toHaveText(RECIPE_TITLE);
		await page.locator('#recipe-sort').selectOption('updated');
		await expect(page.getByRole('heading', { level: 2 }).first()).toHaveText(RECIPE_COPY_TITLE);

		// 10. The duplicate warning appears while typing an existing title.
		await page.getByRole('heading', { name: RECIPE_TITLE, exact: true }).click();
		const warningDialog = await openSaveDialog(page);
		await page.locator('#save-recipe-title').fill(RECIPE_COPY_TITLE);
		await expect(
			warningDialog.getByText('A saved recipe already uses this title.', { exact: true })
		).toBeVisible();
		await expect(warningDialog.getByRole('button', { name: 'Save as new' })).toBeVisible();
		await warningDialog.getByRole('button', { name: 'Cancel' }).click();

		// 11. A never-saved recipe still warns when its title already exists,
		//     but does not offer Save as new.
		await page.goto('/score');
		await page.waitForLoadState('networkidle');
		await page.locator('#recipe-title').fill(RECIPE_TITLE);
		const newDraftDialog = await openSaveDialog(page);
		await expect(
			newDraftDialog.getByText('A saved recipe already uses this title.', { exact: true })
		).toBeVisible();
		await expect(newDraftDialog.getByRole('button', { name: 'Save as new' })).toHaveCount(0);
		await newDraftDialog.getByRole('button', { name: 'Cancel' }).click();

		// 12. Delete the copy, then the original; the empty state remains and
		//     the navbar link disappears with the last recipe.
		await myRecipesLink.click();
		await page.getByRole('button', { name: `Delete recipe: ${RECIPE_COPY_TITLE}` }).click();
		const deleteDialog = page.getByRole('dialog');
		await expect(deleteDialog.getByText(RECIPE_COPY_TITLE, { exact: true })).toBeVisible();
		await deleteDialog.getByRole('button', { name: 'Delete', exact: true }).click();
		await expect(page.getByRole('heading', { name: RECIPE_COPY_TITLE, exact: true })).toHaveCount(
			0
		);

		await page.getByRole('button', { name: `Delete recipe: ${RECIPE_TITLE}` }).click();
		await page.getByRole('dialog').getByRole('button', { name: 'Delete', exact: true }).click();
		await expect(page.getByRole('heading', { name: 'No saved recipes yet' })).toBeVisible();
		await expect(page.getByRole('link', { name: 'My recipes' })).toHaveCount(0);
	});
});
