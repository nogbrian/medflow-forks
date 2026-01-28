/**
 * DevOps Skill for Moltbot
 *
 * Manages deployments, service status, logs, and rollbacks.
 * Integrates with Coolify for deployment orchestration.
 *
 * Usage:
 *   "deploy" - Push and deploy to production
 *   "status" - Show service health
 *   "logs moltbot" - Show recent logs
 *   "restart crabwalk" - Restart a service
 *   "rollback" - Revert last deployment
 */

import { Skill, Context } from 'moltbot';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface ServiceStatus {
  name: string;
  status: string;
  isUp: boolean;
}

export default class DevOpsSkill extends Skill {
  name = 'devops';
  description = 'Gerencia deploys, logs e status de serviços';

  triggers = [
    'deploy', 'faz deploy', 'publica', 'publicar', 'push',
    'restart', 'reinicia', 'reiniciar',
    'logs', 'log', 'ver logs', 'mostra logs',
    'status', 'estado', 'health', 'saúde',
    'rollback', 'reverter', 'desfazer'
  ];

  private workspaceRoot = process.env.CLAUDE_WORKSPACE || '/home/deploy/workspaces/medflow';
  private coolifyUrl = process.env.COOLIFY_API_URL || '';
  private coolifyToken = process.env.COOLIFY_API_TOKEN || '';

  // Service configurations
  private services = {
    moltbot: { type: 'systemd', name: 'moltbot' },
    cloudflared: { type: 'systemd', name: 'cloudflared' },
    crabwalk: { type: 'docker', name: 'crabwalk' },
    'medflow-api': { type: 'docker', name: 'medflow-api' },
    postgres: { type: 'docker', name: 'postgres' },
    redis: { type: 'docker', name: 'redis' },
    fail2ban: { type: 'systemd', name: 'fail2ban' },
  };

  async execute(ctx: Context): Promise<void> {
    const message = ctx.message.toLowerCase();

    try {
      if (this.matchesAny(message, ['deploy', 'publica', 'push'])) {
        await this.deploy(ctx);
      } else if (this.matchesAny(message, ['restart', 'reinicia'])) {
        await this.restart(ctx, message);
      } else if (this.matchesAny(message, ['logs', 'log'])) {
        await this.showLogs(ctx, message);
      } else if (this.matchesAny(message, ['status', 'estado', 'health', 'saúde'])) {
        await this.showStatus(ctx);
      } else if (this.matchesAny(message, ['rollback', 'reverter', 'desfazer'])) {
        await this.rollback(ctx);
      } else {
        await this.showHelp(ctx);
      }
    } catch (error: any) {
      await ctx.reply(`❌ **Erro:**\n\`\`\`\n${error.message}\n\`\`\``);
    }
  }

  private matchesAny(text: string, keywords: string[]): boolean {
    return keywords.some(k => text.includes(k));
  }

  // ==================== DEPLOY ====================

  private async deploy(ctx: Context): Promise<void> {
    await ctx.reply('🚀 **Iniciando deploy...**');

    // Step 1: Git status check
    const { stdout: gitStatus } = await execAsync('git status --porcelain', { cwd: this.workspaceRoot });
    if (gitStatus.trim()) {
      await ctx.reply('⚠️ Existem mudanças não commitadas. Commitando automaticamente...');
      await execAsync('git add -A && git commit -m "chore: auto-commit before deploy"', { cwd: this.workspaceRoot });
    }

    // Step 2: Git push
    await ctx.reply('📤 Fazendo push para origin/main...');
    try {
      const { stdout: pushOut } = await execAsync('git push origin main 2>&1', { cwd: this.workspaceRoot });
      if (pushOut.includes('Everything up-to-date')) {
        await ctx.reply('ℹ️ Repositório já está atualizado.');
      } else {
        await ctx.reply('✅ Push realizado com sucesso.');
      }
    } catch (e: any) {
      if (!e.message.includes('Everything up-to-date')) {
        throw new Error(`Git push falhou: ${e.message}`);
      }
    }

    // Step 3: Trigger Coolify (if configured)
    if (this.coolifyUrl && this.coolifyToken) {
      await ctx.reply('🔄 Triggerando deploy no Coolify...');

      try {
        const response = await fetch(`${this.coolifyUrl}/api/v1/applications/medflow-forks/restart`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.coolifyToken}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Coolify API error: ${response.status} - ${errorText}`);
        }

        await ctx.reply('✅ Deploy iniciado no Coolify.');
      } catch (e: any) {
        await ctx.reply(`⚠️ Coolify não disponível: ${e.message}\nContinuando sem Coolify...`);
      }
    }

    // Step 4: Wait and verify
    await ctx.reply('⏳ Aguardando serviços...');
    await this.sleep(15000);

    // Step 5: Check status
    const status = await this.getServiceStatus('medflow-api');

    if (status.isUp) {
      await ctx.reply('✅ **Deploy concluído com sucesso!**\n\n🟢 Aplicação rodando em produção.');
    } else {
      await ctx.reply(`⚠️ **Deploy finalizado, verificar status:**\n\`${status.status}\``);
    }
  }

