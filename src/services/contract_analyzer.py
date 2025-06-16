"""
Serviço de Análise Inteligente de Contratos
Utiliza IA para análise profunda de documentos jurídicos
"""

import re
import time
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import PyPDF2
import docx
from io import BytesIO

from src.services.ai_service import LegalAIService, AIRequest, AITask, DocumentType
from src.models.contract_analysis import ContractAnalysis
from src.extensions import db

logger = logging.getLogger(__name__)

@dataclass
class ContractAnalysisResult:
    """Resultado da análise de contrato"""
    score_risco: int
    nivel_complexidade: str
    tipo_contrato: str
    clausulas_extraidas: Dict
    riscos_identificados: Dict
    sugestoes_melhoria: Dict
    pontos_atencao: Dict
    tempo_analise: float
    tokens_utilizados: int

class ContractAnalyzer:
    """Analisador Inteligente de Contratos"""
    
    def __init__(self):
        self.ai_service = LegalAIService()
        
        # Tipos de contratos reconhecidos
        self.tipos_contratos = {
            'prestacao_servicos': 'Prestação de Serviços',
            'compra_venda': 'Compra e Venda',
            'locacao': 'Locação',
            'trabalho': 'Contrato de Trabalho',
            'sociedade': 'Contrato Social',
            'confidencialidade': 'Confidencialidade (NDA)',
            'franchising': 'Franquia',
            'distribuicao': 'Distribuição',
            'fornecimento': 'Fornecimento',
            'consultoria': 'Consultoria',
            'licenciamento': 'Licenciamento',
            'parceria': 'Parceria Comercial'
        }
        
        # Cláusulas críticas por tipo
        self.clausulas_criticas = {
            'geral': [
                'rescisão', 'vigência', 'pagamento', 'multa', 'foro',
                'responsabilidade', 'garantia', 'confidencialidade'
            ],
            'prestacao_servicos': [
                'escopo', 'prazo', 'entregáveis', 'propriedade intelectual',
                'remuneração', 'exclusividade'
            ],
            'compra_venda': [
                'preço', 'entrega', 'qualidade', 'garantia', 'vícios',
                'propriedade', 'riscos'
            ],
            'locacao': [
                'aluguel', 'reajuste', 'benfeitorias', 'uso', 'reforma',
                'fiador', 'caução'
            ]
        }
    
    def extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """Extrai texto de arquivos PDF ou DOCX"""
        try:
            if filename.lower().endswith('.pdf'):
                return self._extract_text_from_pdf(file_content)
            elif filename.lower().endswith(('.docx', '.doc')):
                return self._extract_text_from_docx(file_content)
            else:
                # Assume que é texto puro
                return file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Erro ao extrair texto de {filename}: {str(e)}")
            raise Exception(f"Não foi possível extrair texto do arquivo: {str(e)}")
    
    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extrai texto de arquivo PDF"""
        pdf_file = BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    
    def _extract_text_from_docx(self, file_content: bytes) -> str:
        """Extrai texto de arquivo DOCX"""
        docx_file = BytesIO(file_content)
        doc = docx.Document(docx_file)
        
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    
    def identify_contract_type(self, text: str) -> str:
        """Identifica o tipo de contrato baseado no conteúdo"""
        text_lower = text.lower()
        
        # Padrões para identificação
        patterns = {
            'prestacao_servicos': [
                'prestação de serviços', 'prestação de serviço', 'serviços',
                'contratado', 'contratante', 'prestador'
            ],
            'compra_venda': [
                'compra e venda', 'comprador', 'vendedor', 'compra', 'venda',
                'mercadoria', 'produto'
            ],
            'locacao': [
                'locação', 'aluguel', 'locador', 'locatário', 'imóvel',
                'arrendamento'
            ],
            'trabalho': [
                'contrato de trabalho', 'emprego', 'empregado', 'empregador',
                'salário', 'clt'
            ],
            'sociedade': [
                'contrato social', 'sociedade', 'sócios', 'capital social',
                'quotas'
            ],
            'confidencialidade': [
                'confidencialidade', 'sigilo', 'nda', 'informações confidenciais',
                'não divulgação'
            ]
        }
        
        scores = {}
        for tipo, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[tipo] = score
        
        if scores:
            tipo_identificado = max(scores, key=scores.get)
            return self.tipos_contratos.get(tipo_identificado, 'Contrato Geral')
        
        return 'Contrato Geral'
    
    def analyze_contract(self, text: str, filename: str) -> ContractAnalysisResult:
        """Realiza análise completa do contrato"""
        start_time = time.time()
        
        try:
            # 1. Identifica tipo de contrato
            tipo_contrato = self.identify_contract_type(text)
            logger.info(f"Tipo identificado: {tipo_contrato}")
            
            # 2. Análise com IA
            ai_result = self._analyze_with_ai(text, tipo_contrato)
            
            # 3. Processa resultados
            analysis_result = self._process_ai_result(ai_result, tipo_contrato)
            
            # 4. Calcula tempo de análise
            analysis_result.tempo_analise = time.time() - start_time
            
            logger.info(f"Análise concluída em {analysis_result.tempo_analise:.2f}s")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Erro na análise do contrato: {str(e)}")
            raise Exception(f"Falha na análise: {str(e)}")
    
    def _analyze_with_ai(self, text: str, tipo_contrato: str) -> Dict:
        """Realiza análise com IA especializada"""
        
        prompt = f"""
