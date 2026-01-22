#!/usr/bin/env node
/**
 * Coolify Auto Deploy - MedFlow Forks
 *
 * Espera login manual e depois configura o deploy automaticamente.
 */

import { chromium } from "playwright";

const COOLIFY_URL = "https://coolify.trafegoparaconsultorios.com.br";
const REPO_URL = "https://github.com/nogbrian/medflow-forks";
const PROJECT_NAME = "medflow-forks";

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitForLogin(page) {
  console.log("\n🔐 AGUARDANDO LOGIN...");
  console.log("   → Faça login no Coolify");
  console.log("   → Eu vou detectar automaticamente quando você logar\n");

  // Esperar até sair da página de login
  while (true) {
    const url = page.url();
    const content = await page.content();

    // Verificar se está logado (não está mais na página de login)
    const isLoginPage = url.includes("/login") ||
                        content.includes('type="password"') ||
                        content.includes("Sign in") ||
                        content.includes("Log in");

    const isLoggedIn = content.includes("Projects") ||
                       content.includes("Servers") ||
                       content.includes("Dashboard") ||
                       url.includes("/project");

    if (isLoggedIn && !isLoginPage) {
      console.log("✅ Login detectado!\n");
      return true;
    }

    await sleep(2000);
  }
}

async function findAndClick(page, selectors, description) {
  for (const selector of selectors) {
    try {
      const element = await page.$(selector);
      if (element && await element.isVisible()) {
        console.log(`   → Clicando: ${description}`);
        await element.click();
        await sleep(1000);
        return true;
      }
    } catch (e) {
      // Continuar tentando
    }
  }
  return false;
}

async function fillInput(page, selectors, value, description) {
  for (const selector of selectors) {
    try {
      const element = await page.$(selector);
      if (element && await element.isVisible()) {
        console.log(`   → Preenchendo: ${description} = ${value}`);
        await element.fill(value);
        await sleep(500);
        return true;
      }
    } catch (e) {
      // Continuar tentando
    }
  }
  return false;
}

async function takeScreenshot(page, name) {
  const path = `./screenshots/${name}-${Date.now()}.png`;
  await page.screenshot({ path, fullPage: true });
  console.log(`   📸 Screenshot: ${path}`);
}