  // ==================== RESTART ====================

  private async restart(ctx: Context, message: string): Promise<void> {
    const serviceName = this.extractServiceName(message);

    if (!serviceName) {
      await ctx.reply('🤔 Qual serviço deseja reiniciar?\n\nDisponíveis: `moltbot`, `crabwalk`, `cloudflared`, `medflow-api`');
      return;
    }

    const service = this.services[serviceName as keyof typeof this.services];
    if (!service) {
      await ctx.reply(`❌ Serviço \`${serviceName}\` não reconhecido.`);
      return;
    }

    await ctx.reply(`🔄 Reiniciando **${serviceName}**...`);

    if (service.type === 'systemd') {
      await execAsync(`sudo systemctl restart ${service.name}`);
    } else if (service.type === 'docker') {
      await execAsync(`docker restart ${service.name}`);
    }

    await this.sleep(3000);

    const status = await this.getServiceStatus(serviceName);
    if (status.isUp) {
      await ctx.reply(`✅ **${serviceName}** reiniciado com sucesso!`);
    } else {
      await ctx.reply(`⚠️ **${serviceName}** pode ter problemas: \`${status.status}\``);
    }
  }

  // ==================== LOGS ====================

  private async showLogs(ctx: Context, message: string, lines: number = 50): Promise<void> {
    const serviceName = this.extractServiceName(message) || 'moltbot';

    await ctx.reply(`📋 Buscando logs de **${serviceName}**...`);

    const service = this.services[serviceName as keyof typeof this.services];
    if (!service) {
      await ctx.reply(`❌ Serviço \`${serviceName}\` não reconhecido.`);
      return;
    }

    let logs: string;

    try {
      if (service.type === 'systemd') {
        const { stdout } = await execAsync(`journalctl -u ${service.name} --no-pager -n ${lines} --output=short`);
        logs = stdout;
      } else {
        const { stdout } = await execAsync(`docker logs --tail ${lines} ${service.name} 2>&1`);
        logs = stdout;
      }
    } catch (e: any) {
      logs = `Erro ao obter logs: ${e.message}`;
    }

    // Truncate if too long for Telegram
    const maxLen = 3500;
    if (logs.length > maxLen) {
      logs = '...(truncado)\n\n' + logs.slice(-maxLen);
    }

    // Escape markdown
    logs = logs.replace(/[`]/g, "'");

    await ctx.reply(`📋 **Logs de ${serviceName}** (últimas ${lines} linhas):\n\`\`\`\n${logs}\n\`\`\``);
  }

  // ==================== STATUS ====================

  private async showStatus(ctx: Context): Promise<void> {
    await ctx.reply('📊 **Verificando status dos serviços...**');

    const checks = [
      { name: 'moltbot', label: 'Moltbot Gateway' },
      { name: 'cloudflared', label: 'Cloudflare Tunnel' },
      { name: 'crabwalk', label: 'Crabwalk Dashboard' },
      { name: 'fail2ban', label: 'Fail2ban' },
    ];

    let statusMsg = '📊 **Status dos Serviços**\n\n';

    for (const check of checks) {
      const status = await this.getServiceStatus(check.name);
      const icon = status.isUp ? '✅' : '❌';
      statusMsg += `${icon} **${check.label}:** ${status.status}\n`;
    }

    // System resources
    statusMsg += '\n**📈 Recursos do Sistema**\n';

    try {
      const { stdout: disk } = await execAsync("df -h / | awk 'NR==2 {print $5}'");
      statusMsg += `💾 Disco: ${disk.trim()} usado\n`;
    } catch {}

    try {
      const { stdout: mem } = await execAsync("free -h | awk 'NR==2 {printf \"%.1f/%.1fGB\", $3, $2}'");
      statusMsg += `🧠 Memória: ${mem.trim()}\n`;
    } catch {}

    try {
      const { stdout: load } = await execAsync("uptime | awk -F'load average:' '{print $2}' | cut -d, -f1");
      statusMsg += `⚡ Load: ${load.trim()}\n`;
    } catch {}

    // Git status
    try {
      const { stdout: commit } = await execAsync('git rev-parse --short HEAD', { cwd: this.workspaceRoot });
      const { stdout: branch } = await execAsync('git branch --show-current', { cwd: this.workspaceRoot });
      statusMsg += `\n**🔗 Git:** \`${branch.trim()}\` @ \`${commit.trim()}\``;
    } catch {}

    await ctx.reply(statusMsg);
  }

  // ==================== ROLLBACK ====================

  private async rollback(ctx: Context): Promise<void> {
    await ctx.reply('⏪ **Iniciando rollback...**');

    // Get current and previous commit
    const { stdout: currentCommit } = await execAsync('git rev-parse --short HEAD', { cwd: this.workspaceRoot });
    const { stdout: prevCommit } = await execAsync('git rev-parse --short HEAD~1', { cwd: this.workspaceRoot });

    await ctx.reply(`📌 Revertendo de \`${currentCommit.trim()}\` para \`${prevCommit.trim()}\``);

    // Revert
    try {
      await execAsync('git revert HEAD --no-edit', { cwd: this.workspaceRoot });
      await ctx.reply('✅ Commit de revert criado.');
    } catch (e: any) {
      throw new Error(`Falha no revert: ${e.message}`);
    }

    // Deploy
    await this.deploy(ctx);
  }

  // ==================== HELPERS ====================

  private async showHelp(ctx: Context): Promise<void> {
    await ctx.reply(`🛠️ **DevOps Commands**

**Deploy:**
• \`deploy\` - Push e deploy para produção

**Serviços:**
• \`status\` - Ver status de todos os serviços
• \`restart <serviço>\` - Reiniciar um serviço
• \`logs <serviço>\` - Ver logs recentes

**Rollback:**
• \`rollback\` - Reverter último deploy

**Serviços disponíveis:**
moltbot, crabwalk, cloudflared, medflow-api`);
  }

  private extractServiceName(message: string): string | null {
    const serviceNames = Object.keys(this.services);
    for (const name of serviceNames) {
      if (message.toLowerCase().includes(name)) {
        return name;
      }
    }
    return null;
  }

  private async getServiceStatus(serviceName: string): Promise<ServiceStatus> {
    const service = this.services[serviceName as keyof typeof this.services];

    if (!service) {
      return { name: serviceName, status: 'unknown', isUp: false };
    }

    try {
      if (service.type === 'systemd') {
        const { stdout } = await execAsync(`systemctl is-active ${service.name}`);
        const status = stdout.trim();
        return {
          name: serviceName,
          status,
          isUp: status === 'active'
        };
      } else {
        const { stdout } = await execAsync(`docker ps --filter name=${service.name} --format "{{.Status}}"`);
        const status = stdout.trim() || 'not running';
        return {
          name: serviceName,
          status,
          isUp: status.toLowerCase().includes('up')
        };
      }
    } catch {
      return { name: serviceName, status: 'error', isUp: false };
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
