#!/usr/bin/env node
/**
 * Fix domains in Coolify via UI automation
 */

import { chromium } from "playwright";

const APP_URL = "https://coolify.trafegoparaconsultorios.com.br/project/igsckco404k4gww4kgwccgcs/environment/okk4s4kcg4kkkcssgckwo0sc/application/qgskkcw0o88404g8cwk0880w";

const DOMAINS = {
  integration: "https://app.trafegoparaconsultorios.com.br",
  web: "https://medflow.trafegoparaconsultorios.com.br"
};

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log("╔══════════════════════════════════════════════════════════════╗");
  console.log("║   🔧 Fix MedFlow Domains in Coolify                          ║");
  console.log("╚══════════════════════════════════════════════════════════════╝\n");

  const browser = await chromium.launch({
    headless: false,
    slowMo: 150,
  });

  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
  });

  const page = await context.newPage();

  const fs = await import("fs");
  if (!fs.existsSync("./screenshots")) {
    fs.mkdirSync("./screenshots");
  }

  try {
    console.log("📡 Opening application page...");
    await page.goto(APP_URL);
    await sleep(3000);

    // Check login
    const needsLogin = await page.content().then(c =>
      c.includes('type="password"') || c.includes("Sign in")
    );

    if (needsLogin) {
      console.log("\n🔐 LOGIN REQUIRED - Please login in the browser");
      console.log("   Waiting for login...\n");

      while (true) {
        await sleep(2000);
        const content = await page.content();
        if (!content.includes('type="password"') && !content.includes("Sign in")) {
          console.log("✅ Login detected!\n");
          await page.goto(APP_URL);
          await sleep(3000);
          break;
        }
      }
    }

    await page.screenshot({ path: "./screenshots/01-app-page.png", fullPage: true });
    console.log("📸 Screenshot: ./screenshots/01-app-page.png\n");

    // Look for domain configuration section
    console.log("🔍 Looking for domain configuration...");

    // Click on the Configuration tab or look for domain inputs
    const configLink = await page.$('text=Configuration, a:has-text("Configuration"), button:has-text("Configuration")');
    if (configLink) {
      await configLink.click();
      await sleep(2000);
    }

    // Try to find domain inputs for each service
    for (const [service, domain] of Object.entries(DOMAINS)) {
      console.log(`\n📝 Configuring domain for ${service}: ${domain}`);

      // Look for input with service name nearby
      const inputs = await page.$$('input[type="text"]');
      for (const input of inputs) {
        const value = await input.inputValue();
        const placeholder = await input.getAttribute('placeholder');

        // Look for inputs that might be domain inputs
        if (placeholder?.toLowerCase().includes('domain') ||
            placeholder?.toLowerCase().includes('fqdn') ||
            value?.includes('http')) {
          console.log(`   Found input with value: ${value}`);
        }
      }
    }

    await page.screenshot({ path: "./screenshots/02-configuration.png", fullPage: true });
    console.log("\n📸 Screenshot: ./screenshots/02-configuration.png");

    console.log("\n═══════════════════════════════════════════════════════════════");
    console.log("   Please configure domains manually in the browser:");
    console.log(`   - integration: ${DOMAINS.integration}`);
    console.log(`   - web: ${DOMAINS.web}`);
    console.log("   Then click Save and Redeploy");
    console.log("═══════════════════════════════════════════════════════════════\n");

    console.log("⏳ Browser will stay open for 10 minutes...");
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
