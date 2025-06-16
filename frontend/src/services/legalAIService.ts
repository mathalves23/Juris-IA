import axios from 'axios';
import { OpenAI } from 'openai';

// Tipos para o serviço de IA Legal
export interface LegalPrompt {
  id: string;
  name: string;
  category: string;
  template: string;
  parameters: string[];
  description: string;
}

export interface ConversationContext {
  id: string;
  messages: ConversationMessage[];
  topic: string;
  legalArea: string;
  relevantLaws: string[];
  clientContext?: ClientContext;
  caseContext?: CaseContext;
}

export interface ConversationMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    confidence: number;
    sources: string[];
    legalReferences: string[];
  };
}

export interface ClientContext {
  name?: string;
  type: 'pessoa_fisica' | 'pessoa_juridica';
  situation?: string;
  previousCases?: string[];
}

export interface CaseContext {
  type: string;
  status: string;
  jurisdiction: string;
  urgency: 'baixa' | 'media' | 'alta';
  deadlines?: string[];
}

export interface LegalKnowledgeBase {
  laws: LegalDocument[];
  jurisprudence: JurisprudenceCase[];
  precedents: LegalPrecedent[];
  templates: DocumentTemplate[];
}

export interface LegalDocument {
  id: string;
  title: string;
  type: 'lei' | 'decreto' | 'portaria' | 'resolucao';
  content: string;
  area: string;
  lastUpdated: Date;
}

export interface JurisprudenceCase {
  id: string;
  court: string;
  decision: string;
  summary: string;
  area: string;
  date: Date;
  relevance: number;
}

// Prompts especializados para direito brasileiro
const LEGAL_PROMPTS: LegalPrompt[] = [
  {
    id: 'draft_contract',
    name: 'Redigir Contrato',
    category: 'Contratos',
    template: `Como advogado especialista em direito contratual, redija um {contract_type} considerando:
    - Partes: {parties}
    - Objeto: {object}
    - Valor: {value}
    - Prazo: {term}
    - Jurisdição: {jurisdiction}
    
    Inclua todas as cláusulas essenciais conforme o Código Civil brasileiro e jurisprudência recente.`,
    parameters: ['contract_type', 'parties', 'object', 'value', 'term', 'jurisdiction'],
    description: 'Gera contratos completos seguindo a legislação brasileira'
  },
  {
    id: 'analyze_contract',
    name: 'Analisar Contrato',
    category: 'Análise',
    template: `Analise o seguinte contrato identificando:
    1. Riscos jurídicos
    2. Cláusulas abusivas ou desequilibradas
    3. Não conformidades com a legislação
    4. Sugestões de melhorias
    
    Contrato: {contract_text}
    
    Base sua análise no CDC, Código Civil e jurisprudência do STJ.`,
    parameters: ['contract_text'],
    description: 'Análise completa de contratos com identificação de riscos'
  },
  {
    id: 'legal_opinion',
    name: 'Parecer Jurídico',
    category: 'Consultoria',
    template: `Elabore um parecer jurídico sobre:
    Questão: {legal_question}
    Área do Direito: {legal_area}
    Fatos: {facts}
    
    Estrutura:
    1. Relatório dos fatos
    2. Fundamentação jurídica
    3. Legislação aplicável
    4. Jurisprudência
    5. Conclusão e recomendações`,
    parameters: ['legal_question', 'legal_area', 'facts'],
    description: 'Pareceres jurídicos fundamentados e estruturados'
  },
  {
    id: 'petition_draft',
    name: 'Petição Inicial',
    category: 'Processual',
    template: `Redija uma petição inicial para:
    Ação: {action_type}
    Autor: {plaintiff}
    Réu: {defendant}
    Causa de Pedir: {cause}
    Pedidos: {requests}
    Comarca: {jurisdiction}
    
    Siga o CPC/2015 e inclua todos os requisitos do art. 319.`,
    parameters: ['action_type', 'plaintiff', 'defendant', 'cause', 'requests', 'jurisdiction'],
    description: 'Petições iniciais conforme CPC/2015'
  },
  {
    id: 'legal_research',
    name: 'Pesquisa Jurídica',
    category: 'Pesquisa',
    template: `Realize uma pesquisa jurídica completa sobre:
    Tema: {topic}
    Área: {area}
    
    Inclua:
    1. Legislação pertinente
    2. Jurisprudência dos tribunais superiores
    3. Doutrina relevante
    4. Precedentes vinculantes
    5. Tendências jurisprudenciais`,
    parameters: ['topic', 'area'],
    description: 'Pesquisa jurídica abrangente com fontes atualizadas'
  }
];

