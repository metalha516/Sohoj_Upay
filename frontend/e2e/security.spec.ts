import { test, expect } from "@playwright/test";

test.describe("Security & Route Protection E2E", () => {
  test("unauthenticated access to protected routes redirects to /login", async ({ page }) => {
    // Attempt visiting protected routes directly with empty cookies
    const protectedRoutes = [
      "/dashboard",
      "/behavior",
      "/coach",
      "/transactions",
      "/goals",
      "/simulator",
      "/settings",
    ];

    for (const route of protectedRoutes) {
      await page.goto(route);
      await page.waitForURL(/\/login\?redirect=/);
      expect(page.url()).toContain(`/login?redirect=${encodeURIComponent(route)}`);
    }
  });

  test("logout clears authentication session and revokes access", async ({ page }) => {
    // 1. Log in as seed persona
    await page.goto("/login");
    await page.fill('input[type="email"]', "sumaiya.talukder.26dafe@example.com");
    await page.fill('input[type="password"]', "SecurePassword123!");
    await page.click('button[type="submit"]');

    await page.waitForURL("/dashboard");
    await expect(page.locator("text=Net Balance")).toBeVisible();

    // 2. Click log out button in header
    await page.click('button[aria-label="Log Out"]');

    // 3. Verify redirected to login
    await page.waitForURL("/login");

    // 4. Try navigating back to /dashboard
    await page.goto("/dashboard");
    await page.waitForURL(/\/login/);
    expect(page.url()).toContain("/login");
  });

  test("XSS payload in transaction merchant and description renders inert", async ({ page }) => {
    page.on("dialog", (dialog) => {
      throw new Error(`XSS dialog triggered: ${dialog.message()}`);
    });

    // 1. Log in
    await page.goto("/login");
    await page.fill('input[type="email"]', "sumaiya.talukder.26dafe@example.com");
    await page.fill('input[type="password"]', "SecurePassword123!");
    await page.click('button[type="submit"]');
    await page.waitForURL("/dashboard");

    // Set flag in window to detect if script executes
    await page.evaluate(() => {
      (window as any).__xss_executed = false;
    });

    // 2. Open Cash-Out Modal
    await page.click("text=Record Cash-Out");
    await page.waitForSelector("#cashout-amount");

    // 3. Fill with XSS payload
    const xssPayload = '<img src=x onerror="window.__xss_executed=true"><script>window.__xss_executed=true</script>';
    await page.fill("#cashout-amount", "1200");
    await page.click('button:has-text("Necessity")');
    await page.fill("#cashout-desc", xssPayload);

    // 4. Submit
    await page.click('button[type="submit"]:has-text("Record Cash-Out")');
    await expect(page.locator("text=Record MFS Cash-Out")).not.toBeVisible({ timeout: 10000 });

    // 5. Navigate to transactions
    await page.goto("/transactions");
    await page.waitForSelector("table");

    // 6. Verify XSS was not executed (window.__xss_executed is not true)
    const xssTriggered = await page.evaluate(() => (window as any).__xss_executed === true);
    expect(xssTriggered).toBe(false);

    // 7. Verify text rendered inert in DOM
    const cellText = await page.locator("table").innerText();
    expect(cellText).toContain("<img src=x");
  });
});
