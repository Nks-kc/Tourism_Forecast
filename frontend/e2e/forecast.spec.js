import { test, expect } from '@playwright/test';
import { registerAndLogin } from './helpers.js';

test('user can log in and generate a forecast', async ({ page, request }) => {
    await registerAndLogin(page, request);

    await page.getByRole('button', { name: '6 mo' }).click();
    await page.getByRole('button', { name: 'Generate Forecast' }).click();

    const forecastSection = page.locator('section').filter({ hasText: 'Model forecast comparison' });
    await expect(forecastSection.locator('canvas')).toBeVisible({ timeout: 15000 });
});