// Áreas do direito brasileiro
const LEGAL_AREAS = [
  'Civil', 'Empresarial', 'Trabalhista', 'Tributário', 'Penal',
  'Administrativo', 'Constitucional', 'Previdenciário', 'Consumidor',
  'Família', 'Sucessões', 'Imobiliário', 'Ambiental', 'Digital'
];

class LegalAIService {
  private openai: OpenAI;
  private knowledgeBase: LegalKnowledgeBase = {
    laws: [],
    jurisprudence: [],
    precedents: [],
    templates: []
  };
  private contexts: Map<string, ConversationContext> = new Map();

  constructor() {
    this.openai = new OpenAI({
      apiKey: process.env.REACT_APP_OPENAI_API_KEY,
      dangerouslyAllowBrowser: true
    });
    this.loadKnowledgeBase();
  }

  // Carregar base de conhecimento jurídico
  private async loadKnowledgeBase(): Promise<void> {
    try {
      const response = await axios.get('/api/legal/knowledge-base');
      this.knowledgeBase = response.data;
    } catch (error) {
      console.error('Erro ao carregar base de conhecimento:', error);
      // Fallback para dados locais se API não estiver disponível
      this.loadLocalKnowledgeBase();
    }
  }

  private loadLocalKnowledgeBase(): void {
    // Base de conhecimento mínima local
    this.knowledgeBase = {
      laws: [
        {
          id: 'cc2002',
          title: 'Código Civil - Lei 10.406/2002',
          type: 'lei',
          content: 'Lei que institui o Código Civil...',
          area: 'Civil',
          lastUpdated: new Date('2002-01-10')
        },
        {
          id: 'cdc',
          title: 'Código de Defesa do Consumidor - Lei 8.078/90',
          type: 'lei',
          content: 'Dispõe sobre a proteção do consumidor...',
          area: 'Consumidor',
          lastUpdated: new Date('1990-09-11')
        }
      ],
      jurisprudence: [],
      precedents: [],
      templates: []
    };
  }

  // Criar nova conversa com contexto
  async createConversation(
    topic: string,
    legalArea: string,
    clientContext?: ClientContext,
    caseContext?: CaseContext
  ): Promise<string> {
    const conversationId = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const context: ConversationContext = {
      id: conversationId,
      messages: [],
      topic,
      legalArea,
      relevantLaws: this.findRelevantLaws(legalArea),
      clientContext,
      caseContext
    };

    // Mensagem de sistema com contexto legal
    const systemMessage: ConversationMessage = {
      id: `msg_${Date.now()}`,
      role: 'system',
      content: this.buildSystemPrompt(context),
      timestamp: new Date()
    };

    context.messages.push(systemMessage);
    this.contexts.set(conversationId, context);

    return conversationId;
  }

  // Construir prompt de sistema especializado
  private buildSystemPrompt(context: ConversationContext): string {
    let prompt = `Você é um assistente jurídico especializado em direito brasileiro, com expertise em ${context.legalArea}.

CONTEXTO LEGAL:
- Área: ${context.legalArea}
- Tópico: ${context.topic}
- Leis Relevantes: ${context.relevantLaws.join(', ')}

INSTRUÇÕES:
1. Sempre cite a legislação brasileira aplicável
2. Mencione jurisprudência relevante quando disponível
3. Forneça respostas práticas e aplicáveis
4. Identifique riscos jurídicos quando pertinente
5. Sugira próximos passos quando apropriado
6. Use linguagem técnica mas acessível

LIMITAÇÕES:
- Não forneça conselhos para atividades ilegais
- Sempre recomende consulta presencial para casos complexos
- Mencione que as informações não substituem análise jurídica completa`;

    if (context.clientContext) {
      prompt += `\n\nCONTEXTO DO CLIENTE:
- Tipo: ${context.clientContext.type === 'pessoa_fisica' ? 'Pessoa Física' : 'Pessoa Jurídica'}
- Situação: ${context.clientContext.situation || 'Não informada'}`;
    }

    if (context.caseContext) {
      prompt += `\n\nCONTEXTO DO CASO:
- Tipo: ${context.caseContext.type}
- Status: ${context.caseContext.status}
- Jurisdição: ${context.caseContext.jurisdiction}
- Urgência: ${context.caseContext.urgency}`;
    }

    return prompt;
  }

  // Encontrar leis relevantes por área
  private findRelevantLaws(area: string): string[] {
    const relevantLaws: { [key: string]: string[] } = {
      'Civil': ['CC/2002', 'CPC/2015'],
      'Empresarial': ['CC/2002', 'Lei 6.404/76', 'Lei 11.101/05'],
      'Trabalhista': ['CLT', 'CF/88 art. 7º'],
      'Tributário': ['CTN', 'CF/88 Títulos VI'],
      'Penal': ['CP', 'CPP'],
      'Consumidor': ['CDC', 'CC/2002'],
      'Família': ['CC/2002 Livro IV', 'ECA'],
      'Previdenciário': ['Lei 8.213/91', 'Lei 8.112/90'],
      'Administrativo': ['Lei 9.784/99', 'Lei 8.666/93'],
      'Constitucional': ['CF/88']
    };

    return relevantLaws[area] || ['CF/88'];
  }

