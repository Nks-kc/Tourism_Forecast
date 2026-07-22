import { test, expect } from '@playwright/test';
import { registerAndLogin } from './helpers.js';

test('switching the country updates the displayed name', async ({ page, request }) => {
    await registerAndLogin(page, request);

    await page.getByRole('button', { name: 'Countries' }).click();

    const select = page.locator('#country-select');
    await expect(select).toBeVisible();

    await select.selectOption({ index: 1 });
    const selectedValue = await select.inputValue();
    const expectedDisplayName = selectedValue.replace(/_/g, ' ');

    await expect(page.locator('.ce-flag-name .panel-title')).toHaveText(expectedDisplayName);
});