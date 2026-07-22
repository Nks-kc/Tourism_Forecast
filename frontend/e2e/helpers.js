export async function registerAndLogin(page, request) {
    const username = `e2e_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
    const password = "secret123";

    await request.post("http://localhost:5000/auth/register", {
        data: { username, email: `${username}@example.com`, password },
    });

    await page.goto("http://localhost:5173");
    await page.getByLabel("Username").fill(username);
    await page.getByLabel("Password").fill(password);
    await page.locator(".login-submit").click();

    return username;
}