  // Enviar mensagem e receber resposta da IA
  async sendMessage(
    conversationId: string,
    message: string,
    usePrompt?: string,
    promptParams?: { [key: string]: string }
  ): Promise<ConversationMessage> {
    const context = this.contexts.get(conversationId);
    if (!context) {
      throw new Error('Conversa não encontrada');
    }

    // Adicionar mensagem do usuário
    const userMessage: ConversationMessage = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content: usePrompt ? this.formatPrompt(usePrompt, promptParams || {}) : message,
      timestamp: new Date()
    };

    context.messages.push(userMessage);

    // Preparar contexto para IA
    const enrichedContext = await this.enrichContextWithKnowledge(context, message);
    
    // Enviar para OpenAI
    const response = await this.openai.chat.completions.create({
      model: 'gpt-4',
      messages: enrichedContext.messages.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
      temperature: 0.3,
      max_tokens: 2000,
      presence_penalty: 0.1,
      frequency_penalty: 0.1
    });

    const aiResponse = response.choices[0]?.message?.content;
    if (!aiResponse) {
      throw new Error('Erro ao obter resposta da IA');
    }

    // Analisar resposta e extrair metadados
    const metadata = await this.analyzeResponse(aiResponse, context);

    const assistantMessage: ConversationMessage = {
      id: `msg_${Date.now()}_assistant`,
      role: 'assistant',
      content: aiResponse,
      timestamp: new Date(),
      metadata
    };

    context.messages.push(assistantMessage);
    this.contexts.set(conversationId, context);

    // Salvar conversa no backend
    await this.saveConversation(context);

