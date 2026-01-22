/**
 * Coolify Deploy Script - MedFlow Forks
 *
 * Este script usa Playwright para configurar e fazer deploy
 * do projeto medflow-forks no Coolify.
 *
 * Uso: npx playwright test scripts/coolify-deploy.ts --headed
 */

import { test, expect, Page } from "@playwright/test";

const COOLIFY_URL = "https://coolify.trafegoparaconsultorios.com.br";
const REPO_URL = "https://github.com/nogbrian/medflow-forks";
const PROJECT_NAME = "medflow-forks";

test.describe("Coolify Deploy - MedFlow Forks", () => {
  test.setTimeout(120000); // 2 minutos de timeout

  test("should deploy medflow-forks to Coolify", async ({ page }) => {
    // 1. Navegar para o Coolify
    await page.goto(COOLIFY_URL);
    console.log("Navegando para Coolify...");

    // Aguardar login (se necessário, o usuário fará manualmente)
    await page.waitForURL("**/dashboard**", { timeout: 60000 }).catch(() => {
      console.log("Aguardando login manual...");
    });

    // 2. Verificar se já está logado ou na página de login
    const isLoggedIn = await page.locator('text="Projects"').isVisible().catch(() => false);

    if (!isLoggedIn) {
      console.log("Por favor, faça login manualmente...");
      // Aguardar até que o dashboard esteja visível
      await page.waitForSelector('text="Projects"', { timeout: 120000 });
    }

    console.log("Login detectado, continuando...");

    // 3. Navegar para Projects
    await page.click('text="Projects"');
    await page.waitForLoadState("networkidle");

    // 4. Verificar se o projeto já existe
    const projectExists = await page.locator(`text="${PROJECT_NAME}"`).isVisible().catch(() => false);

    if (projectExists) {
      console.log("Projeto já existe, atualizando...");
      await page.click(`text="${PROJECT_NAME}"`);
    } else {
      console.log("Criando novo projeto...");
      // Clicar em "Add New Project" ou "+"
      await page.click('button:has-text("New"), button:has-text("Add"), [aria-label*="new"], [aria-label*="add"]');
      await page.waitForLoadState("networkidle");
    }

    // 5. Configurar o projeto (se novo)
    if (!projectExists) {
      // Preencher nome do projeto
      const nameInput = page.locator('input[name="name"], input[placeholder*="name"]');
      if (await nameInput.isVisible()) {
        await nameInput.fill(PROJECT_NAME);
      }

      // Selecionar source (GitHub)
      await page.click('text="GitHub", text="Git"').catch(() => {});

      // Preencher URL do repositório
      const repoInput = page.locator('input[name="repository"], input[placeholder*="repository"], input[placeholder*="git"]');
      if (await repoInput.isVisible()) {
        await repoInput.fill(REPO_URL);
      }

      // Selecionar branch
      const branchInput = page.locator('input[name="branch"], select[name="branch"]');
      if (await branchInput.isVisible()) {
        await branchInput.fill("main");
      }
    }

    // 6. Configurar recursos (Resource)
    // Procurar por seção de recursos ou adicionar novo
    const addResourceBtn = page.locator('button:has-text("Add Resource"), button:has-text("New Resource")');
    if (await addResourceBtn.isVisible()) {
      await addResourceBtn.click();

      // Selecionar tipo (Docker Compose ou Dockerfile)
      await page.click('text="Docker Compose"').catch(() => {
        page.click('text="Dockerfile"');
      });
    }

    // 7. Configurar variáveis de ambiente
    const envSection = page.locator('text="Environment", text="Variables"');
    if (await envSection.isVisible()) {
      await envSection.click();

      // Adicionar variáveis essenciais
      const envVars = `
APP_ENV=production
JWT_SECRET=${generateSecret()}
WEBHOOK_SECRET=${generateSecret()}
TWENTY_URL=https://crm.medflow.com.br
CALCOM_URL=https://agenda.medflow.com.br
CHATWOOT_URL=https://inbox.medflow.com.br
      `.trim();

      const envInput = page.locator('textarea[name="env"], textarea[placeholder*="environment"]');
      if (await envInput.isVisible()) {
        await envInput.fill(envVars);
      }
    }

    // 8. Salvar e fazer deploy
    const saveBtn = page.locator('button:has-text("Save"), button:has-text("Deploy"), button[type="submit"]');
    await saveBtn.click();

    console.log("Configuração enviada, iniciando deploy...");

    // 9. Aguardar deploy iniciar
    await page.waitForSelector('text="Deploying", text="Building", text="Running"', {
      timeout: 30000,
    }).catch(() => {
      console.log("Status de deploy não detectado automaticamente");
    });

    // 10. Capturar URL do deploy
    const deployUrl = await page.locator('a[href*="medflow"], text*="medflow"').getAttribute("href").catch(() => null);

    if (deployUrl) {
      console.log(`Deploy URL: ${deployUrl}`);
    }

    console.log("Script concluído! Verifique o status no Coolify.");
  });
});

function generateSecret(): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "";
  for (let i = 0; i < 32; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}
