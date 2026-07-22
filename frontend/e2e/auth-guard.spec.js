import { test, expect } from '@playwright/test';

test('logged-out visitor sees the login page, not the dashboard', async ({ page }) => {
    await page.goto('http://localhost:5173');

    await expect(page.locator('.login-submit')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Dashboard', exact: true })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Countries', exact: true })).toHaveCount(0);
});
