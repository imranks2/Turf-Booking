import { test, expect } from '@playwright/test';

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? 'admin@turf.in';
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? 'password123';

test.describe('Admin owner approval', () => {
  test('admin can view users and toggle status', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill(ADMIN_EMAIL);
    await page.getByLabel('Password').fill(ADMIN_PASSWORD);
    await page.getByRole('button', { name: /sign in/i }).click();

    await page.goto('/admin/users');
    await expect(page.getByRole('heading', { name: /users/i })).toBeVisible();

    const approveButton = page.getByRole('button', { name: /approve/i }).first();
    if ((await approveButton.count()) > 0) {
      await approveButton.click();
      await expect(page.getByText(/active/i).first()).toBeVisible();
    }
  });
});
