/**
 * Claude Code Skill for Moltbot
 *
 * Spawns Claude Code CLI as a subprocess to execute development tasks.
 * Enables natural language coding requests via Telegram/WhatsApp.
 *
 * Usage:
 *   "Implementa validação de CPF no cadastro"
 *   "Corrige o bug no endpoint de agendamento"
 *   "Adiciona testes para o módulo de autenticação"
 */

import { Skill, Context } from 'moltbot';
import { spawn } from 'child_process';

interface ClaudeCodeResult {
  success: boolean;
  filesModified: string[];
  testsRun: boolean;
  testsPassed: boolean;
  commitHash: string | null;
  summary: string;
  error?: string;
}

export default class ClaudeCodeSkill extends Skill {
  name = 'claude-code';
  description = 'Executa tarefas de desenvolvimento usando Claude Code CLI';

  triggers = [
    'implementa', 'implemente', 'cria', 'crie', 'adiciona', 'adicione',
    'corrige', 'corrija', 'fix', 'bug', 'refatora', 'refatore',
    'escreve código', 'desenvolve', 'desenvolva', 'código para',
    'feature', 'funcionalidade', 'endpoint', 'componente',
    'teste', 'testa', 'unit test'
  ];

  private workspaceRoot = process.env.CLAUDE_WORKSPACE || '/home/deploy/workspaces/medflow';
  private timeout = parseInt(process.env.CLAUDE_TIMEOUT || '600') * 1000; // 10 min default

  async execute(ctx: Context): Promise<void> {
    const task = ctx.message;

    // Notificar início
    await ctx.reply('🔧 **Iniciando Claude Code...**\n\n_Isso pode levar alguns minutos dependendo da complexidade._');

    try {
      // Executar Claude Code
      const result = await this.runClaudeCode(task, ctx);

      // Formatar e enviar resultado
      await ctx.reply(this.formatResult(result));

    } catch (error: any) {
      await ctx.reply(`❌ **Erro no Claude Code:**\n\`\`\`\n${error.message}\n\`\`\``);
    }
  }

