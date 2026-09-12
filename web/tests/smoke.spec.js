import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (url.port === "3100") return route.continue();
    if (url.port === "8000") {
      const headers = { "access-control-allow-origin": "*" };
      if (url.pathname === "/status") {
        return route.fulfill({ headers, json: { voice: { connected: false } } });
      }
      if (url.pathname === "/chat") {
        return route.fulfill({ headers, json: { reply: "Mocked reply: how can I help?", tool_events: [] } });
      }
      if (url.pathname === "/feed") return route.fulfill({ headers, json: { events: [] } });
      if (url.pathname === "/events") {
        const bookings = url.searchParams.get("tenant") === "restaurant" ? 7 : 2;
        return route.fulfill({
          contentType: "text/event-stream",
          headers,
          body: `data: ${JSON.stringify({ bookings })}\n\n`,
        });
      }
    }
    // Provider calls and external assets never leave the browser test.
    return route.abort();
  });
});

test("text fallback sends a valid chat request without a microphone", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page.getByRole("tab", { name: "Text", exact: true })).toHaveAttribute("aria-selected", "true");
  await expect(page.getByRole("tab", { name: "Voice", exact: true })).toBeDisabled();
  await page.locator(".chat-input").fill("Hello, I would like an appointment.");
  const requestPromise = page.waitForRequest("**/chat");
  await page.getByRole("button", { name: "Send", exact: true }).click();
  const request = await requestPromise;
  expect(request.postDataJSON()).toEqual({
    vertical: "dental",
    messages: [{ role: "user", content: "Hello, I would like an appointment." }],
  });
  await expect(page.getByText("Mocked reply: how can I help?", { exact: true })).toBeVisible();
  expect(errors).toEqual([]);
});

test("dashboard changes tenant and can navigate back", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.locator(".dash-kpi-v").nth(1)).toHaveText("2");
  await page.locator(".dash-tenants button").nth(1).click();
  await expect(page.locator(".dash-kpi-v").nth(1)).toHaveText("7");
  await page.locator(".dash-back").click();
  await expect(page).toHaveURL("/");
});

test("reduced motion leaves reveal content visible", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const reveal = page.locator(".reveal").first();
  await expect(reveal).toHaveClass(/\bin\b/);
  await expect(reveal).toHaveCSS("opacity", "1");
});
