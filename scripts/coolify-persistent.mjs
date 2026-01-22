#!/usr/bin/env node
/**
 * Coolify - Browser Persistente
 * NÃO FECHA O NAVEGADOR!
 */

import { chromium } from "playwright";

const COOLIFY_URL = "https://coolify.trafegoparaconsultorios.com.br";

async function main() {
  console.log("🚀 Abrindo Coolify - NAVEGADOR PERSISTENTE\n");

  const browser = await chromium.launch({
    headless: false,
    slowMo: 50,
  });

  const page = await browser.newPage();
  await page.goto(COOLIFY_URL);

  console.log("✅ Navegador aberto!");
  console.log("📍 URL: " + COOLIFY_URL);
  console.log("\n⚠️  NAVEGADOR NÃO VAI FECHAR AUTOMATICAMENTE");
  console.log("   Faça login e me avise quando estiver pronto.\n");

  // NUNCA FECHA - loop infinito
  while (true) {
    await new Promise(r => setTimeout(r, 60000));
    console.log("   [navegador ainda aberto...]");
  }
}

main().catch(e => {
  console.error("Erro:", e.message);
  // Mesmo com erro, não sair
  setInterval(() => {}, 1000000);
});
