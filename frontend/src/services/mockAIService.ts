// Serviço de IA Mock para funcionar offline
export interface MockAIResponse {
  id: string;
  content: string;
  type: 'generation' | 'analysis' | 'summary';
  confidence: number;
  timestamp: Date;
  sources: string[];
  legalReferences: string[];
}

export interface DocumentAnalysis {
  risks: string[];
  suggestions: string[];
  compliance: string[];
  score: number;
}

export interface ContractAnalysis {
  clauses: Array<{
    type: string;
    content: string;
    risk: 'baixo' | 'medio' | 'alto';
    suggestion: string;
  }>;
  overallRisk: 'baixo' | 'medio' | 'alto';
  recommendations: string[];
}

class MockAIService {
  private responseDelay = 1500; // Simular delay de rede

  // Templates de respostas jurídicas
  private templates = {
    contract_analysis: [
      "Com base na análise do contrato apresentado, identifiquei os seguintes pontos relevantes:",
      "Após análise detalhada do documento contratual, observo:",
      "A revisão jurídica do contrato revela aspectos importantes:",
    ],
    legal_opinion: [
      "Considerando a questão jurídica apresentada e a legislação brasileira aplicável:",
      "Com fundamento na doutrina e jurisprudência pátrias:",
      "À luz do ordenamento jurídico brasileiro:",
    ],
    document_generation: [
      "Elaborei o documento jurídico solicitado conforme as especificações:",
      "O documento foi redigido observando as normas técnicas e legais:",
      "Segue a redação do documento jurídico solicitado:",
    ]
  };

  private legalReferences = [
    'Art. 421 do Código Civil',
    'Art. 422 do Código Civil', 
    'Lei 8.078/90 (CDC)',
    'Lei 8.245/91 (Lei do Inquilinato)',
    'Art. 927 do Código Civil',
    'Súmula 54 do STJ',
    'Art. 157 do Código Civil',
    'Art. 317 do CPC/2015',
    'Art. 1º da Lei 9.099/95'
  ];

  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Gerar texto jurídico
  async generateText(prompt: string, context?: any): Promise<MockAIResponse> {
    await this.delay(this.responseDelay);

    const type = this.detectPromptType(prompt);
    const template = this.getRandomTemplate(type);
    const content = this.generateContentByType(prompt, type, template);

    return {
      id: `mock_${Date.now()}`,
      content,
      type: 'generation',
      confidence: 0.85 + Math.random() * 0.1,
      timestamp: new Date(),
      sources: ['Base de Conhecimento Jurídico Local', 'Templates Padrão'],
      legalReferences: this.getRandomLegalReferences(2, 4)
    };
  }

  // Analisar documento
  async analyzeDocument(content: string, type: string = 'contrato'): Promise<DocumentAnalysis> {
    await this.delay(this.responseDelay);

    const wordCount = content.split(' ').length;
    const hasProblematicTerms = this.checkProblematicTerms(content);
    const hasRequiredClauses = this.checkRequiredClauses(content, type);

    return {
      risks: this.generateRisks(hasProblematicTerms, type),
      suggestions: this.generateSuggestions(hasRequiredClauses, type),
      compliance: this.generateCompliance(type),
      score: this.calculateScore(wordCount, hasProblematicTerms, hasRequiredClauses)
    };
  }

  // Analisar contrato específico
  async analyzeContract(content: string): Promise<ContractAnalysis> {
    await this.delay(this.responseDelay);

    const clauses = this.extractClauses(content);
    const overallRisk = this.calculateOverallRisk(clauses);

    return {
      clauses,
      overallRisk,
      recommendations: this.generateContractRecommendations(overallRisk)
    };
  }

  // Resumir texto
  async summarizeText(content: string): Promise<MockAIResponse> {
    await this.delay(this.responseDelay);

    const sentences = content.split('.').filter(s => s.trim().length > 10);
    const keyPoints = sentences.slice(0, Math.min(5, Math.ceil(sentences.length / 3)));
    
    const summary = `**Resumo Executivo:**

${keyPoints.map((point, index) => `${index + 1}. ${point.trim()}.`).join('\n')}

**Pontos Principais:**
- Documento com ${content.split(' ').length} palavras
- ${sentences.length} períodos identificados
- Análise baseada em estrutura textual e palavras-chave jurídicas

**Observações:**
Esta análise foi gerada automaticamente. Para análises mais detalhadas, consulte um advogado especializado.`;

    return {
      id: `summary_${Date.now()}`,
      content: summary,
      type: 'summary',
      confidence: 0.75 + Math.random() * 0.15,
      timestamp: new Date(),
      sources: ['Análise Textual Automatizada'],
      legalReferences: this.getRandomLegalReferences(1, 3)
    };
  }

  // Detectar tipo de prompt
  private detectPromptType(prompt: string): string {
    const lowerPrompt = prompt.toLowerCase();
    
    if (lowerPrompt.includes('contrato') || lowerPrompt.includes('análise')) {
      return 'contract_analysis';
    } else if (lowerPrompt.includes('parecer') || lowerPrompt.includes('opinião')) {
      return 'legal_opinion';
    } else {
      return 'document_generation';
    }
  }

