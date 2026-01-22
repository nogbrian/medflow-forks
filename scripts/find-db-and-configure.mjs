#!/usr/bin/env node
/**
 * Find PostgreSQL/Redis in Coolify and configure all env vars
 */

import { chromium } from "playwright";

const PROJECT_URL = "https://coolify.trafegoparaconsultorios.com.br/project/igsckco404k4gww4kgwccgcs";
const APP_ENV_URL = "https://coolify.trafegoparaconsultorios.com.br/project/igsckco404k4gww4kgwccgcs/environment/okk4s4kcg4kkkcssgckwo0sc/application/qgskkcw0o88404g8cwk0880w/environment-variables";

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log("╔══════════════════════════════════════════════════════════════╗");
  console.log("║   🔍 Find PostgreSQL/Redis and Configure MedFlow             ║");
  console.log("╚══════════════════════════════════════════════════════════════╝\n");

  const browser = await chromium.launch({
    headless: false,
    slowMo: 100,
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
    // 1. Go to project page
    console.log("📡 Opening project page...");
    await page.goto(PROJECT_URL);
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
        if (url.includes("/project/") && !await page.content().then(c => c.includes('type="password"'))) {
          console.log("✅ Logged in!\n");
          break;
        }
      }
    }

    await sleep(2000);
    await page.screenshot({ path: "./screenshots/01-project-page.png", fullPage: true });
    console.log("📸 Screenshot: ./screenshots/01-project-page.png");

    // 2. Look for production environment
    console.log("\n🔍 Looking for production environment...");
    await page.click('text=production').catch(() => {});
    await sleep(2000);
    await page.screenshot({ path: "./screenshots/02-production-env.png", fullPage: true });

    // 3. Get page text to analyze what resources exist
    const pageText = await page.textContent('body');
    console.log("\n📋 Resources found on page:");

    const hasPostgres = pageText.toLowerCase().includes('postgres');
    const hasRedis = pageText.toLowerCase().includes('redis');
    const hasMedflow = pageText.toLowerCase().includes('medflow');

    console.log(`   PostgreSQL: ${hasPostgres ? '✅' : '❌'}`);
    console.log(`   Redis: ${hasRedis ? '✅' : '❌'}`);
    console.log(`   MedFlow App: ${hasMedflow ? '✅' : '❌'}`);

    // 4. Try to find and click on PostgreSQL to get connection URL
    let dbUrl = null;
    let redisUrl = null;

    if (hasPostgres) {
      console.log("\n🐘 Finding PostgreSQL connection string...");

      // Click on postgres link
      const pgLink = await page.$('a:has-text("postgres"), a:has-text("Postgres"), a:has-text("PostgreSQL"), [href*="database"]');
      if (pgLink) {
        await pgLink.click();
        await sleep(2000);
        await page.screenshot({ path: "./screenshots/03-postgres-page.png", fullPage: true });

        // Look for connection string
        const pgPageText = await page.textContent('body');

        // Try to find DATABASE_URL pattern
        const dbMatch = pgPageText.match(/postgresql:\/\/[^\s<>"]+/);
        if (dbMatch) {
          dbUrl = dbMatch[0];
          console.log(`   ✅ Found: ${dbUrl.substring(0, 50)}...`);
        } else {
          console.log("   ⚠️ Connection string not visible on this page");
          console.log("   → Look in the PostgreSQL configuration page");
        }

        // Go back
        await page.goBack();
        await sleep(1000);
      }
    }

    if (hasRedis) {
      console.log("\n🔴 Finding Redis connection string...");

      const redisLink = await page.$('a:has-text("redis"), a:has-text("Redis"), [href*="redis"]');
      if (redisLink) {
        await redisLink.click();
        await sleep(2000);
        await page.screenshot({ path: "./screenshots/04-redis-page.png", fullPage: true });

        const redisPageText = await page.textContent('body');
        const redisMatch = redisPageText.match(/redis:\/\/[^\s<>"]+/);
        if (redisMatch) {
          redisUrl = redisMatch[0];
          console.log(`   ✅ Found: ${redisUrl}`);
        } else {
          console.log("   ⚠️ Connection string not visible on this page");
        }

        await page.goBack();
        await sleep(1000);
      }
    }

    // 5. Navigate to Environment Variables
    console.log("\n📝 Opening Environment Variables page...");
    await page.goto(APP_ENV_URL);
    await sleep(3000);
    await page.screenshot({ path: "./screenshots/05-env-vars-page.png", fullPage: true });

    // 6. Print instructions
    console.log("\n╔══════════════════════════════════════════════════════════════╗");
    console.log("║   📋 ENVIRONMENT VARIABLES TO ADD IN COOLIFY                 ║");
    console.log("╠══════════════════════════════════════════════════════════════╣");
    console.log("║                                                              ║");
    console.log("║   Required (Add these in the Environment Variables tab):    ║");
    console.log("║                                                              ║");

    if (dbUrl) {
      console.log(`║   DATABASE_URL=${dbUrl.substring(0, 45)}...`);
    } else {
      console.log("║   DATABASE_URL=<get from PostgreSQL resource>");
    }

    if (redisUrl) {
      console.log(`║   REDIS_URL=${redisUrl}`);
    } else {
      console.log("║   REDIS_URL=<get from Redis resource>");
    }

    console.log("║   JWT_SECRET=aoSFZlTRQ9Cq4fylhnzt9sUkxv9-pGoLWQRsYi_Q05A");
    console.log("║   WEBHOOK_SECRET=sznx1iz1QEA13sQGXmQ_4PQbtTrBrdEDIHck6iw1VCw");
    console.log("║   APP_ENV=production");
    console.log("║   DEBUG=false");
    console.log("║   LLM_PROVIDER=anthropic");
    console.log("║   CORS_ORIGINS=[\"https://medflow.trafegoparaconsultorios.com.br\"]");
    console.log("║                                                              ║");
    console.log("║   LLM Keys (add at least one):                               ║");
    console.log("║   ANTHROPIC_API_KEY=<your key>                               ║");
    console.log("║                                                              ║");
    console.log("╠══════════════════════════════════════════════════════════════╣");
    console.log("║   After adding, click 'Redeploy' at the top!                 ║");
    console.log("╚══════════════════════════════════════════════════════════════╝");

    // 7. Try to add variables automatically
    console.log("\n🔧 Attempting to add variables automatically...");

    const varsToAdd = [
      { key: "APP_ENV", value: "production" },
      { key: "DEBUG", value: "false" },
      { key: "JWT_SECRET", value: "aoSFZlTRQ9Cq4fylhnzt9sUkxv9-pGoLWQRsYi_Q05A" },
      { key: "WEBHOOK_SECRET", value: "sznx1iz1QEA13sQGXmQ_4PQbtTrBrdEDIHck6iw1VCw" },
      { key: "LLM_PROVIDER", value: "anthropic" },
      { key: "CORS_ORIGINS", value: '["https://medflow.trafegoparaconsultorios.com.br"]' },
    ];

    if (dbUrl) {
      varsToAdd.unshift({ key: "DATABASE_URL", value: dbUrl });
    }
    if (redisUrl) {
      varsToAdd.unshift({ key: "REDIS_URL", value: redisUrl });
    }

    for (const { key, value } of varsToAdd) {
      try {
        // Look for Add button
        const addBtns = await page.$$('button');
        for (const btn of addBtns) {
          const text = await btn.textContent();
          if (text && (text.includes('Add') || text.includes('New'))) {
            await btn.click();
            await sleep(500);
            break;
          }
        }

        // Fill form
        const inputs = await page.$$('input');
        if (inputs.length >= 2) {
          // Usually first input is key, second is value
          for (const input of inputs) {
            const placeholder = await input.getAttribute('placeholder');
            const name = await input.getAttribute('name');
            if (placeholder?.toLowerCase().includes('key') || name?.toLowerCase().includes('key')) {
              await input.fill(key);
            } else if (placeholder?.toLowerCase().includes('value') || name?.toLowerCase().includes('value')) {
              await input.fill(value);
            }
          }
          await sleep(300);

          // Click save
          const saveBtns = await page.$$('button');
          for (const btn of saveBtns) {
            const text = await btn.textContent();
            if (text && text.includes('Save')) {
              await btn.click();
              await sleep(500);
              console.log(`   ✅ Added: ${key}`);
              break;
            }
          }
        }
      } catch (e) {
        console.log(`   ❌ Could not add ${key}: ${e.message}`);
      }
    }

    await page.screenshot({ path: "./screenshots/06-final-state.png", fullPage: true });
    console.log("\n📸 Final screenshot: ./screenshots/06-final-state.png");

    console.log("\n════════════════════════════════════════════════════════════════");
    console.log("   Browser will stay open - complete the configuration manually");
    console.log("   Don't forget to click REDEPLOY when done!");
    console.log("════════════════════════════════════════════════════════════════\n");

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