async function main() {
  console.log("╔══════════════════════════════════════════════════════════════╗");
  console.log("║      🚀 MedFlow Forks - Auto Deploy no Coolify               ║");
  console.log("╚══════════════════════════════════════════════════════════════╝\n");

  // Criar pasta de screenshots
  const fs = await import("fs");
  if (!fs.existsSync("./screenshots")) {
    fs.mkdirSync("./screenshots");
  }

  const browser = await chromium.launch({
    headless: false,
    slowMo: 100,
  });

  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
  });

  const page = await context.newPage();

  try {
    // 1. Abrir Coolify
    console.log("📡 Abrindo Coolify...");
    await page.goto(COOLIFY_URL);
    await sleep(2000);

    // 2. Aguardar login
    await waitForLogin(page);
    await sleep(2000);
    await takeScreenshot(page, "01-logged-in");

    // 3. Navegar para Projects
    console.log("📁 Navegando para Projects...");

    // Tentar clicar em Projects no menu
    const projectsClicked = await findAndClick(page, [
      'a[href*="project"]',
      'text=Projects',
      '[data-testid="projects"]',
      'nav >> text=Projects',
      'aside >> text=Projects',
      '.sidebar >> text=Projects',
    ], "Projects");

    if (!projectsClicked) {
      // Tentar navegar diretamente
      await page.goto(COOLIFY_URL + "/projects");
    }

    await sleep(2000);
    await takeScreenshot(page, "02-projects-page");

    // 4. Verificar se projeto existe ou criar novo
    console.log(`🔍 Procurando projeto "${PROJECT_NAME}"...`);

    const projectLink = await page.$(`a:has-text("${PROJECT_NAME}"), text="${PROJECT_NAME}"`);

    if (projectLink) {
      console.log("📦 Projeto encontrado! Abrindo...");
      await projectLink.click();
      await sleep(2000);
    } else {
      console.log("🆕 Criando novo projeto...");

      // Clicar em New/Add Project
      await findAndClick(page, [
        'button:has-text("New")',
        'button:has-text("Add")',
        'button:has-text("Create")',
        'a:has-text("New")',
        '[data-testid="new-project"]',
        'button >> svg', // Botão com ícone +
      ], "New Project");

      await sleep(2000);
      await takeScreenshot(page, "03-new-project-form");

      // Preencher nome do projeto
      await fillInput(page, [
        'input[name="name"]',
        'input[placeholder*="Name"]',
        'input#name',
        'input[type="text"]:first-of-type',
      ], PROJECT_NAME, "Nome do projeto");

      // Preencher descrição (opcional)
      await fillInput(page, [
        'textarea[name="description"]',
        'input[name="description"]',
        'textarea[placeholder*="Description"]',
      ], "Plataforma unificada: Twenty CRM + Cal.com + Chatwoot com agentes de IA", "Descrição");

      // Salvar projeto
      await findAndClick(page, [
        'button:has-text("Save")',
        'button:has-text("Create")',
        'button:has-text("Continue")',
        'button[type="submit"]',
      ], "Salvar projeto");

      await sleep(3000);
      await takeScreenshot(page, "04-project-created");
    }

    // 5. Adicionar Resource
    console.log("\n🔧 Configurando Resource...");

    // Procurar botão de adicionar resource
    await findAndClick(page, [
      'button:has-text("New Resource")',
      'button:has-text("Add Resource")',
      'button:has-text("+ New")',
      'a:has-text("New Resource")',
      '[data-testid="add-resource"]',
    ], "Add Resource");

    await sleep(2000);
    await takeScreenshot(page, "05-resource-options");

    // Selecionar Public Repository
    console.log("   → Selecionando Public Repository...");
    await findAndClick(page, [
      'text=Public Repository',
      'button:has-text("Public")',
      '[data-testid="public-repository"]',
      'div:has-text("Public Repository")',
    ], "Public Repository");

    await sleep(2000);
    await takeScreenshot(page, "06-public-repo-form");

    // Preencher URL do repositório
    console.log("   → Configurando repositório...");
    await fillInput(page, [
      'input[name="repository_url"]',
      'input[placeholder*="repository"]',
      'input[placeholder*="github"]',
      'input[placeholder*="https://"]',
      'input[type="url"]',
    ], REPO_URL, "Repository URL");

    await sleep(1000);

    // Preencher branch
    await fillInput(page, [
      'input[name="branch"]',
      'input[placeholder*="branch"]',
      'input[placeholder*="main"]',
    ], "main", "Branch");

    await sleep(1000);
    await takeScreenshot(page, "07-repo-configured");

    // Clicar em Check/Continue para verificar repo
    await findAndClick(page, [
      'button:has-text("Check")',
      'button:has-text("Continue")',
      'button:has-text("Next")',
      'button:has-text("Validate")',
    ], "Check Repository");

    await sleep(3000);
    await takeScreenshot(page, "08-repo-checked");

    // 6. Selecionar Build Pack (Docker Compose)
    console.log("   → Selecionando Build Pack...");
    await findAndClick(page, [
      'text=Docker Compose',
      'button:has-text("Docker Compose")',
      '[data-testid="docker-compose"]',
      'div:has-text("Docker Compose"):not(:has(*))',
    ], "Docker Compose");

    await sleep(2000);
    await takeScreenshot(page, "09-build-pack-selected");

    // Continuar
    await findAndClick(page, [
      'button:has-text("Continue")',
      'button:has-text("Next")',
      'button:has-text("Save")',
    ], "Continue");

    await sleep(3000);
    await takeScreenshot(page, "10-resource-configured");

    // 7. Configurar variáveis de ambiente (se página existir)
    console.log("\n⚙️ Configurando variáveis de ambiente...");

    const envVars = `APP_ENV=production
JWT_SECRET=mf${Date.now()}secret${Math.random().toString(36).substring(7)}
WEBHOOK_SECRET=wh${Date.now()}hook${Math.random().toString(36).substring(7)}
NEXT_PUBLIC_API_URL=/api
TWENTY_API_URL=http://twenty:3000
CALCOM_API_URL=http://calcom:3000
CHATWOOT_API_URL=http://chatwoot:3000`;

    // Procurar seção de Environment
    await findAndClick(page, [
      'text=Environment',
      'a:has-text("Environment")',
      'button:has-text("Environment")',
      '[data-testid="environment"]',
    ], "Environment section");

    await sleep(2000);

    // Preencher variáveis
    await fillInput(page, [
      'textarea[name="env"]',
      'textarea[placeholder*="environment"]',
      'textarea[placeholder*="KEY=value"]',
      '.env-editor textarea',
    ], envVars, "Environment Variables");

    await sleep(1000);
    await takeScreenshot(page, "11-env-vars");

    // Salvar
    await findAndClick(page, [
      'button:has-text("Save")',
      'button[type="submit"]',
    ], "Save Env Vars");

    await sleep(2000);

    // 8. Fazer Deploy
    console.log("\n🚀 INICIANDO DEPLOY...");

    await findAndClick(page, [
      'button:has-text("Deploy")',
      'button:has-text("Start")',
      'button:has-text("Build")',
      '[data-testid="deploy"]',
    ], "Deploy");

    await sleep(3000);
    await takeScreenshot(page, "12-deploy-started");

    console.log("\n╔══════════════════════════════════════════════════════════════╗");
    console.log("║  ✅ CONFIGURAÇÃO COMPLETA!                                   ║");
    console.log("╠══════════════════════════════════════════════════════════════╣");
    console.log("║                                                              ║");
    console.log("║  O deploy foi iniciado no Coolify.                           ║");
    console.log("║  Acompanhe o progresso no painel.                            ║");
    console.log("║                                                              ║");
    console.log("║  Screenshots salvos em: ./screenshots/                       ║");
    console.log("║                                                              ║");
    console.log("╚══════════════════════════════════════════════════════════════╝\n");

    // Manter browser aberto para verificação
    console.log("⏳ Browser permanecerá aberto por 2 minutos para verificação...");
    await sleep(120000);

  } catch (error) {
    console.error("\n❌ Erro:", error.message);
    await takeScreenshot(page, "error");

    console.log("\n⏳ Browser permanecerá aberto para debug...");
    await sleep(300000); // 5 minutos
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
