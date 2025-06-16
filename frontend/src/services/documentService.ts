import axios from 'axios';
import adaptiveAIService from './adaptiveAIService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://jurisia-api.onrender.com/api';

// Cliente configurado com timeout menor para detectar falhas rapidamente
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  }
});

interface Document {
  id?: string;
  title: string;
  content: string;
  type: string;
  status: string;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
}

class DocumentService {
  private isAPIAvailable = false;
  private lastCheck = 0;
  private checkInterval = 30000; // 30 segundos

  constructor() {
    this.checkAPIStatus();
  }

  private async checkAPIStatus(): Promise<boolean> {
    const now = Date.now();
    if (now - this.lastCheck < this.checkInterval) {
      return this.isAPIAvailable;
    }

    try {
      await apiClient.get('/health');
      this.isAPIAvailable = true;
      this.lastCheck = now;
      return true;
    } catch {
      this.isAPIAvailable = false;
      this.lastCheck = now;
      return false;
    }
  }

  async getAllDocuments(): Promise<Document[]> {
    try {
      const isOnline = await this.checkAPIStatus();
      if (isOnline) {
        const response = await apiClient.get('/documents');
        return response.data.documents || response.data || [];
      }
    } catch (error) {
      console.log('📄 API offline - usando documentos mock');
    }

    // Fallback para dados mock
    return this.getMockDocuments();
  }

  async getDocument(id: string): Promise<Document | null> {
    try {
      const isOnline = await this.checkAPIStatus();
      if (isOnline) {
        const response = await apiClient.get(`/documents/${id}`);
        return response.data;
      }
    } catch (error) {
      console.log('📄 API offline - usando documento mock');
    }

    // Fallback para mock
    const mockDocs = this.getMockDocuments();
    return mockDocs.find(doc => doc.id === id) || null;
  }

  async saveDocument(document: Document): Promise<Document> {
    try {
      const isOnline = await this.checkAPIStatus();
      if (isOnline) {
        if (document.id) {
          const response = await apiClient.put(`/documents/${document.id}`, document);
          return response.data;
        } else {
          const response = await apiClient.post('/documents', document);
          return response.data;
        }
      }
    } catch (error) {
      console.log('💾 API offline - salvando localmente');
    }

    // Fallback para salvamento local
    return this.saveMockDocument(document);
  }

  async deleteDocument(id: string): Promise<boolean> {
    try {
      const isOnline = await this.checkAPIStatus();
      if (isOnline) {
        await apiClient.delete(`/documents/${id}`);
        return true;
      }
    } catch (error) {
      console.log('🗑️ API offline - removendo localmente');
    }

    // Fallback para remoção local
    this.deleteMockDocument(id);
    return true;
  }

  async generateDocumentWithAI(prompt: string, type: string): Promise<string> {
    try {
      // Tentar usar o serviço adaptativo que já tem fallback
      const response = await adaptiveAIService.generateText(prompt, { type });
      return response.content;
    } catch (error) {
      console.log('🤖 Gerando documento com IA offline');
      return this.generateMockDocument(prompt, type);
    }
  }

  async analyzeDocument(content: string): Promise<any> {
    try {
      const analysis = await adaptiveAIService.analyzeDocument(content);
      return analysis;
    } catch (error) {
      console.log('📊 Analisando documento offline');
      return this.analyzeMockDocument(content);
    }
  }

  // Métodos mock para funcionalidade offline
  private getMockDocuments(): Document[] {
    const stored = localStorage.getItem('jurisia_documents');
    if (stored) {
      return JSON.parse(stored);
    }

    const defaultDocs: Document[] = [
      {
        id: 'doc_1',
        title: 'Contrato de Prestação de Serviços',
        content: 'CONTRATO DE PRESTAÇÃO DE SERVIÇOS\n\nEntre as partes...',
        type: 'contrato',
        status: 'rascunho',
        tags: ['serviços', 'prestação'],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: 'doc_2',
        title: 'Petição Inicial - Ação de Cobrança',
        content: 'EXCELENTÍSSIMO SENHOR DOUTOR JUIZ...\n\nVem respeitosamente...',
        type: 'petição',
        status: 'finalizado',
        tags: ['cobrança', 'petição'],
        created_at: new Date(Date.now() - 86400000).toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: 'doc_3',
        title: 'Parecer Jurídico - Análise de Viabilidade',
        content: 'PARECER JURÍDICO\n\n1. RELATÓRIO\nTrata-se de consulta...',
        type: 'parecer',
        status: 'revisão',
        tags: ['parecer', 'viabilidade'],
        created_at: new Date(Date.now() - 172800000).toISOString(),
        updated_at: new Date(Date.now() - 3600000).toISOString()
      }
    ];

    localStorage.setItem('jurisia_documents', JSON.stringify(defaultDocs));
    return defaultDocs;
  }

