#!/usr/bin/env node
/**
 * Deploy MedFlow Forks to Coolify
 *
 * Script interativo usando Playwright para configurar deploy no Coolify.
 * Executa em modo headed para permitir login manual.
 *
 * Uso: node scripts/deploy-coolify.mjs
 */

import { chromium } from "playwright";

const COOLIFY_URL = "https://coolify.trafegoparaconsultorios.com.br";
const REPO_URL = "https://github.com/nogbrian/medflow-forks";
const PROJECT_NAME = "medflow-forks";

async function main() {
  console.log("🚀 Iniciando deploy do MedFlow Forks no Coolify...\n");

  // Iniciar browser em modo visível
  const browser = await chromium.launch({
    headless: false,
    slowMo: 100, // Mais lento para visualizar
  });

  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
  });

  const page = await context.newPage();

  try {
    // 1. Navegar para Coolify
    console.log("📡 Abrindo Coolify...");
    await page.goto(COOLIFY_URL);

    // 2. Aguardar login
    console.log("🔐 Aguardando login...");
    console.log("   → Por favor, faça login no Coolify se necessário");

    // Esperar até estar no dashboard (detectar "Projects" ou "Dashboard")
    await page.waitForFunction(
      () => {
        const text = document.body.innerText.toLowerCase();
        return text.includes("projects") || text.includes("dashboard") || text.includes("servers");
      },
      { timeout: 120000 }
    );

    console.log("✅ Login detectado!\n");

    // 3. Ir para Projects
    console.log("📁 Navegando para Projects...");

    // Tentar diferentes seletores para Projects
    const projectsLink = await page.$('a:has-text("Projects"), [href*="project"], nav >> text=Projects');
    if (projectsLink) {
      await projectsLink.click();
      await page.waitForLoadState("networkidle");
    }

    // 4. Verificar se projeto existe
    console.log(`🔍 Procurando projeto "${PROJECT_NAME}"...`);
    await page.waitForTimeout(2000);

    const existingProject = await page.$(`text="${PROJECT_NAME}"`);

    if (existingProject) {
      console.log("📦 Projeto encontrado! Abrindo...");
      await existingProject.click();
      await page.waitForLoadState("networkidle");
    } else {
      console.log("🆕 Projeto não encontrado. Criando novo...");

      // Procurar botão de adicionar
      const addBtn = await page.$(
        'button:has-text("New Project"), button:has-text("Add"), [data-testid="add-project"], button >> svg'
      );

      if (addBtn) {
        await addBtn.click();
        await page.waitForLoadState("networkidle");
        await page.waitForTimeout(1000);

        // Preencher nome
        const nameInput = await page.$('input[name="name"], input[placeholder*="Name"], input#name');
        if (nameInput) {
          await nameInput.fill(PROJECT_NAME);
          console.log(`   → Nome: ${PROJECT_NAME}`);
        }

        // Preencher descrição
        const descInput = await page.$('textarea[name="description"], input[name="description"]');
        if (descInput) {
          await descInput.fill("Plataforma unificada com Twenty CRM, Cal.com e Chatwoot");
        }

        // Salvar projeto
        const saveBtn = await page.$('button:has-text("Save"), button:has-text("Create"), button[type="submit"]');
        if (saveBtn) {
          await saveBtn.click();
          await page.waitForLoadState("networkidle");
          console.log("   → Projeto criado!");
        }
      }
    }

    // 5. Adicionar recurso (se necessário)
    console.log("\n🔧 Configurando recurso...");
    await page.waitForTimeout(2000);

    // Procurar botão de adicionar recurso
    const addResourceBtn = await page.$(
      'button:has-text("New Resource"), button:has-text("Add Resource"), text="+ New"'
    );

    if (addResourceBtn) {
      await addResourceBtn.click();
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(1000);

      // Selecionar tipo - Public Repository
      console.log("   → Selecionando Public Repository...");
      const publicRepoOption = await page.$('text="Public Repository", button:has-text("Public")');
      if (publicRepoOption) {
        await publicRepoOption.click();
        await page.waitForTimeout(1000);
      }

      // Preencher URL do repositório
      const repoInput = await page.$(
        'input[name="repository_url"], input[placeholder*="repository"], input[placeholder*="https://github"]'
      );
      if (repoInput) {
        await repoInput.fill(REPO_URL);
        console.log(`   → Repository: ${REPO_URL}`);
      }

      // Branch
      const branchInput = await page.$('input[name="branch"], input[placeholder*="branch"]');
      if (branchInput) {
        await branchInput.fill("main");
        console.log("   → Branch: main");
      }

      // Build pack - Docker Compose
      const dockerComposeOption = await page.$('text="Docker Compose", button:has-text("Docker Compose")');
      if (dockerComposeOption) {
        await dockerComposeOption.click();
        console.log("   → Build pack: Docker Compose");
      }
    }

    // 6. Continuar configuração manual
    console.log("\n⏳ Continuando configuração...");
    console.log("   → Complete a configuração manualmente se necessário");
    console.log("   → O browser permanecerá aberto por 5 minutos\n");

    // Manter browser aberto para configuração manual
    await page.waitForTimeout(300000); // 5 minutos

  } catch (error) {
    console.error("❌ Erro:", error.message);
  } finally {
    console.log("\n🏁 Fechando browser...");
    await browser.close();
  }
}

main().catch(console.error);
