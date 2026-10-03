import { test, expect } from "@playwright/test";

test.describe("Full End-to-End User Journey", () => {
  const timestamp = Date.now();
  const testUser = {
    email: `tanvir.ahmed.${timestamp}@example.com`,
    password: "SecurePassword123!",
    fullName: "Tanvir Ahmed",
    phone: `+88017${Math.floor(10000000 + Math.random() * 90000000)}`,
    occupation: "Software Engineer",
    income: "55000",
  };

  test("completes end-to-end registration, cash-out, goal, simulation, and AI coach flow", async ({
    page,
  }) => {
    // ----------------------------------------------------
    // STEP 1: Registration with AI Consent
    // ----------------------------------------------------
    await page.goto("/register");
    await page.waitForSelector("form");

    await page.fill("#reg-name", testUser.fullName);
    await page.fill("#reg-email", testUser.email);
    await page.fill("#reg-phone", testUser.phone);
    await page.selectOption("#reg-occ", "freelancer");
    await page.fill("#reg-password", testUser.password);

    // Ensure AI consent is checked
    const consentCheckbox = page.locator('input[type="checkbox"]');
    if (!(await consentCheckbox.isChecked())) {
      await consentCheckbox.check();
    }

    // Submit registration
    await page.click('button[type="submit"]');
    await page.waitForURL("/dashboard", { timeout: 15000 });
    await expect(page.locator("text=Net Balance")).toBeVisible();

    // ----------------------------------------------------
    // STEP 2: Record Cash-Out with Mandatory Purpose
    // ----------------------------------------------------
    await page.click("text=Record Cash-Out");
    await page.waitForSelector("#cashout-amount");

    await page.fill("#cashout-amount", "3500");
    await page.click('button:has-text("Necessity")');
    await page.click('button:has-text("bKash")');
    await page.fill("#cashout-desc", "Weekly essential groceries");

    await page.click('button[type="submit"]:has-text("Record Cash-Out")');

    // Verify modal closes
    await expect(page.locator("text=Record MFS Cash-Out")).not.toBeVisible();

    // ----------------------------------------------------
    // STEP 3: Verify Transaction on /transactions
    // ----------------------------------------------------
    await page.goto("/transactions");
    await page.waitForSelector("table");
    await expect(page.locator("text=Weekly essential groceries")).toBeVisible();
    await expect(page.locator("text=necessity")).toBeVisible();

    // ----------------------------------------------------
    // STEP 4: Inspect Behavior & Anomaly Surface
    // ----------------------------------------------------
    await page.goto("/behavior");
    await page.waitForSelector("text=Behavior & Anomaly Intelligence");
    await expect(page.locator("text=Explainability Factors")).toBeVisible();
    await expect(page.locator("text=Detected Spending Anomalies")).toBeVisible();

    // ----------------------------------------------------
    // STEP 5: Create Financial Goal on /goals
    // ----------------------------------------------------
    await page.goto("/goals");
    await page.waitForSelector("text=Financial Goals");

    await page.click('button:has-text("Create New Goal")');
    await page.waitForSelector('input[placeholder="Emergency Buffer (3 Months)"]');

    await page.fill('input[placeholder="Emergency Buffer (3 Months)"]', "Emergency Buffer Fund");
    await page.fill('input[placeholder="50000"]', "50000");
    await page.fill('input[type="date"]', "2027-12-31");
    await page.click('button[type="submit"]:has-text("Save Goal")');

    // Verify goal appears in list
    await expect(page.locator("text=Emergency Buffer Fund")).toBeVisible();
    await expect(page.locator("text=৳ 50,000")).toBeVisible();

    // ----------------------------------------------------
    // STEP 6: Wealth Simulator
    // ----------------------------------------------------
    await page.goto("/simulator");
    await page.waitForSelector("text=Deterministic Wealth Simulator");

    // Check permanently visible Assumed-Rate badge
    await expect(page.locator("text=Assumed Rate")).toBeVisible();
    await expect(page.locator("text=Rule of 72 Doubling Time")).toBeVisible();

    // ----------------------------------------------------
    // STEP 7: Conversational AI Coach
    // ----------------------------------------------------
    await page.goto("/coach");
    await page.waitForSelector('textarea[aria-label="Message to Sohoj Coach"]');

    // Type query: "Can I afford a ৳5,000 expense this month?"
    const inputArea = page.locator('textarea[aria-label="Message to Sohoj Coach"]');
    await inputArea.fill("Can I afford ৳5,000?");
    await page.click('button[aria-label="Send message"]');

    // Verify user message appears in thread
    await expect(page.locator("text=Can I afford ৳5,000?")).toBeVisible();

    // Wait for assistant response to stream and complete
    await page.waitForSelector("text=Grounded AI", { timeout: 25000 });

    // Verify grounded response content is rendered
    const assistantBubble = page.locator("text=Grounded AI").first();
    await expect(assistantBubble).toBeVisible();

    // Take final screenshot of the coach interaction
    await page.screenshot({ path: "test-results/coach-full-flow.png" });
  });
});
