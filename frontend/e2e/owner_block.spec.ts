import { test, expect } from '@playwright/test';

const OWNER_EMAIL = process.env.E2E_OWNER_EMAIL ?? 'owner@turf.in';
const OWNER_PASSWORD = process.env.E2E_OWNER_PASSWORD ?? 'password123';

test.describe('Owner slot blocking', () => {
  test('owner signs in and reaches the calendar', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill(OWNER_EMAIL);
    await page.getByLabel('Password').fill(OWNER_PASSWORD);
    await page.getByRole('button', { name: /sign in/i }).click();

    await page.goto('/owner/calendar');
    await expect(page.getByRole('heading', { name: /calendar/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /generate 14 days/i })).toBeVisible();
  });
});
