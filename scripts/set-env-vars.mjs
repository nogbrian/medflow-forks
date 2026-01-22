#!/usr/bin/env node
/**
 * Set Environment Variables in Coolify
 * Navigates to the Environment Variables page and adds them
 */

import { chromium } from "playwright";

const ENV_VARS_URL = "https://coolify.trafegoparaconsultorios.com.br/project/igsckco404k4gww4kgwccgcs/environment/okk4s4kcg4kkkcssgckwo0sc/application/qgskkcw0o88404g8cwk0880w/environment-variables";

// Environment variables to configure
const ENV_VARS = [
  { key: "APP_ENV", value: "production" },
  { key: "DEBUG", value: "false" },
  { key: "JWT_SECRET", value: "aoSFZlTRQ9Cq4fylhnzt9sUkxv9-pGoLWQRsYi_Q05A" },
  { key: "WEBHOOK_SECRET", value: "sznx1iz1QEA13sQGXmQ_4PQbtTrBrdEDIHck6iw1VCw" },
  { key: "LLM_PROVIDER", value: "anthropic" },
  { key: "CORS_ORIGINS", value: '["https://medflow.trafegoparaconsultorios.com.br"]' },
];

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log("╔══════════════════════════════════════════════════════════════╗");
  console.log("║   🔧 MedFlow - Set Environment Variables in Coolify          ║");
  console.log("╚══════════════════════════════════════════════════════════════╝\n");

  const browser = await chromium.launch({
    headless: false,
    slowMo: 100,
  });

  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
  });

  const page = await context.newPage();

  try {
    console.log("📡 Opening Environment Variables page...");
    await page.goto(ENV_VARS_URL);
    await sleep(3000);

    // Check if we need to login
    const needsLogin = await page.content().then(c =>
      c.includes('type="password"') || c.includes("Sign in") || c.includes("Log in")
    );

    if (needsLogin) {
      console.log("\n🔐 LOGIN REQUIRED!");
      console.log("   → Please login in the browser");
      console.log("   → Waiting...\n");

      // Wait for login
      let attempts = 0;
      while (attempts < 150) {
        await sleep(2000);
        const url = page.url();
        if (url.includes("environment-variables")) {
          console.log("✅ Login detected!\n");
          break;
        }
        attempts++;
      }
      await sleep(2000);
    }

    // Create screenshots folder
    const fs = await import("fs");
    if (!fs.existsSync("./screenshots")) {
      fs.mkdirSync("./screenshots");
    }

    // Take screenshot
    await page.screenshot({ path: "./screenshots/env-vars-page.png", fullPage: true });
    console.log("📸 Screenshot: ./screenshots/env-vars-page.png\n");

    // Check existing variables
    console.log("🔍 Checking existing variables...");
    const pageText = await page.textContent('body');

    const hasDbUrl = pageText.includes('DATABASE_URL');
    const hasRedisUrl = pageText.includes('REDIS_URL');

    console.log(`   DATABASE_URL: ${hasDbUrl ? '✅ Found' : '❌ Not found - NEEDS CONFIGURATION'}`);
    console.log(`   REDIS_URL: ${hasRedisUrl ? '✅ Found' : '❌ Not found - NEEDS CONFIGURATION'}`);

    // Add each environment variable
    console.log("\n📝 Adding environment variables...\n");

    for (const { key, value } of ENV_VARS) {
      // Check if already exists
      if (pageText.includes(key)) {
        console.log(`   ⏭️  ${key} already exists, skipping`);
        continue;
      }

      try {
        // Click Add button
        const addBtn = await page.$('button:has-text("Add"), [data-testid="add-env-var"]');
        if (addBtn) {
          await addBtn.click();
          await sleep(500);

          // Find and fill key input
          const keyInput = await page.$('input[name="key"], input[placeholder*="Key"], input[placeholder*="key"], input[placeholder*="NAME"]');
          if (keyInput) {
            await keyInput.fill(key);
            await sleep(300);
          }

          // Find and fill value input
          const valueInput = await page.$('input[name="value"], input[placeholder*="Value"], input[placeholder*="value"], textarea[name="value"]');
          if (valueInput) {
            await valueInput.fill(value);
            await sleep(300);
          }

          // Click save/add
          const saveBtn = await page.$('button:has-text("Save"), button:has-text("Add"), button[type="submit"]');
          if (saveBtn) {
            await saveBtn.click();
            await sleep(1000);
          }

          console.log(`   ✅ ${key}=${value.substring(0, 30)}${value.length > 30 ? '...' : ''}`);
        }
      } catch (e) {
        console.log(`   ❌ Failed to add ${key}: ${e.message}`);
      }
    }

    // Final screenshot
    await page.screenshot({ path: "./screenshots/env-vars-configured.png", fullPage: true });
    console.log("\n📸 Final screenshot: ./screenshots/env-vars-configured.png");

    console.log("\n╔══════════════════════════════════════════════════════════════╗");
    console.log("║   ⚠️  IMPORTANT: You still need to add manually:             ║");
    console.log("╠══════════════════════════════════════════════════════════════╣");
    console.log("║   1. DATABASE_URL - Get from Coolify PostgreSQL              ║");
    console.log("║   2. REDIS_URL - Get from Coolify Redis                      ║");
    console.log("║   3. ANTHROPIC_API_KEY (or other LLM key)                    ║");
    console.log("╠══════════════════════════════════════════════════════════════╣");
    console.log("║   Then click 'Redeploy' at the top of the page               ║");
    console.log("╚══════════════════════════════════════════════════════════════╝");

    // Keep browser open
    console.log("\n⏳ Browser will stay open for 10 minutes...");
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