  // Obter template aleatório
  private getRandomTemplate(type: string): string {
    const templates = this.templates[type as keyof typeof this.templates] || this.templates.document_generation;
    return templates[Math.floor(Math.random() * templates.length)];
  }

  // Gerar conteúdo por tipo
  private generateContentByType(prompt: string, type: string, template: string): string {
    switch (type) {
      case 'contract_analysis':
        return this.generateContractAnalysisContent(prompt, template);
      case 'legal_opinion':
        return this.generateLegalOpinionContent(prompt, template);
      default:
        return this.generateDocumentContent(prompt, template);
    }
  }

  // Gerar análise de contrato
  private generateContractAnalysisContent(prompt: string, template: string): string {
    return `${template}

**1. ASPECTOS POSITIVOS:**
• Cláusulas claras quanto aos direitos e deveres das partes
• Definição adequada do objeto contratual
• Prazo de vigência bem delimitado

**2. PONTOS DE ATENÇÃO:**
• Verificar adequação das cláusulas penais aos limites legais (Art. 412, CC)
• Analisar equilíbrio nas obrigações entre as partes
• Conferir se há cláusulas abusivas conforme CDC (se aplicável)

**3. SUGESTÕES DE MELHORIA:**
• Incluir cláusula de resolução alternativa de conflitos
• Detalhar melhor as hipóteses de rescisão
• Prever atualização monetária conforme índices oficiais

**4. FUNDAMENTAÇÃO LEGAL:**
Esta análise baseia-se no Código Civil (Lei 10.406/2002), especialmente nos artigos 421 e 422, que tratam da função social do contrato e da boa-fé objetiva.

**OBSERVAÇÃO IMPORTANTE:**
Esta análise é preliminar. Recomenda-se revisão presencial com advogado para casos específicos.`;
  }

  // Gerar parecer jurídico
  private generateLegalOpinionContent(prompt: string, template: string): string {
    return `${template}

**I. RELATÓRIO:**
Com base nas informações apresentadas, verifico que a questão envolve aspectos relevantes do direito brasileiro.

**II. FUNDAMENTAÇÃO JURÍDICA:**
A legislação pátria, em especial o Código Civil e normas específicas da área, estabelece diretrizes claras para a situação apresentada.

**III. JURISPRUDÊNCIA:**
Os tribunais superiores têm entendimento consolidado sobre questões similares, conforme se verifica na jurisprudência do STJ e STF.

**IV. CONCLUSÃO:**
Considerando o exposto, entendo que a situação deve ser analisada à luz dos princípios constitucionais e da legislação específica aplicável.

**V. RECOMENDAÇÕES:**
• Analisar documentação pertinente
• Verificar prazos prescricionais/decadenciais
• Considerar medidas preventivas
• Avaliar viabilidade de solução extrajudicial

**Referências:**
${this.getRandomLegalReferences(3, 5).join(', ')}

*Parecer elaborado com base na legislação vigente à data da consulta.*`;
  }

  // Gerar documento genérico
  private generateDocumentContent(prompt: string, template: string): string {
    return `${template}

**DOCUMENTO JURÍDICO**

Com base na solicitação apresentada, elaboro o presente documento observando as formalidades legais e técnicas jurídicas aplicáveis.

**CONSIDERAÇÕES INICIAIS:**
O documento foi estruturado conforme as normas vigentes e práticas consolidadas no direito brasileiro.

**DESENVOLVIMENTO:**
[Conteúdo específico baseado na solicitação]

**CLÁUSULAS/DISPOSIÇÕES PRINCIPAIS:**
• Definição clara dos termos
• Estabelecimento de direitos e obrigações
• Previsão de penalidades aplicáveis
• Foro competente para dirimir controvérsias

**DISPOSIÇÕES FINAIS:**
As partes declaram estar cientes dos termos e condições estabelecidos, comprometendo-se ao fiel cumprimento.

**Base Legal:**
Este documento fundamenta-se na legislação brasileira vigente, especialmente ${this.getRandomLegalReferences(2, 3).join(' e ')}.

*Documento gerado automaticamente. Sujeito a revisão jurídica especializada.*`;
  }

  // Verificar termos problemáticos
  private checkProblematicTerms(content: string): boolean {
    const problematicTerms = [
      'irrevogável', 'irretratável', 'renúncia total',
      'foro único', 'cláusula leonina', 'vencimento antecipado automático'
    ];
    
    return problematicTerms.some(term => 
      content.toLowerCase().includes(term.toLowerCase())
    );
  }

  // Verificar cláusulas obrigatórias
  private checkRequiredClauses(content: string, type: string): boolean {
    const requiredClauses = {
      'contrato': ['objeto', 'prazo', 'valor', 'partes'],
      'petição': ['qualificação', 'fatos', 'direito', 'pedido'],
      'procuração': ['outorgante', 'outorgado', 'poderes']
    };

    const required = requiredClauses[type as keyof typeof requiredClauses] || requiredClauses.contrato;
    return required.some(clause => 
      content.toLowerCase().includes(clause.toLowerCase())
    );
  }