Você é um advogado especialista em análise de contratos. Analise o seguinte contrato de {tipo_contrato}:

CONTRATO:
{text[:8000]}  # Limita para evitar excesso de tokens

INSTRUÇÕES DE ANÁLISE:
1. Identifique e extraia as principais cláusulas
2. Avalie os riscos jurídicos (pontuação 0-100)
3. Determine o nível de complexidade (Baixa/Média/Alta)
4. Identifique pontos que precisam de atenção especial
5. Sugira melhorias específicas

FORMATO DE RESPOSTA (JSON):
{{
    "score_risco": <número 0-100>,
    "nivel_complexidade": "<Baixa|Média|Alta>",
    "clausulas_extraidas": {{
        "vigencia": "<texto da cláusula ou null>",
        "rescisao": "<texto da cláusula ou null>",
        "pagamento": "<texto da cláusula ou null>",
        "multa": "<texto da cláusula ou null>",
        "foro": "<texto da cláusula ou null>",
        "responsabilidade": "<texto da cláusula ou null>",
        "garantia": "<texto da cláusula ou null>",
        "outras": ["<outras cláusulas importantes>"]
    }},
    "riscos_identificados": {{
        "alto": ["<riscos de alto impacto>"],
        "medio": ["<riscos de médio impacto>"],
        "baixo": ["<riscos de baixo impacto>"]
    }},
    "pontos_atencao": {{
        "criticos": ["<pontos críticos>"],
        "importantes": ["<pontos importantes>"],
        "observacoes": ["<observações gerais>"]
    }},
    "sugestoes_melhoria": {{
        "essenciais": ["<melhorias essenciais>"],
        "recomendadas": ["<melhorias recomendadas>"],
        "opcionais": ["<melhorias opcionais>"]
    }}
}}

