import { test, expect } from '@playwright/test';

test('theme toggle persists after page reload', async ({ page }) => {
    await page.goto('http://localhost:5173');

    // Default theme is dark, so the toggle's accessible name offers switching to light
    await page.getByRole('button', { name: 'Switch to light mode' }).click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');

    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
});