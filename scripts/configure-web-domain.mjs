#!/usr/bin/env node
/**
 * Configure web domain in Coolify
 */

import { chromium } from "playwright";

const APP_URL = "https://coolify.trafegoparaconsultorios.com.br/project/igsckco404k4gww4kgwccgcs/environment/okk4s4kcg4kkkcssgckwo0sc/application/qgskkcw0o88404g8cwk0880w";

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log("🔧 Configuring web domain in Coolify...\n");

  const browser = await chromium.launch({
    headless: false,
    slowMo: 100,
  });

  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
  });

  const page = await context.newPage();

  try {
    console.log("📡 Opening application page...");
    await page.goto(APP_URL);
    await sleep(3000);

    // Check login
    const needsLogin = await page.content().then(c =>
      c.includes('type="password"') || c.includes("Sign in")
    );

    if (needsLogin) {
      console.log("\n🔐 LOGIN REQUIRED - Please login in the browser\n");
      while (true) {
        await sleep(2000);
        const url = page.url();
        if (url.includes("/application/") && !await page.content().then(c => c.includes('type="password"'))) {
          console.log("✅ Logged in!\n");
          break;
        }
      }
    }

    await sleep(2000);

    // Look for the web service domain configuration
    console.log("🔍 Looking for web service domain input...");

    // The page should show domain configuration for each service
    // Look for input fields related to domains
    const pageText = await page.textContent('body');

    if (pageText.includes('web')) {
      console.log("✅ Found web service on page");
    }

    // Take screenshot
    const fs = await import("fs");
    if (!fs.existsSync("./screenshots")) {
      fs.mkdirSync("./screenshots");
    }
    await page.screenshot({ path: "./screenshots/coolify-domains.png", fullPage: true });
    console.log("📸 Screenshot: ./screenshots/coolify-domains.png");

    console.log("\n═══════════════════════════════════════════════════════════════");
    console.log("   Please configure the web service domain manually:");
    console.log("   Domain: https://medflow.trafegoparaconsultorios.com.br");
    console.log("═══════════════════════════════════════════════════════════════\n");

    // Keep browser open
    await sleep(600000);

  } catch (error) {
    console.error("\n❌ Error:", error.message);
    await page.screenshot({ path: "./screenshots/error.png", fullPage: true });
    await sleep(300000);
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
