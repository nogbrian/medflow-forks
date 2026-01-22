#!/usr/bin/env node
/**
 * Configure Environment Variables in Coolify
 * Goes directly to the application and sets up all env vars
 */

import { chromium } from "playwright";

const APP_URL = "https://coolify.trafegoparaconsultorios.com.br/project/igsckco404k4gww4kgwccgcs/environment/okk4s4kcg4kkkcssgckwo0sc/application/qgskkcw0o88404g8cwk0880w";

// Environment variables to configure (excluding LLM keys - user will add those)
const ENV_VARS = {
  // Application
  APP_ENV: "production",
  DEBUG: "false",

  // Security (generated secrets)
  JWT_SECRET: "aoSFZlTRQ9Cq4fylhnzt9sUkxv9-pGoLWQRsYi_Q05A",
  WEBHOOK_SECRET: "sznx1iz1QEA13sQGXmQ_4PQbtTrBrdEDIHck6iw1VCw",

  // LLM (placeholder - user configures)
  LLM_PROVIDER: "anthropic",

  // CORS
  CORS_ORIGINS: '["https://medflow.trafegoparaconsultorios.com.br"]',

  // External Services (empty - optional)
  TWENTY_API_URL: "",
  TWENTY_API_KEY: "",
  CALCOM_API_URL: "",
  CALCOM_API_KEY: "",
  CHATWOOT_API_URL: "",
  CHATWOOT_API_KEY: "",
  EVOLUTION_API_URL: "",
  EVOLUTION_API_KEY: "",
  REPLICATE_API_KEY: "",
};

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log("╔══════════════════════════════════════════════════════════════╗");
  console.log("║   🔧 MedFlow - Configurar Environment Variables no Coolify   ║");
  console.log("╚══════════════════════════════════════════════════════════════╝\n");

  const browser = await chromium.launch({
    headless: false,
    slowMo: 50,
  });

  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
  });

  const page = await context.newPage();

  try {
    // 1. Go to the application page
    console.log("📡 Abrindo aplicação no Coolify...");
    await page.goto(APP_URL);
    await sleep(2000);

    // 2. Check if we need to login
    const content = await page.content();
    const needsLogin = content.includes('type="password"') ||
                       content.includes("Sign in") ||
                       content.includes("Log in");

    if (needsLogin) {
      console.log("\n🔐 LOGIN NECESSÁRIO!");
      console.log("   → Faça login no browser que abriu");
      console.log("   → Aguardando...\n");

      // Wait for login (max 5 minutes)
      let attempts = 0;
      while (attempts < 150) {
        await sleep(2000);
        const currentContent = await page.content();
        const currentUrl = page.url();

        // Check if logged in
        if (currentUrl.includes("/application/") &&
            !currentContent.includes('type="password"')) {
          console.log("✅ Login detectado!\n");
          break;
        }
        attempts++;
      }
    }

    await sleep(2000);

    // 3. Navigate to Environment Variables tab
    console.log("📝 Procurando aba de Environment Variables...");

    // Click on Environment tab/link
    const envTab = await page.$('a[href*="environment-variables"], button:has-text("Environment"), [data-tab="environment"], a:has-text("Environment")');
    if (envTab) {
      await envTab.click();
      await sleep(2000);
    } else {
      // Try clicking text directly
      await page.click('text=Environment Variables').catch(() => {});
      await sleep(1000);
      await page.click('text=Environment').catch(() => {});
      await sleep(2000);
    }

    // 4. Take screenshot of current state
    const fs = await import("fs");
    if (!fs.existsSync("./screenshots")) {
      fs.mkdirSync("./screenshots");
    }
    await page.screenshot({ path: "./screenshots/env-page.png", fullPage: true });
    console.log("   📸 Screenshot: ./screenshots/env-page.png");

    // 5. Look for existing DATABASE_URL and REDIS_URL
    console.log("\n🔍 Procurando DATABASE_URL e REDIS_URL existentes...");

    const pageText = await page.textContent('body');
    const hasDbUrl = pageText.includes('DATABASE_URL');
    const hasRedisUrl = pageText.includes('REDIS_URL');

    console.log(`   DATABASE_URL: ${hasDbUrl ? '✅ Encontrado' : '❌ Não encontrado'}`);
    console.log(`   REDIS_URL: ${hasRedisUrl ? '✅ Encontrado' : '❌ Não encontrado'}`);

    // 6. Print env vars to add
    console.log("\n╔══════════════════════════════════════════════════════════════╗");
    console.log("║   📋 VARIÁVEIS DE AMBIENTE PARA ADICIONAR                    ║");
    console.log("╠══════════════════════════════════════════════════════════════╣");

    for (const [key, value] of Object.entries(ENV_VARS)) {
      if (value) {
        console.log(`║   ${key}=${value.substring(0, 40)}${value.length > 40 ? '...' : ''}`);
      }
    }

    console.log("╠══════════════════════════════════════════════════════════════╣");
    console.log("║   ⚠️  VOCÊ PRECISA ADICIONAR MANUALMENTE:                    ║");
    console.log("║   - ANTHROPIC_API_KEY (ou outra LLM key)                     ║");
    console.log("║   - DATABASE_URL (do PostgreSQL do Coolify)                  ║");
    console.log("║   - REDIS_URL (do Redis do Coolify)                          ║");
    console.log("╚══════════════════════════════════════════════════════════════╝");

    // 7. Try to find "Add" button for env vars
    console.log("\n🔧 Tentando adicionar variáveis automaticamente...");

    for (const [key, value] of Object.entries(ENV_VARS)) {
      if (!value) continue;

      try {
        // Look for "Add" button
        const addBtn = await page.$('button:has-text("Add"), button:has-text("New"), button:has-text("+")');
        if (addBtn) {
          await addBtn.click();
          await sleep(500);

          // Fill key
          const keyInput = await page.$('input[name="key"], input[placeholder*="key"], input[placeholder*="KEY"], input[placeholder*="name"]');
          if (keyInput) {
            await keyInput.fill(key);
            await sleep(200);
          }

          // Fill value
          const valueInput = await page.$('input[name="value"], input[placeholder*="value"], textarea[name="value"]');
          if (valueInput) {
            await valueInput.fill(value);
            await sleep(200);
          }

          // Save
          const saveBtn = await page.$('button:has-text("Save"), button:has-text("Add"), button[type="submit"]');
          if (saveBtn) {
            await saveBtn.click();
            await sleep(500);
            console.log(`   ✅ ${key} adicionado`);
          }
        }
      } catch (e) {
        // Continue with next var
      }
    }

    // 8. Final screenshot
    await page.screenshot({ path: "./screenshots/env-configured.png", fullPage: true });
    console.log("\n   📸 Screenshot final: ./screenshots/env-configured.png");

    console.log("\n════════════════════════════════════════════════════════════════");
    console.log("   Browser permanecerá aberto para você completar a configuração");
    console.log("   Pressione Ctrl+C quando terminar");
    console.log("════════════════════════════════════════════════════════════════\n");

    // Keep browser open
    await sleep(600000); // 10 minutes

  } catch (error) {
    console.error("\n❌ Erro:", error.message);
    await page.screenshot({ path: "./screenshots/error.png", fullPage: true });
    await sleep(300000);
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