Responda APENAS com o JSON válido, sem explicações adicionais.
"""
        
        try:
            # Faz requisição para IA
            ai_request = AIRequest(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.1  # Baixa para análise mais precisa
            )
            
            response = self.ai_service.generate_text(ai_request)
            
            # Extrai JSON da resposta
            json_text = response.content.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:-3]
            elif json_text.startswith('```'):
                json_text = json_text[3:-3]
            
            result = json.loads(json_text)
            result['tokens_utilizados'] = response.tokens_used
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON da IA: {str(e)}")
            # Fallback com análise básica
            return self._fallback_analysis(text, tipo_contrato)
        except Exception as e:
            logger.error(f"Erro na análise com IA: {str(e)}")
            return self._fallback_analysis(text, tipo_contrato)
    
    def _process_ai_result(self, ai_result: Dict, tipo_contrato: str) -> ContractAnalysisResult:
        """Processa resultado da IA"""
        
        return ContractAnalysisResult(
            score_risco=ai_result.get('score_risco', 50),
            nivel_complexidade=ai_result.get('nivel_complexidade', 'Média'),
            tipo_contrato=tipo_contrato,
            clausulas_extraidas=ai_result.get('clausulas_extraidas', {}),
            riscos_identificados=ai_result.get('riscos_identificados', {}),
            sugestoes_melhoria=ai_result.get('sugestoes_melhoria', {}),
            pontos_atencao=ai_result.get('pontos_atencao', {}),
            tempo_analise=0.0,  # Será calculado depois
            tokens_utilizados=ai_result.get('tokens_utilizados', 0)
        )
    
    def _fallback_analysis(self, text: str, tipo_contrato: str) -> Dict:
        """Análise básica quando a IA falha"""
        logger.warning("Usando análise básica - IA indisponível")
        
        text_lower = text.lower()
        
        # Análise básica de risco baseada em palavras-chave
        risk_keywords = {
            'alto': ['multa', 'penalidade', 'rescisão', 'exclusividade', 'irrevogável'],
            'medio': ['responsabilidade', 'garantia', 'indenização', 'prazo'],
            'baixo': ['acordo', 'consenso', 'mútuo', 'amigável']
        }
        
        score_risco = 30  # Base
        for nivel, keywords in risk_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            if nivel == 'alto':
                score_risco += count * 15
            elif nivel == 'medio':
                score_risco += count * 8
            else:
                score_risco -= count * 5
        
        score_risco = max(0, min(100, score_risco))
        
        return {
            'score_risco': score_risco,
            'nivel_complexidade': 'Média',
            'clausulas_extraidas': {'outras': ['Análise detalhada indisponível']},
            'riscos_identificados': {'medio': ['Análise automática limitada']},
            'pontos_atencao': {'importantes': ['Recomenda-se revisão manual']},
            'sugestoes_melhoria': {'recomendadas': ['Consulte um advogado especialista']},
            'tokens_utilizados': 0
        }
    
    def save_analysis(self, analysis_result: ContractAnalysisResult, 
                     filename: str, text: str, user_id: int, 
                     document_id: Optional[int] = None) -> ContractAnalysis:
        """Salva análise no banco de dados"""
        
        try:
            analysis = ContractAnalysis(
                nome_arquivo=filename,
                tipo_contrato=analysis_result.tipo_contrato,
                conteudo_original=text[:10000],  # Limita tamanho
                score_risco=analysis_result.score_risco,
                nivel_complexidade=analysis_result.nivel_complexidade,
                tempo_analise=analysis_result.tempo_analise,
                tokens_utilizados=analysis_result.tokens_utilizados,
                user_id=user_id,
                document_id=document_id
            )
            
            # Define dados JSON
            analysis.set_clausulas(analysis_result.clausulas_extraidas)
            analysis.set_riscos(analysis_result.riscos_identificados)
            analysis.set_sugestoes(analysis_result.sugestoes_melhoria)
            analysis.set_pontos_atencao(analysis_result.pontos_atencao)
            
            db.session.add(analysis)
            db.session.commit()
            
            logger.info(f"Análise salva com ID: {analysis.id}")
            return analysis
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao salvar análise: {str(e)}")
            raise Exception(f"Falha ao salvar análise: {str(e)}")
    
    def get_analysis_by_id(self, analysis_id: int, user_id: int) -> Optional[ContractAnalysis]:
        """Recupera análise por ID"""
        return ContractAnalysis.query.filter_by(
            id=analysis_id, 
            user_id=user_id
        ).first()
    
    def get_user_analyses(self, user_id: int, limit: int = 50) -> List[ContractAnalysis]:
        """Recupera análises do usuário"""
        return ContractAnalysis.query.filter_by(
            user_id=user_id
        ).order_by(ContractAnalysis.created_at.desc()).limit(limit).all()
    
    def delete_analysis(self, analysis_id: int, user_id: int) -> bool:
        """Remove análise"""
        try:
            analysis = ContractAnalysis.query.filter_by(
                id=analysis_id, 
                user_id=user_id
            ).first()
            
            if analysis:
                db.session.delete(analysis)
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao deletar análise: {str(e)}")
            return False 