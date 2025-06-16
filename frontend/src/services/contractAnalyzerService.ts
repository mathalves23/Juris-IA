import api from './api';

export interface AnalysisResult {
  analysis_id: number;
  nome_arquivo: string;
  tipo_contrato: string;
  score_risco: number;
  nivel_risco: string;
  cor_risco: string;
  nivel_complexidade: string;
  tempo_analise: number;
  tokens_utilizados: number;
  created_at: string;
}

export interface AnalysisDetail {
  id: number;
  nome_arquivo: string;
  tipo_contrato: string;
  score_risco: number;
  nivel_risco: string;
  cor_risco: string;
  nivel_complexidade: string;
  clausulas: Record<string, any>;
  riscos: Record<string, string[]>;
  sugestoes: Record<string, string[]>;
  pontos_atencao: Record<string, string[]>;
  tempo_analise: number;
  tokens_utilizados: number;
  created_at: string;
}

export interface UserStats {
  total_analyses: number;
  risk_distribution: Record<string, number>;
  complexity_distribution: Record<string, number>;
  contract_types: Record<string, number>;
  avg_risk_score: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  total?: number;
}

class ContractAnalyzerService {
  private baseURL = '/contract-analyzer';

  /**
   * Upload e análise de contrato
   */
  async uploadAndAnalyze(file: File): Promise<ApiResponse<AnalysisResult>> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post(`${this.baseURL}/upload-contract`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 60 segundos para análise
    });

    return response.data;
  }

  /**
   * Obter detalhes de uma análise
   */
  async getAnalysisDetail(analysisId: number): Promise<ApiResponse<AnalysisDetail>> {
    const response = await api.get(`${this.baseURL}/analysis/${analysisId}`);
    return response.data;
  }

  /**
   * Listar análises do usuário
   */
  async listAnalyses(limit: number = 20): Promise<ApiResponse<AnalysisResult[]>> {
    const response = await api.get(`${this.baseURL}/analyses`, {
      params: { limit }
    });
    return response.data;
  }

  /**
   * Deletar análise
   */
  async deleteAnalysis(analysisId: number): Promise<ApiResponse<null>> {
    const response = await api.delete(`${this.baseURL}/analysis/${analysisId}`);
    return response.data;
  }

  /**
   * Obter estatísticas do usuário
   */
  async getStats(): Promise<ApiResponse<UserStats>> {
    const response = await api.get(`${this.baseURL}/stats`);
    return response.data;
  }

  /**
   * Comparar duas análises
   */
  async compareAnalyses(analysisId1: number, analysisId2: number): Promise<ApiResponse<any>> {
    const response = await api.post(`${this.baseURL}/compare`, {
      analysis_id_1: analysisId1,
      analysis_id_2: analysisId2
    });
    return response.data;
  }

  /**
   * Validar arquivo antes do upload
   */
  validateFile(file: File): { valid: boolean; error?: string } {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'text/plain'
    ];

    if (file.size > maxSize) {
      return {
        valid: false,
        error: 'Arquivo muito grande. Máximo permitido: 10MB'
      };
    }

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'Formato não suportado. Use PDF, DOCX, DOC ou TXT'
      };
    }

    return { valid: true };
  }

  /**
   * Obter cor baseada no score de risco
   */
  getRiskColor(score: number): string {
    if (score <= 30) return '#52c41a'; // Verde
    if (score <= 60) return '#faad14'; // Amarelo
    return '#ff4d4f'; // Vermelho
  }

  /**
   * Obter texto do nível de risco
   */
  getRiskLevel(score: number): string {
    if (score <= 30) return 'Baixo';
    if (score <= 60) return 'Médio';
    return 'Alto';
  }

  /**
   * Formatar tempo de análise
   */
  formatAnalysisTime(seconds: number): string {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  }

  /**
   * Formatar data de criação
   */
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  /**
   * Obter extensões de arquivo suportadas
   */
  getSupportedExtensions(): string[] {
    return ['.pdf', '.docx', '.doc', '.txt'];
  }

  /**
   * Gerar relatório de análise em texto
   */
  generateTextReport(analysis: AnalysisDetail): string {
    const report = `
RELATÓRIO DE ANÁLISE DE CONTRATO
================================

Arquivo: ${analysis.nome_arquivo}
Tipo: ${analysis.tipo_contrato}
Data: ${this.formatDate(analysis.created_at)}

AVALIAÇÃO DE RISCO
------------------
Score: ${analysis.score_risco}/100
Nível: ${analysis.nivel_risco}
Complexidade: ${analysis.nivel_complexidade}

CLÁUSULAS IDENTIFICADAS
-----------------------
${Object.entries(analysis.clausulas || {})
  .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value || 'Não identificada'}`)
  .join('\n')}

RISCOS IDENTIFICADOS
--------------------
${Object.entries(analysis.riscos || {})
  .map(([nivel, riscos]) => `${nivel.toUpperCase()}:\n${riscos.map(r => `- ${r}`).join('\n')}`)
  .join('\n\n')}

SUGESTÕES DE MELHORIA
---------------------
${Object.entries(analysis.sugestoes || {})
  .map(([categoria, sugestoes]) => `${categoria.toUpperCase()}:\n${sugestoes.map(s => `- ${s}`).join('\n')}`)
  .join('\n\n')}

PONTOS DE ATENÇÃO
-----------------
${Object.entries(analysis.pontos_atencao || {})
  .map(([categoria, pontos]) => `${categoria.toUpperCase()}:\n${pontos.map(p => `- ${p}`).join('\n')}`)
  .join('\n\n')}

INFORMAÇÕES TÉCNICAS
--------------------
Tempo de análise: ${this.formatAnalysisTime(analysis.tempo_analise)}
Tokens utilizados: ${analysis.tokens_utilizados}
    `.trim();

    return report;
  }
}

export const contractAnalyzerService = new ContractAnalyzerService();
export default contractAnalyzerService; 