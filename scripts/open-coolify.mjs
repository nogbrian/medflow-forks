#!/usr/bin/env node
/**
 * Open Coolify for Manual Deploy Configuration
 *
 * Abre o Coolify em um browser persistente para configuração manual.
 * O repositório já está no GitHub: https://github.com/nogbrian/medflow-forks
 */

import { chromium } from "playwright";

const COOLIFY_URL = "https://coolify.trafegoparaconsultorios.com.br";
const REPO_URL = "https://github.com/nogbrian/medflow-forks";

async function main() {
  console.log("╔══════════════════════════════════════════════════════════════╗");
  console.log("║        MedFlow Forks - Deploy no Coolify                     ║");
  console.log("╚══════════════════════════════════════════════════════════════╝\n");

  console.log("📦 Repositório: " + REPO_URL);
  console.log("🌐 Coolify: " + COOLIFY_URL);
  console.log("\n");

  // Iniciar browser persistente
  const browser = await chromium.launch({
    headless: false,
    slowMo: 50,
    args: ["--start-maximized"],
  });

  const context = await browser.newContext({
    viewport: null, // Maximizado
  });

  const page = await context.newPage();

  // Navegar para Coolify
  console.log("🚀 Abrindo Coolify...\n");
  await page.goto(COOLIFY_URL);

  console.log("╔══════════════════════════════════════════════════════════════╗");
  console.log("║  INSTRUÇÕES PARA DEPLOY:                                     ║");
  console.log("╠══════════════════════════════════════════════════════════════╣");
  console.log("║                                                              ║");
  console.log("║  1. Faça login no Coolify (se necessário)                    ║");
  console.log("║                                                              ║");
  console.log("║  2. Vá para Projects → Create New Project                    ║");
  console.log("║     Nome: medflow-forks                                      ║");
  console.log("║                                                              ║");
  console.log("║  3. Adicione um Resource → Public Repository                 ║");
  console.log("║     Repository URL: " + REPO_URL + "     ║");
  console.log("║     Branch: main                                             ║");
  console.log("║     Build Pack: Docker Compose                               ║");
  console.log("║                                                              ║");
  console.log("║  4. Configure Environment Variables:                         ║");
  console.log("║     APP_ENV=production                                       ║");
  console.log("║     JWT_SECRET=<gerar-secret-32-chars>                       ║");
  console.log("║     WEBHOOK_SECRET=<gerar-secret-32-chars>                   ║");
  console.log("║                                                              ║");
  console.log("║  5. Clique em Deploy!                                        ║");
  console.log("║                                                              ║");
  console.log("╚══════════════════════════════════════════════════════════════╝\n");

  console.log("⏳ Browser aberto. Configure manualmente e feche quando terminar.");
  console.log("   (Ou pressione Ctrl+C para fechar)\n");

  // Aguardar até o usuário fechar
  page.on("close", () => {
    console.log("\n✅ Página fechada. Encerrando...");
    process.exit(0);
  });

  // Manter rodando indefinidamente
  await new Promise(() => {});
}

main().catch((err) => {
  console.error("❌ Erro:", err.message);
  process.exit(1);
});
