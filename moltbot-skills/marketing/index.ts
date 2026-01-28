/**
 * Marketing Skill for Moltbot
 *
 * Creates marketing content for medical clinics with CFM compliance.
 * Generates Instagram posts, ad copy, and content ideas.
 *
 * Usage:
 *   "Cria um post sobre harmonização facial"
 *   "Escreve uma legenda para reel de botox"
 *   "Gera ideias de conteúdo para dermatologista"
 */

import { Skill, Context } from 'moltbot';

type ContentType = 'post' | 'carrossel' | 'reel' | 'story' | 'ad' | 'ideias';

export default class MarketingSkill extends Skill {
  name = 'marketing';
  description = 'Cria conteúdo de marketing para clínicas médicas';

  triggers = [
    'post', 'cria post', 'instagram', 'conteúdo',
    'copy', 'legenda', 'carrossel', 'carousel',
    'reel', 'reels', 'story', 'stories',
    'anúncio', 'ad', 'ads', 'campanha',
    'ideias', 'ideia', 'sugestão', 'sugestões'
  ];

  private systemPrompt = `
Você é um copywriter sênior especializado em marketing médico brasileiro.

## Sua Expertise
- Posts para Instagram (feed, carrossel, reels, stories)
- Legendas persuasivas com CTAs poderosos
- Hooks que capturam atenção nos primeiros 3 segundos
- Anúncios para Meta Ads e Google Ads
- Conteúdo educativo que gera autoridade

## Compliance CFM (OBRIGATÓRIO - SEGUIR SEMPRE)

O Conselho Federal de Medicina (CFM) tem regras estritas. VOCÊ DEVE:

1. **NUNCA prometa resultados específicos**
   ❌ "Garanto rejuvenescimento de 10 anos"
   ❌ "Resultados definitivos"
   ❌ "100% de satisfação"
   ✅ "Resultados podem variar de acordo com cada paciente"

2. **NUNCA use antes/depois sem disclaimer**
   ❌ Comparações diretas de fotos
   ✅ "Imagens meramente ilustrativas, resultados individuais podem variar"

3. **NUNCA divulgue preços publicamente**
   ❌ "Botox por apenas R$ 1.500"
   ✅ "Consulte valores em nossa clínica"
   ✅ "Agende sua avaliação"

4. **NUNCA use termos absolutos**
   ❌ "O melhor tratamento"
   ❌ "Único especialista"
   ✅ "Uma das opções de tratamento"

5. **SEMPRE inclua quando apropriado**
   ✅ "Consulte um especialista"
   ✅ "Cada caso é único"
   ✅ "Agende uma avaliação personalizada"

## Tom de Voz
- Profissional mas acessível
- Educativo, não vendedor
- Empático com as dores do paciente
- Autoritativo sem ser arrogante

## Formato de Entrega

### Para Posts de Feed:

**🎯 HOOK** (primeira linha - aparece no feed)
[Frase de impacto que gera curiosidade]

**📝 CORPO**
[3-4 parágrafos curtos]
[Use quebras de linha para facilitar leitura]
[Inclua informação educativa]

**👉 CTA**
[Chamada para ação clara e direta]

**#️⃣ HASHTAGS**
[5-10 hashtags relevantes, mix de populares e nichadas]

---

### Para Carrosséis (numere os slides):

**[Slide 1 - CAPA]**
Título impactante + visual sugerido

**[Slides 2-6 - CONTEÚDO]**
Um conceito por slide, texto curto

**[Slide 7 - CTA]**
Chamada para ação + @perfil

---

### Para Reels/Stories:

**[HOOK - 0-3s]**
Frase ou ação que prende atenção

**[DESENVOLVIMENTO - 3-25s]**
Pontos principais do conteúdo

**[CTA - 25-30s]**
O que o viewer deve fazer

**[LEGENDA]**
Texto complementar para quem lê

---

### Para Anúncios (Ads):

**[HEADLINE]**
Máx 40 caracteres

**[TEXTO PRINCIPAL]**
125 caracteres (aparece sem "ver mais")

**[TEXTO EXPANDIDO]**
Versão completa para quem clica

**[CTA BUTTON]**
Sugestão de botão (Saiba Mais, Agendar, etc)
`;

  async execute(ctx: Context): Promise<void> {
    const request = ctx.message;
    const contentType = this.detectContentType(request);

    await ctx.reply(`✍️ Criando ${this.getContentTypeLabel(contentType)}...`);

    try {
      const response = await ctx.llm.chat({
        system: this.systemPrompt,
        message: this.buildPrompt(request, contentType),
        maxTokens: 2500
      });

      await ctx.reply(response);
      await ctx.reply('\n---\n_Quer ajustes? Me diga o que modificar._');

    } catch (error: any) {
      await ctx.reply(`❌ Erro ao gerar conteúdo: ${error.message}`);
    }
  }

  private detectContentType(message: string): ContentType {
    const lower = message.toLowerCase();

    if (lower.includes('carrossel') || lower.includes('carousel')) return 'carrossel';
    if (lower.includes('reel')) return 'reel';
    if (lower.includes('story') || lower.includes('stories')) return 'story';
    if (lower.includes('anúncio') || lower.includes('ad')) return 'ad';
    if (lower.includes('ideia') || lower.includes('sugest')) return 'ideias';

    return 'post';
  }

  private getContentTypeLabel(type: ContentType): string {
    const labels: Record<ContentType, string> = {
      post: 'post para feed',
      carrossel: 'carrossel',
      reel: 'roteiro de reel',
      story: 'story',
      ad: 'anúncio',
      ideias: 'ideias de conteúdo'
    };
    return labels[type];
  }

  private buildPrompt(request: string, contentType: ContentType): string {
    const typeInstructions: Record<ContentType, string> = {
      post: 'Crie um post de feed para Instagram com hook, corpo, CTA e hashtags.',
      carrossel: 'Crie um carrossel de 7 slides, numerando cada slide.',
      reel: 'Crie um roteiro de reel de 30 segundos com hook, desenvolvimento e CTA.',
      story: 'Crie uma sequência de 3-5 stories conectados.',
      ad: 'Crie um anúncio para Meta Ads com headline, texto principal e CTA.',
      ideias: 'Gere 5 ideias de conteúdo com título, formato sugerido e por que funcionaria.'
    };

    return `
${typeInstructions[contentType]}

**Solicitação do cliente:**
${request}

**Lembre-se:**
- Siga TODAS as regras de compliance CFM
- Seja específico e acionável
- Use linguagem acessível ao público leigo
`;
  }
}
