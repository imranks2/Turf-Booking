import { test, expect } from '@playwright/test';

test.describe('Player booking discovery', () => {
  test('player can browse turfs and open a turf detail', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /find a turf/i })).toBeVisible();

    const firstCard = page.locator('a[href^="/turfs/"]').first();
    if ((await firstCard.count()) > 0) {
      await firstCard.click();
      await expect(page).toHaveURL(/\/turfs\//);
      await expect(page.getByText(/operating hours/i)).toBeVisible();
    }
  });

  test('unauthenticated user is prompted to sign in to book', async ({ page }) => {
    await page.goto('/');
    const firstCard = page.locator('a[href^="/turfs/"]').first();
    test.skip((await firstCard.count()) === 0, 'No turfs seeded');
    await firstCard.click();
    await expect(page.getByRole('button', { name: /sign in to book/i })).toBeVisible();
  });
});