  private async runClaudeCode(task: string, ctx: Context): Promise<ClaudeCodeResult> {
    return new Promise((resolve, reject) => {
      const prompt = this.buildPrompt(task);

      const claude = spawn('claude', [
        '--print',
        '--dangerously-skip-permissions',
        '-p', prompt
      ], {
        cwd: this.workspaceRoot,
        env: {
          ...process.env,
          ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
          HOME: process.env.HOME,
          PATH: process.env.PATH
        },
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';
      let lastUpdate = Date.now();
      const updateInterval = 8000; // 8 seconds between updates

      // Coletar output
      claude.stdout?.on('data', (data: Buffer) => {
        const text = data.toString();
        stdout += text;

        // Enviar updates de progresso (throttled)
        if (Date.now() - lastUpdate > updateInterval) {
          const progressMsg = this.extractProgress(text);
          if (progressMsg) {
            ctx.reply(`⏳ ${progressMsg}`);
          }
          lastUpdate = Date.now();
        }
      });

      claude.stderr?.on('data', (data: Buffer) => {
        stderr += data.toString();
      });

      claude.on('close', (code: number | null) => {
        if (code === 0) {
          resolve(this.parseOutput(stdout));
        } else {
          reject(new Error(stderr || `Claude Code exited with code ${code}`));
        }
      });

      claude.on('error', (err: Error) => {
        reject(new Error(`Failed to start Claude Code: ${err.message}`));
      });

      // Timeout
      const timeoutId = setTimeout(() => {
        claude.kill('SIGTERM');
        reject(new Error(`Timeout: tarefa excedeu ${this.timeout / 1000 / 60} minutos`));
      }, this.timeout);

      claude.on('close', () => clearTimeout(timeoutId));
    });
  }

  private buildPrompt(task: string): string {
    return `
Você está no repositório MedFlow em ${this.workspaceRoot}.

## Tarefa Solicitada
${task}

## Contexto do Projeto
- Stack: FastAPI (Python) + Next.js (TypeScript)
- Backend em apps/api/
- Frontend em frontend/ ou apps/web/
- Testes em tests/ ou __tests__/

## Instruções Obrigatórias

1. **Antes de codificar**: Leia e entenda o código existente relacionado
2. **Padrões do projeto**:
   - TypeScript strict mode
   - Python com type hints e Pydantic
   - async/await para operações I/O
   - Docstrings descritivas
3. **Testes**: Adicione ou atualize testes quando apropriado
4. **Commit**: Faça um commit atômico com mensagem descritiva
   - Formato: "feat|fix|refactor|test|docs: descrição"
   - NÃO inclua "Claude" na mensagem de commit
5. **NÃO faça push**: O push será feito pelo skill de deploy
6. **Segurança**: Nunca hardcode secrets, use variáveis de ambiente

## Formato de Resposta

Ao finalizar, SEMPRE inclua um bloco de resumo no formato exato:

\`\`\`
FILES_MODIFIED: [arquivo1.ts, arquivo2.py]
TESTS_RUN: true
TESTS_PASSED: true
COMMIT_HASH: abc1234
SUMMARY: Implementei a validação de CPF com regex e testes unitários.
\`\`\`
`;
  }

  private extractProgress(text: string): string | null {
    const lines = text.split('\n').filter(l => l.trim());
    const lastLine = lines[lines.length - 1];

    if (!lastLine || lastLine.length > 150) return null;

    // Detectar ações comuns do Claude Code
    if (lastLine.includes('Reading')) return `Lendo ${this.extractFilename(lastLine)}...`;
    if (lastLine.includes('Writing')) return `Escrevendo ${this.extractFilename(lastLine)}...`;
    if (lastLine.includes('Running')) return 'Executando comando...';
    if (lastLine.includes('Test')) return 'Rodando testes...';
    if (lastLine.includes('Commit')) return 'Criando commit...';

    return null;
  }

  private extractFilename(text: string): string {
    const match = text.match(/[\/\w-]+\.\w+/);
    return match ? match[0].split('/').pop() || 'arquivo' : 'arquivo';
  }

  private parseOutput(output: string): ClaudeCodeResult {
    const result: ClaudeCodeResult = {
      success: true,
      filesModified: [],
      testsRun: false,
      testsPassed: false,
      commitHash: null,
      summary: ''
    };

    // Extrair campos estruturados
    const filesMatch = output.match(/FILES_MODIFIED:\s*\[([^\]]*)\]/);
    if (filesMatch) {
      result.filesModified = filesMatch[1]
        .split(',')
        .map(f => f.trim().replace(/['"]/g, ''))
        .filter(Boolean);
    }

    const testsRunMatch = output.match(/TESTS_RUN:\s*(true|false)/i);
    if (testsRunMatch) {
      result.testsRun = testsRunMatch[1].toLowerCase() === 'true';
    }

    const testsPassedMatch = output.match(/TESTS_PASSED:\s*(true|false)/i);
    if (testsPassedMatch) {
      result.testsPassed = testsPassedMatch[1].toLowerCase() === 'true';
    }

    const commitMatch = output.match(/COMMIT_HASH:\s*([a-f0-9]{7,40}|null|none)/i);
    if (commitMatch && !['null', 'none'].includes(commitMatch[1].toLowerCase())) {
      result.commitHash = commitMatch[1];
    }

    const summaryMatch = output.match(/SUMMARY:\s*(.+?)(?:\n```|$)/s);
    if (summaryMatch) {
      result.summary = summaryMatch[1].trim();
    } else {
      // Fallback: últimas linhas úteis do output
      const lines = output.trim().split('\n').filter(l =>
        l.trim() &&
        !l.includes('FILES_MODIFIED') &&
        !l.includes('TESTS_') &&
        !l.includes('COMMIT_HASH')
      );
      result.summary = lines.slice(-3).join('\n');
    }

    return result;
  }

  private formatResult(result: ClaudeCodeResult): string {
    let msg = result.success
      ? '✅ **Tarefa concluída!**\n\n'
      : '⚠️ **Tarefa parcialmente concluída**\n\n';

    if (result.filesModified.length > 0) {
      msg += '**📁 Arquivos modificados:**\n';
      msg += result.filesModified.map(f => `• \`${f}\``).join('\n');
      msg += '\n\n';
    }

    if (result.testsRun) {
      msg += result.testsPassed
        ? '✅ **Testes:** Passando\n'
        : '❌ **Testes:** Alguns falharam\n';
    }

    if (result.commitHash) {
      msg += `\n🔗 **Commit:** \`${result.commitHash}\`\n`;
    }

    if (result.summary) {
      msg += `\n**📝 Resumo:**\n${result.summary}\n`;
    }

    msg += '\n---\n';
    msg += '_Responda **"deploy"** para publicar ou **"logs"** para ver detalhes._';

    return msg;
  }
}
