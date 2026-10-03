import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Accessibility Audits (axe-core)", () => {
  test("login page has zero critical accessibility violations", async ({ page }) => {
    await page.goto("/login");
    await page.waitForSelector("form");

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    const criticalViolations = accessibilityScanResults.violations.filter(
      (v) => v.impact === "critical"
    );
    expect(criticalViolations).toEqual([]);
  });

  test("register page has zero critical accessibility violations", async ({ page }) => {
    await page.goto("/register");
    await page.waitForSelector("form");

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    const criticalViolations = accessibilityScanResults.violations.filter(
      (v) => v.impact === "critical"
    );
    expect(criticalViolations).toEqual([]);
  });

  test("dashboard has zero critical accessibility violations when authenticated", async ({ page }) => {
    // Log in first
    await page.goto("/login");
    await page.fill('input[type="email"]', "sumaiya.talukder.26dafe@example.com");
    await page.fill('input[type="password"]', "SecurePassword123!");
    await page.click('button[type="submit"]');

    await page.waitForURL("/dashboard");
    await page.waitForSelector("text=Net Balance");

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    const criticalViolations = accessibilityScanResults.violations.filter(
      (v) => v.impact === "critical"
    );
    expect(criticalViolations).toEqual([]);
  });

  test("wealth simulator has zero critical accessibility violations", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[type="email"]', "sumaiya.talukder.26dafe@example.com");
    await page.fill('input[type="password"]', "SecurePassword123!");
    await page.click('button[type="submit"]');

    await page.waitForURL("/dashboard");
    await page.goto("/simulator");
    await page.waitForSelector("text=Deterministic Wealth Simulator");

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    const criticalViolations = accessibilityScanResults.violations.filter(
      (v) => v.impact === "critical"
    );
    expect(criticalViolations).toEqual([]);
  });
});