  // Gerar riscos
  private generateRisks(hasProblematic: boolean, type: string): string[] {
    const baseRisks = [
      'Possível desequilíbrio contratual',
      'Falta de clareza em algumas cláusulas',
      'Ausência de previsão para casos específicos'
    ];

    if (hasProblematic) {
      baseRisks.unshift('Identificadas cláusulas potencialmente abusivas');
    }

    return baseRisks.slice(0, Math.floor(Math.random() * 3) + 2);
  }

  // Gerar sugestões
  private generateSuggestions(hasRequired: boolean, type: string): string[] {
    const baseSuggestions = [
      'Revisar redação para maior clareza',
      'Incluir cláusula de mediação/arbitragem',
      'Verificar adequação à legislação específica'
    ];

    if (!hasRequired) {
      baseSuggestions.unshift('Incluir elementos essenciais do tipo de documento');
    }

    return baseSuggestions.slice(0, Math.floor(Math.random() * 3) + 2);
  }

  // Gerar compliance
  private generateCompliance(type: string): string[] {
    const compliance = {
      'contrato': ['Código Civil', 'CDC (se aplicável)', 'Legislação específica'],
      'petição': ['CPC/2015', 'Regimento interno do tribunal'],
      'procuração': ['Código Civil', 'Estatuto da OAB']
    };

    return compliance[type as keyof typeof compliance] || compliance.contrato;
  }

  // Calcular score
  private calculateScore(wordCount: number, hasProblematic: boolean, hasRequired: boolean): number {
    let score = 70; // Base

    if (wordCount > 500) score += 10;
    if (wordCount > 1000) score += 5;
    if (hasRequired) score += 15;
    if (!hasProblematic) score += 10;

    return Math.min(score, 100);
  }

  // Extrair cláusulas do contrato
  private extractClauses(content: string): Array<{
    type: string;
    content: string;
    risk: 'baixo' | 'medio' | 'alto';
    suggestion: string;
  }> {
    const mockClauses = [
      {
        type: 'Cláusula de Pagamento',
        content: 'Identificada cláusula referente aos termos de pagamento...',
        risk: 'baixo' as const,
        suggestion: 'Verificar adequação dos prazos e formas de pagamento'
      },
      {
        type: 'Cláusula de Rescisão',
        content: 'Localizada cláusula sobre rescisão contratual...',
        risk: 'medio' as const,
        suggestion: 'Equilibrar condições de rescisão para ambas as partes'
      },
      {
        type: 'Cláusula Penal',
        content: 'Presente cláusula estabelecendo penalidades...',
        risk: 'alto' as const,
        suggestion: 'Verificar se a penalidade não excede o valor da obrigação principal'
      }
    ];

    return mockClauses.slice(0, Math.floor(Math.random() * 3) + 1);
  }

  // Calcular risco geral
  private calculateOverallRisk(clauses: any[]): 'baixo' | 'medio' | 'alto' {
    const highRiskClauses = clauses.filter(c => c.risk === 'alto').length;
    const mediumRiskClauses = clauses.filter(c => c.risk === 'medio').length;

    if (highRiskClauses > 0) return 'alto';
    if (mediumRiskClauses > 1) return 'medio';
    return 'baixo';
  }

  // Gerar recomendações para contrato
  private generateContractRecommendations(risk: string): string[] {
    const recommendations = {
      'alto': [
        'Revisão jurídica urgente recomendada',
        'Renegociar cláusulas de alto risco',
        'Considerar parecer jurídico especializado'
      ],
      'medio': [
        'Revisar pontos específicos identificados',
        'Equilibrar direitos e deveres das partes',
        'Incluir salvaguardas adicionais'
      ],
      'baixo': [
        'Contrato em conformidade geral',
        'Pequenos ajustes podem ser benéficos',
        'Manter revisões periódicas'
      ]
    };

    return recommendations[risk as keyof typeof recommendations] || recommendations.medio;
  }

  // Obter referências legais aleatórias
  private getRandomLegalReferences(min: number, max: number): string[] {
    const count = Math.floor(Math.random() * (max - min + 1)) + min;
    const shuffled = [...this.legalReferences].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count);
  }

  // Verificar se a API está disponível
  async isAPIAvailable(): Promise<boolean> {
    try {
      const response = await fetch('https://jurisia-api.onrender.com/health', {
        method: 'GET',
        mode: 'cors',
        credentials: 'omit'
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  // Obter status do serviço
  getServiceStatus(): { online: boolean; mode: string; capabilities: string[] } {
    return {
      online: false,
      mode: 'offline',
      capabilities: [
        'Análise de documentos básica',
        'Geração de texto padrão',
        'Resumos automáticos',
        'Templates jurídicos',
        'Análise de contratos'
      ]
    };
  }
}

export default new MockAIService(); 