  private saveMockDocument(document: Document): Document {
    const docs = this.getMockDocuments();
    
    if (document.id) {
      // Atualizar documento existente
      const index = docs.findIndex(d => d.id === document.id);
      if (index !== -1) {
        docs[index] = { ...document, updated_at: new Date().toISOString() };
      }
    } else {
      // Criar novo documento
      const newDoc = {
        ...document,
        id: `doc_${Date.now()}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      docs.unshift(newDoc);
      document = newDoc;
    }

    localStorage.setItem('jurisia_documents', JSON.stringify(docs));
    return document;
  }

  private deleteMockDocument(id: string): void {
    const docs = this.getMockDocuments();
    const filtered = docs.filter(d => d.id !== id);
    localStorage.setItem('jurisia_documents', JSON.stringify(filtered));
  }

  private generateMockDocument(prompt: string, type: string): string {
    const templates: { [key: string]: string } = {
      'contrato': `CONTRATO DE ${prompt.toUpperCase()}

CONTRATANTE: [NOME DO CONTRATANTE]
CONTRATADO: [NOME DO CONTRATADO]

CLÁUSULA PRIMEIRA - DO OBJETO
O presente contrato tem por objeto...

CLÁUSULA SEGUNDA - DAS OBRIGAÇÕES
Ficam estabelecidas as seguintes obrigações...

CLÁUSULA TERCEIRA - DO VALOR E PAGAMENTO
O valor total do contrato é de R$ [VALOR]...

[DOCUMENTO GERADO AUTOMATICAMENTE - MODO OFFLINE]`,

      'petição': `EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO

${prompt}

Vem respeitosamente à presença de Vossa Excelência, [NOME DO AUTOR], [QUALIFICAÇÃO], por meio de seu advogado que esta subscreve, propor a presente

AÇÃO [TIPO DA AÇÃO]

em face de [NOME DO RÉU], [QUALIFICAÇÃO], pelos fatos e fundamentos jurídicos a seguir expostos:

I - DOS FATOS
[NARRAÇÃO DOS FATOS]

II - DO DIREITO
[FUNDAMENTAÇÃO JURÍDICA]

III - DOS PEDIDOS
Diante do exposto, requer-se...

[DOCUMENTO GERADO AUTOMATICAMENTE - MODO OFFLINE]`,

      'parecer': `PARECER JURÍDICO

CONSULENTE: [NOME DO CONSULENTE]
ASSUNTO: ${prompt}

1. RELATÓRIO
Trata-se de consulta jurídica sobre...

2. FUNDAMENTAÇÃO LEGAL
Com base na legislação vigente...

3. CONCLUSÃO
Face ao exposto, opina-se que...

[DOCUMENTO GERADO AUTOMATICAMENTE - MODO OFFLINE]`
    };

    return templates[type] || templates['contrato'];
  }

  private analyzeMockDocument(content: string): any {
    const wordCount = content.split(' ').length;
    const paragraphs = content.split('\n').filter(p => p.trim().length > 0).length;
    
    return {
      risks: wordCount > 1000 ? ['Documento extenso pode conter cláusulas complexas'] : ['Documento padrão'],
      suggestions: [
        'Revisar termos técnicos',
        'Verificar adequação à legislação',
        'Considerar incluir cláusulas de segurança'
      ],
      compliance: ['Código Civil', 'Legislação específica'],
      score: Math.floor(Math.random() * 30) + 70, // Score entre 70-100
      statistics: {
        words: wordCount,
        paragraphs: paragraphs,
        readability: wordCount > 500 ? 'Complexo' : 'Simples',
        estimatedReadTime: Math.ceil(wordCount / 200) + ' minutos'
      }
    };
  }

  // Verificar se está online
  isOnline(): boolean {
    return this.isAPIAvailable;
  }

  // Forçar verificação de status
  async checkStatus(): Promise<boolean> {
    return this.checkAPIStatus();
  }
}

export default new DocumentService(); 