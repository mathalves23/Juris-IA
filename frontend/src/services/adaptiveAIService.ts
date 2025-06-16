import axios, { AxiosError } from 'axios';
import mockAIService, { MockAIResponse, DocumentAnalysis, ContractAnalysis } from './mockAIService';

// Configuração de timeout mais baixo para detectar falhas rapidamente
const API_TIMEOUT = 5000;

// Cliente axios configurado
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || (
    process.env.NODE_ENV === 'production' ? '/api' : 'https://jurisia-api.onrender.com/api'
  ),
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

interface ServiceStatus {
  isOnline: boolean;
  lastCheck: Date;
  mode: 'api' | 'mock';
  errorCount: number;
}

class AdaptiveAIService {
  private status: ServiceStatus = {
    isOnline: false,
    lastCheck: new Date(0),
    mode: 'mock',
    errorCount: 0
  };

  private maxErrors = 3;
  private checkInterval = 60000; // 1 minuto
  private retryDelay = 2000; // 2 segundos

  constructor() {
    this.initializeService();
  }

  // Inicializar serviço
  private async initializeService() {
    await this.checkAPIStatus();
    
    // Verificar status periodicamente
    setInterval(() => {
      this.checkAPIStatus();
    }, this.checkInterval);
  }

  // Verificar status da API
  private async checkAPIStatus(): Promise<boolean> {
    try {
      const response = await apiClient.get('/health');
      this.status = {
        isOnline: true,
        lastCheck: new Date(),
        mode: 'api',
        errorCount: 0
      };
      
      console.log('✅ API online - usando serviço completo');
      return true;
    } catch (error) {
      this.status.errorCount++;
      this.status.isOnline = false;
      this.status.lastCheck = new Date();
      this.status.mode = 'mock';
      
      console.log(`❌ API offline (erros: ${this.status.errorCount}) - usando modo offline`);
      return false;
    }
  }

  // Executar com fallback
  private async executeWithFallback<T>(
    apiCall: () => Promise<T>,
    mockCall: () => Promise<T>,
    operationName: string
  ): Promise<T> {
    // Se já sabemos que está offline, usar mock diretamente
    if (!this.status.isOnline && this.status.errorCount >= this.maxErrors) {
      console.log(`🔄 ${operationName}: Usando modo offline`);
      return mockCall();
    }

    try {
      console.log(`🚀 ${operationName}: Tentando API...`);
      const result = await apiCall();
      
      // Se sucesso, resetar contador de erros
      this.status.errorCount = 0;
      this.status.isOnline = true;
      this.status.mode = 'api';
      
      return result;
    } catch (error) {
      console.log(`⚠️ ${operationName}: API falhou, usando fallback`);
      this.handleAPIError(error as AxiosError);
      
      return mockCall();
    }
  }

  // Lidar com erros da API
  private handleAPIError(error: AxiosError) {
    this.status.errorCount++;
    this.status.isOnline = false;
    
    if (error.code === 'ERR_NETWORK' || error.code === 'ERR_FAILED') {
      console.log('🔌 Problema de conectividade detectado');
    } else if (error.response?.status === 404) {
      console.log('🚫 Endpoint não encontrado');
    } else if (error.response?.status && error.response.status >= 500) {
      console.log('🔥 Erro interno do servidor');
    }
  }

  // Gerar texto com IA
  async generateText(prompt: string, context?: any): Promise<MockAIResponse> {
    return this.executeWithFallback(
      async () => {
        const response = await apiClient.post('/ai/generate', {
          prompt,
          context,
          max_tokens: 1000
        });
        
        return {
          id: response.data.id || `api_${Date.now()}`,
          content: response.data.content || response.data.text,
          type: 'generation',
          confidence: response.data.confidence || 0.9,
          timestamp: new Date(),
          sources: response.data.sources || ['API de IA Jurídica'],
          legalReferences: response.data.legal_references || []
        };
      },
      () => mockAIService.generateText(prompt, context),
      'Geração de Texto'
    );
  }

  // Analisar documento
  async analyzeDocument(content: string, type: string = 'contrato'): Promise<DocumentAnalysis> {
    return this.executeWithFallback(
      async () => {
        const response = await apiClient.post('/ai/analyze-document', {
          content,
          document_type: type
        });
        
        return {
          risks: response.data.risks || [],
          suggestions: response.data.suggestions || [],
          compliance: response.data.compliance || [],
          score: response.data.score || 75
        };
      },
      () => mockAIService.analyzeDocument(content, type),
      'Análise de Documento'
    );
  }

  // Analisar contrato
  async analyzeContract(content: string): Promise<ContractAnalysis> {
    return this.executeWithFallback(
      async () => {
        const response = await apiClient.post('/contract-analyzer/analyze', {
          content,
          analysis_type: 'complete'
        });
        
        return {
          clauses: response.data.clauses || [],
          overallRisk: response.data.overall_risk || 'medio',
          recommendations: response.data.recommendations || []
        };
      },
      () => mockAIService.analyzeContract(content),
      'Análise de Contrato'
    );
  }

  // Resumir texto
  async summarizeText(content: string): Promise<MockAIResponse> {
    return this.executeWithFallback(
      async () => {
        const response = await apiClient.post('/ai/summarize', {
          content,
          max_length: 500
        });
        
        return {
          id: response.data.id || `summary_${Date.now()}`,
          content: response.data.summary || response.data.content,
          type: 'summary',
          confidence: response.data.confidence || 0.8,
          timestamp: new Date(),
          sources: response.data.sources || ['API de Resumo'],
          legalReferences: response.data.legal_references || []
        };
      },
      () => mockAIService.summarizeText(content),
      'Resumo de Texto'
    );
  }

