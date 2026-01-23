#!/usr/bin/env node
/**
 * Set ALL Environment Variables in Coolify for MedFlow Integration
 *
 * Usage:
 *   node scripts/set-env-vars.mjs
 *   node scripts/set-env-vars.mjs --anthropic-key=sk-ant-xxx
 *
 * This will open a browser, wait for you to login, then set all vars.
 * DATABASE_URL and REDIS_URL must already exist in Coolify (from PostgreSQL/Redis services).
 */

import { chromium } from "playwright";

const ENV_VARS_URL = "https://coolify.trafegoparaconsultorios.com.br/project/igsckco404k4gww4kgwccgcs/environment/okk4s4kcg4kkkcssgckwo0sc/application/qgskkcw0o88404g8cwk0880w/environment-variables";

// Parse CLI args
const args = Object.fromEntries(
  process.argv.slice(2)
    .filter(a => a.startsWith("--"))
    .map(a => {
      const [k, ...v] = a.slice(2).split("=");
      return [k, v.join("=") || "true"];
    })
);

// Complete environment variables for the integration service
const ENV_VARS = [
  // --- Application ---
  { key: "APP_ENV", value: "production" },
  { key: "DEBUG", value: "false" },

  // --- Security ---
  { key: "JWT_SECRET", value: "aoSFZlTRQ9Cq4fylhnzt9sUkxv9-pGoLWQRsYi_Q05A" },
  { key: "WEBHOOK_SECRET", value: "sznx1iz1QEA13sQGXmQ_4PQbtTrBrdEDIHck6iw1VCw" },

  // --- LLM / Agno ---
  { key: "LLM_PROVIDER", value: "anthropic" },
  { key: "MODEL_SMART", value: "claude-sonnet-4-5-20250514" },
  { key: "MODEL_FAST", value: "claude-haiku-4-20250514" },
  { key: "ANTHROPIC_API_KEY", value: args["anthropic-key"] || "" },
  { key: "OPENAI_API_KEY", value: args["openai-key"] || "" },
  { key: "GOOGLE_API_KEY", value: args["google-key"] || "" },
  { key: "XAI_API_KEY", value: args["xai-key"] || "" },

  // --- Twenty CRM ---
  { key: "TWENTY_API_URL", value: "https://crm.trafegoparaconsultorios.com.br" },
  { key: "TWENTY_API_KEY", value: args["twenty-key"] || "" },

  // --- Cal.com ---
  { key: "CALCOM_API_URL", value: "https://agenda.trafegoparaconsultorios.com.br" },
  { key: "CALCOM_API_KEY", value: args["calcom-key"] || "" },
  { key: "CALCOM_EVENT_TYPE_ID_DEFAULT", value: "1" },

  // --- Chatwoot ---
  { key: "CHATWOOT_API_URL", value: "https://inbox.trafegoparaconsultorios.com.br" },
  { key: "CHATWOOT_API_KEY", value: args["chatwoot-key"] || "" },
  { key: "CHATWOOT_ACCOUNT_ID", value: "1" },
  { key: "CHATWOOT_INBOX_ID", value: "1" },
  { key: "CHATWOOT_HUMAN_TEAM_ID", value: "1" },

  // --- WhatsApp (Evolution API) ---
  { key: "EVOLUTION_API_URL", value: args["evolution-url"] || "" },
  { key: "EVOLUTION_API_KEY", value: args["evolution-key"] || "" },
  { key: "EVOLUTION_INSTANCE_AGENCIA", value: "agencia" },

  // --- Image Generation ---
  { key: "REPLICATE_API_KEY", value: args["replicate-key"] || "" },
  { key: "NANOBANANA_API_KEY", value: args["nanobanana-key"] || "" },

  // --- Social / Ads ---
  { key: "META_ACCESS_TOKEN", value: args["meta-token"] || "" },

  // --- Scraping ---
  { key: "APIFY_TOKEN", value: args["apify-token"] || "" },

  // --- CORS ---
  { key: "CORS_ORIGINS_RAW", value: "https://medflow.trafegoparaconsultorios.com.br,https://studio.trafegoparaconsultorios.com.br" },
];

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log("╔══════════════════════════════════════════════════════════════╗");
  console.log("║   MedFlow - Configurar Environment Variables no Coolify     ║");
  console.log("╚══════════════════════════════════════════════════════════════╝\n");

  // Filter out empty values (user didn't provide)
  const varsToSet = ENV_VARS.filter(v => v.value !== "");
  const varsSkipped = ENV_VARS.filter(v => v.value === "");

  console.log(`Variáveis a configurar: ${varsToSet.length}`);
  console.log(`Variáveis sem valor (puladas): ${varsSkipped.length}`);
  if (varsSkipped.length > 0) {
    console.log(`   Puladas: ${varsSkipped.map(v => v.key).join(", ")}`);
  }
  console.log("");

  const browser = await chromium.launch({
    headless: false,
    slowMo: 100,
  });

  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
  });

  const page = await context.newPage();

  try {
    console.log("Abrindo página de Environment Variables...");
    await page.goto(ENV_VARS_URL);
    await sleep(3000);

    // Check if login needed
    const needsLogin = await page.content().then(c =>
      c.includes('type="password"') || c.includes("Sign in") || c.includes("Log in")
    );

    if (needsLogin) {
      console.log("\n[LOGIN NECESSARIO]");
      console.log("   Faca login no browser que abriu");
      console.log("   Aguardando...\n");

      let attempts = 0;
      while (attempts < 150) {
        await sleep(2000);
        const url = page.url();
        if (url.includes("environment-variables")) {
          console.log("[OK] Login detectado!\n");
          break;
        }
        attempts++;
      }
      await sleep(2000);
    }

    // Check existing variables
    console.log("Verificando variáveis existentes...");
    const pageText = await page.textContent("body");

    const existing = varsToSet.filter(v => pageText.includes(v.key));
    const toAdd = varsToSet.filter(v => !pageText.includes(v.key));

    console.log(`   Já existem: ${existing.length} (${existing.map(v => v.key).join(", ") || "nenhuma"})`);
    console.log(`   A adicionar: ${toAdd.length}\n`);

    // Check required vars
    const hasDbUrl = pageText.includes("DATABASE_URL");
    const hasRedisUrl = pageText.includes("REDIS_URL");
    console.log(`   DATABASE_URL: ${hasDbUrl ? "[OK]" : "[FALTA] - Adicione manualmente do PostgreSQL service"}`);
    console.log(`   REDIS_URL: ${hasRedisUrl ? "[OK]" : "[FALTA] - Adicione manualmente do Redis service"}\n`);

    // Add each env var
    let added = 0;
    let failed = 0;

    for (const { key, value } of toAdd) {
      try {
        // Find and click Add button
        const addBtn = await page.$('button:has-text("Add"), [data-testid="add-env-var"], button:has-text("New")');
        if (!addBtn) {
          console.log(`   [ERRO] Botão "Add" não encontrado para ${key}`);
          failed++;
          continue;
        }

        await addBtn.click();
        await sleep(500);

        // Fill key input
        const keyInput = await page.$(
          'input[name="key"], input[placeholder*="Key"], input[placeholder*="key"], input[placeholder*="NAME"], input[placeholder*="name"]'
        );
        if (keyInput) {
          await keyInput.fill(key);
          await sleep(200);
        }

        // Fill value input
        const valueInput = await page.$(
          'input[name="value"], input[placeholder*="Value"], input[placeholder*="value"], textarea[name="value"], textarea[placeholder*="value"]'
        );
        if (valueInput) {
          await valueInput.fill(value);
          await sleep(200);
        }

        // Click save
        const saveBtn = await page.$(
          'button:has-text("Save"), button:has-text("Add"), button[type="submit"]'
        );
        if (saveBtn) {
          await saveBtn.click();
          await sleep(800);
        }

        const displayValue = value.length > 40 ? value.substring(0, 37) + "..." : value;
        console.log(`   [OK] ${key}=${displayValue}`);
        added++;
      } catch (e) {
        console.log(`   [ERRO] ${key}: ${e.message}`);
        failed++;
      }
    }

    // Summary
    console.log("\n══════════════════════════════════════════════════════════════");
    console.log(`   Adicionadas: ${added} | Falharam: ${failed} | Já existiam: ${existing.length}`);
    console.log("══════════════════════════════════════════════════════════════");

    if (!hasDbUrl || !hasRedisUrl) {
      console.log("\n[ACAO NECESSARIA]");
      if (!hasDbUrl) console.log("   1. Adicione DATABASE_URL (copie do servico PostgreSQL no Coolify)");
      if (!hasRedisUrl) console.log("   2. Adicione REDIS_URL (copie do servico Redis no Coolify)");
    }

    if (varsSkipped.some(v => v.key === "ANTHROPIC_API_KEY")) {
      console.log("\n[ACAO NECESSARIA]");
      console.log("   Adicione ANTHROPIC_API_KEY manualmente (ou passe --anthropic-key=sk-ant-xxx)");
    }

    console.log("\n   Depois de configurar tudo, clique 'Redeploy' no topo da página.");
    console.log("\n   Browser permanecerá aberto por 10 minutos...");
    await sleep(600000);

  } catch (error) {
    console.error(`\n[ERRO] ${error.message}`);
    await sleep(300000);
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