    return assistantMessage;
  }

  // Formatar prompt com parâmetros
  private formatPrompt(promptId: string, params: { [key: string]: string }): string {
    const prompt = LEGAL_PROMPTS.find(p => p.id === promptId);
    if (!prompt) return '';

    let formattedTemplate = prompt.template;
    for (const [key, value] of Object.entries(params)) {
      formattedTemplate = formattedTemplate.replace(new RegExp(`{${key}}`, 'g'), value);
    }

    return formattedTemplate;
  }

  // Enriquecer contexto com base de conhecimento
  private async enrichContextWithKnowledge(
    context: ConversationContext,
    query: string
  ): Promise<ConversationContext> {
    // Buscar jurisprudência relevante
    const relevantJurisprudence = await this.searchJurisprudence(query, context.legalArea);
    
    // Buscar leis aplicáveis
    const applicableLaws = await this.searchLaws(query, context.legalArea);

    // Adicionar conhecimento ao contexto se encontrado
    if (relevantJurisprudence.length > 0 || applicableLaws.length > 0) {
      const knowledgeContext = `
CONHECIMENTO RELEVANTE:

${applicableLaws.length > 0 ? `LEGISLAÇÃO:
${applicableLaws.map(law => `- ${law.title}: ${law.content.substring(0, 200)}...`).join('\n')}` : ''}

${relevantJurisprudence.length > 0 ? `JURISPRUDÊNCIA:
${relevantJurisprudence.map(case_ => `- ${case_.court}: ${case_.summary}`).join('\n')}` : ''}

Com base neste conhecimento, responda à seguinte consulta:`;

      // Adicionar ao contexto
      const knowledgeMessage: ConversationMessage = {
        id: `msg_${Date.now()}_knowledge`,
        role: 'system',
        content: knowledgeContext,
        timestamp: new Date()
      };

      const enrichedContext = { ...context };
      enrichedContext.messages = [...context.messages, knowledgeMessage];
      return enrichedContext;
    }

    return context;
  }

  // Buscar jurisprudência relevante
  private async searchJurisprudence(query: string, area: string): Promise<JurisprudenceCase[]> {
    // Implementar busca semântica na base de jurisprudência
    // Por ora, retorna resultados mockados
    return this.knowledgeBase.jurisprudence
      .filter(case_ => 
        case_.area === area && 
        (case_.summary.toLowerCase().includes(query.toLowerCase()) ||
         case_.decision.toLowerCase().includes(query.toLowerCase()))
      )
      .sort((a, b) => b.relevance - a.relevance)
      .slice(0, 3);
  }

  // Buscar leis aplicáveis
  private async searchLaws(query: string, area: string): Promise<LegalDocument[]> {
    return this.knowledgeBase.laws
      .filter(law => 
        law.area === area && 
        law.content.toLowerCase().includes(query.toLowerCase())
      )
      .slice(0, 2);
  }

  // Analisar resposta e extrair metadados
  private async analyzeResponse(response: string, context: ConversationContext): Promise<any> {
    // Extrair referências legais
    const legalReferences = this.extractLegalReferences(response);
    
    // Calcular confiança baseada no contexto
    const confidence = this.calculateConfidence(response, context);

    // Identificar fontes utilizadas
    const sources = this.identifySources(response);

    return {
      confidence,
      sources,
      legalReferences
    };
  }

  // Extrair referências legais do texto
  private extractLegalReferences(text: string): string[] {
    const references: string[] = [];
    
    // Padrões para identificar referências legais
    const patterns = [
      /Lei\s+\d+[\.\d]*\/\d+/gi,
      /Decreto\s+\d+[\.\d]*\/\d+/gi,
      /Art\.\s*\d+/gi,
      /Artigo\s+\d+/gi,
      /CC\/\d+/gi,
      /CF\/\d+/gi,
      /STJ/gi,
      /STF/gi,
      /TST/gi
    ];

    patterns.forEach(pattern => {
      const matches = text.match(pattern);
      if (matches) {
        references.push(...matches);
      }
    });

    return [...new Set(references)]; // Remove duplicatas
  }

  // Calcular confiança da resposta
  private calculateConfidence(response: string, context: ConversationContext): number {
    let confidence = 0.5; // Base

    // Aumenta confiança se há referências legais
    if (this.extractLegalReferences(response).length > 0) {
      confidence += 0.2;
    }

    // Aumenta confiança se a área é conhecida
    if (LEGAL_AREAS.includes(context.legalArea)) {
      confidence += 0.1;
    }

    // Aumenta confiança se há contexto detalhado
    if (context.clientContext || context.caseContext) {
      confidence += 0.1;
    }

    // Diminui confiança se a resposta é muito curta
    if (response.length < 200) {
      confidence -= 0.1;
    }

    return Math.min(Math.max(confidence, 0), 1);
  }

  // Identificar fontes utilizadas
  private identifySources(response: string): string[] {
    const sources: string[] = [];
    
    if (response.includes('Código Civil') || response.includes('CC/')) {
      sources.push('Código Civil');
    }
    if (response.includes('STJ') || response.includes('Superior Tribunal')) {
      sources.push('STJ');
    }
    if (response.includes('STF') || response.includes('Supremo')) {
      sources.push('STF');
    }
    if (response.includes('CDC') || response.includes('Consumidor')) {
      sources.push('CDC');
    }

    return sources;
  }

  // Salvar conversa no backend
  private async saveConversation(context: ConversationContext): Promise<void> {
    try {
      await axios.post('/api/legal/conversations', {
        id: context.id,
        topic: context.topic,
        legalArea: context.legalArea,
        messages: context.messages.map(msg => ({
          ...msg,
          timestamp: msg.timestamp.toISOString()
        })),
        clientContext: context.clientContext,
        caseContext: context.caseContext
      });
    } catch (error) {
      console.error('Erro ao salvar conversa:', error);
    }
  }

  // Obter histórico de conversas
  async getConversationHistory(userId: string): Promise<ConversationContext[]> {
    try {
      const response = await axios.get(`/api/legal/conversations/user/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Erro ao carregar histórico:', error);
      return [];
    }
  }

  // Obter prompts disponíveis
  getAvailablePrompts(): LegalPrompt[] {
    return LEGAL_PROMPTS;
  }

  // Obter áreas do direito
  getLegalAreas(): string[] {
    return LEGAL_AREAS;
  }

  // Buscar precedentes similares
  async findSimilarPrecedents(query: string, area: string): Promise<LegalPrecedent[]> {
    try {
      const response = await axios.post('/api/legal/precedents/search', {
        query,
        area,
        limit: 5
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar precedentes:', error);
      return [];
    }
  }

  // Gerar resumo da conversa
  async generateConversationSummary(conversationId: string): Promise<string> {
    const context = this.contexts.get(conversationId);
    if (!context) return '';

    const messages = context.messages
      .filter(msg => msg.role !== 'system')
      .map(msg => `${msg.role}: ${msg.content}`)
      .join('\n\n');

    const response = await this.openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [{
        role: 'system',
        content: 'Resuma esta conversa jurídica de forma concisa, destacando os pontos principais discutidos e as conclusões.'
      }, {
        role: 'user',
        content: messages
      }],
      max_tokens: 300
    });

    return response.choices[0]?.message?.content || '';
  }
}

// Interface para precedentes legais
export interface LegalPrecedent {
  id: string;
  title: string;
  court: string;
  decision: string;
  area: string;
  similarity: number;
  date: Date;
}

export default new LegalAIService(); 