  // Buscar documentos
  async getDocuments(): Promise<any[]> {
    return this.executeWithFallback(
      async () => {
        const response = await apiClient.get('/documents');
        return response.data.documents || response.data || [];
      },
      async () => {
        // Dados mock para documentos
        return [
          {
            id: 'doc1',
            title: 'Contrato de Prestação de Serviços',
            type: 'contrato',
            status: 'rascunho',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            content: 'Contrato exemplo...',
            tags: ['serviços', 'prestação']
          },
          {
            id: 'doc2', 
            title: 'Petição Inicial - Ação de Cobrança',
            type: 'petição',
            status: 'finalizado',
            created_at: new Date(Date.now() - 86400000).toISOString(),
            updated_at: new Date().toISOString(),
            content: 'Petição exemplo...',
            tags: ['cobrança', 'petição']
          }
        ];
      },
      'Buscar Documentos'
    );
  }

  // Buscar templates
  async getTemplates(): Promise<any[]> {
    return this.executeWithFallback(
      async () => {
        const response = await apiClient.get('/templates');
        return response.data.templates || response.data || [];
      },
      async () => {
        // Templates mock
        return [
          {
            id: 'tpl1',
            name: 'Contrato de Prestação de Serviços',
            category: 'Contratos',
            content: 'Template de contrato...',
            variables: ['CONTRATANTE', 'CONTRATADO', 'OBJETO', 'VALOR'],
            created_at: new Date().toISOString()
          },
          {
            id: 'tpl2',
            name: 'Petição Inicial Cível',
            category: 'Petições',
            content: 'Template de petição...',
            variables: ['AUTOR', 'REU', 'CAUSA_PEDIR', 'PEDIDO'],
            created_at: new Date().toISOString()
          }
        ];
      },
      'Buscar Templates'
    );
  }

  // Obter análises de contrato
  async getContractAnalyses(limit: number = 20): Promise<any[]> {
    return this.executeWithFallback(
      async () => {
        const response = await apiClient.get(`/contract-analyzer/analyses?limit=${limit}`);
        return response.data.analyses || response.data || [];
      },
      async () => {
        // Análises mock
        return [
          {
            id: 'analysis1',
            document_name: 'Contrato_Servicos_001.pdf',
            risk_level: 'baixo',
            score: 85,
            created_at: new Date().toISOString(),
            summary: 'Contrato bem estruturado com baixo risco'
          },
          {
            id: 'analysis2',
            document_name: 'Contrato_Fornecimento_002.pdf', 
            risk_level: 'medio',
            score: 72,
            created_at: new Date(Date.now() - 3600000).toISOString(),
            summary: 'Algumas cláusulas requerem atenção'
          }
        ];
      },
      'Buscar Análises de Contrato'
    );
  }

  // Obter estatísticas de contrato
  async getContractStats(): Promise<any> {
    return this.executeWithFallback(
      async () => {
        const response = await apiClient.get('/contract-analyzer/stats');
        return response.data || {};
      },
      async () => {
        // Stats mock
        return {
          total_analyses: 45,
          avg_score: 78.5,
          risk_distribution: {
            baixo: 60,
            medio: 30,
            alto: 10
          },
          monthly_analyses: 12,
          improvement_trend: 8.5
        };
      },
      'Buscar Estatísticas'
    );
  }

  // Salvar documento
  async saveDocument(document: any): Promise<any> {
    return this.executeWithFallback(
      async () => {
        const response = await apiClient.post('/documents', document);
        return response.data;
      },
      async () => {
        // Simulação de salvamento
        return {
          ...document,
          id: `mock_${Date.now()}`,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
      },
      'Salvar Documento'
    );
  }

  // Obter status do serviço
  getServiceStatus(): {
    mode: 'api' | 'mock';
    isOnline: boolean;
    lastCheck: Date;
    errorCount: number;
    capabilities: string[];
  } {
    return {
      mode: this.status.mode,
      isOnline: this.status.isOnline,
      lastCheck: this.status.lastCheck,
      errorCount: this.status.errorCount,
      capabilities: this.status.mode === 'api' ? [
        'IA avançada com GPT',
        'Análise completa de documentos',
        'Base de conhecimento jurídico',
        'Sincronização em nuvem',
        'Análise de contratos profissional'
      ] : [
        'IA básica offline',
        'Análise de documentos local',
        'Templates padrão',
        'Funcionamento sem internet',
        'Análise de contratos básica'
      ]
    };
  }

  // Forçar verificação de status
  async forceStatusCheck(): Promise<boolean> {
    return this.checkAPIStatus();
  }

  // Alternar para modo mock (para testes)
  forceMockMode(): void {
    this.status.isOnline = false;
    this.status.mode = 'mock';
    this.status.errorCount = this.maxErrors;
    console.log('🔧 Modo mock forçado');
  }

  // Alternar para modo API (para testes)
  async forceAPIMode(): Promise<boolean> {
    const isOnline = await this.checkAPIStatus();
    if (isOnline) {
      console.log('🔧 Modo API forçado');
    }
    return isOnline;
  }
}

export default new AdaptiveAIService(); 