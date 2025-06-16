import openai
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime
from flask import current_app

class DocumentType(Enum):
    """Tipos de documentos jurídicos"""
    CONTRATO = "contrato"
    PETICAO = "peticao"
    PARECER = "parecer"
    ATA = "ata"
    PROCURACAO = "procuracao"
    ESCRITURA = "escritura"
    RECURSO = "recurso"
    DEFESA = "defesa"
    ACORDO = "acordo"
    NOTIFICACAO = "notificacao"

class LegalArea(Enum):
    """Áreas do direito"""
    CIVIL = "civil"
    PENAL = "penal"
    TRABALHISTA = "trabalhista"
    TRIBUTARIO = "tributario"
    EMPRESARIAL = "empresarial"
    FAMILIA = "familia"
    CONSUMIDOR = "consumidor"
    PREVIDENCIARIO = "previdenciario"
    ADMINISTRATIVO = "administrativo"
    CONSTITUCIONAL = "constitucional"

@dataclass
class LegalContext:
    """Contexto jurídico para IA"""
    document_type: DocumentType
    legal_area: LegalArea
    court_level: Optional[str] = None
    jurisdiction: Optional[str] = None
    case_number: Optional[str] = None
    parties: Optional[List[str]] = None
    subject_matter: Optional[str] = None

class LegalAIService:
    """Serviço de IA especializado em documentos jurídicos"""
    
    def __init__(self):
        self.client = None
        self.setup_openai()
        
        # Base de conhecimento jurídico
        self.legal_templates = {
            DocumentType.CONTRATO: self._get_contract_templates(),
            DocumentType.PETICAO: self._get_petition_templates(),
            DocumentType.PARECER: self._get_legal_opinion_templates(),
            DocumentType.PROCURACAO: self._get_power_of_attorney_templates(),
            DocumentType.RECURSO: self._get_appeal_templates(),
            DocumentType.DEFESA: self._get_defense_templates(),
            DocumentType.ACORDO: self._get_agreement_templates(),
            DocumentType.NOTIFICACAO: self._get_notification_templates()
        }
        
        # Prompts especializados
        self.system_prompts = {
            'contract_analysis': self._get_contract_analysis_prompt(),
            'document_review': self._get_document_review_prompt(),
            'legal_research': self._get_legal_research_prompt(),
            'document_generation': self._get_document_generation_prompt(),
            'clause_suggestion': self._get_clause_suggestion_prompt()
        }
    
    def setup_openai(self):
        """Configurar cliente OpenAI"""
        api_key = current_app.config.get('OPENAI_API_KEY') if current_app else None
        if api_key:
            openai.api_key = api_key
            self.client = openai
    
    def analyze_document(self, content: str, context: LegalContext) -> Dict[str, Any]:
        """Análise avançada de documento jurídico"""
        if not self.client:
            return self._fallback_analysis(content, context)
        
        try:
            prompt = self._build_analysis_prompt(content, context)
            
            response = self.client.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": self.system_prompts['document_review']},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            analysis = self._parse_analysis_response(response.choices[0].message.content)
            
            return {
                'status': 'success',
                'analysis': analysis,
                'suggestions': self._generate_suggestions(analysis, context),
                'risk_assessment': self._assess_risks(analysis, context),
                'compliance_check': self._check_compliance(content, context)
            }
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Erro na análise de documento: {e}")
            return self._fallback_analysis(content, context)
    
    def generate_document(self, 
                         document_type: DocumentType,
                         legal_area: LegalArea,
                         parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Geração inteligente de documento jurídico"""
        if not self.client:
            return self._fallback_generation(document_type, legal_area, parameters)
        
        try:
            template = self.legal_templates.get(document_type, {}).get(legal_area.value, "")
            prompt = self._build_generation_prompt(document_type, legal_area, parameters, template)
            
            response = self.client.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": self.system_prompts['document_generation']},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=3000
            )
            
            generated_content = response.choices[0].message.content
            
            return {
                'status': 'success',
                'content': generated_content,
                'metadata': {
                    'document_type': document_type.value,
                    'legal_area': legal_area.value,
                    'generated_at': datetime.utcnow().isoformat(),
                    'parameters_used': parameters
                },
                'quality_score': self._calculate_quality_score(generated_content)
            }
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Erro na geração de documento: {e}")
            return self._fallback_generation(document_type, legal_area, parameters)
    
    def suggest_clauses(self, 
                       document_type: DocumentType,
                       existing_content: str,
                       context: LegalContext) -> Dict[str, Any]:
        """Sugestão inteligente de cláusulas"""
        if not self.client:
            return self._fallback_clause_suggestions(document_type, existing_content)
        
        try:
            prompt = self._build_clause_suggestion_prompt(document_type, existing_content, context)
            
            response = self.client.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": self.system_prompts['clause_suggestion']},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            suggestions = self._parse_clause_suggestions(response.choices[0].message.content)
            
            return {
                'status': 'success',
                'suggestions': suggestions,
                'priority_clauses': self._identify_priority_clauses(suggestions, context),
                'legal_precedents': self._find_relevant_precedents(document_type, context)
            }
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Erro na sugestão de cláusulas: {e}")
            return self._fallback_clause_suggestions(document_type, existing_content)
    
    def legal_research(self, query: str, legal_area: LegalArea) -> Dict[str, Any]:
        """Pesquisa jurídica assistida por IA"""
        if not self.client:
            return self._fallback_legal_research(query, legal_area)
        
        try:
            prompt = self._build_research_prompt(query, legal_area)
            
            response = self.client.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": self.system_prompts['legal_research']},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2500
            )
            
            research_result = self._parse_research_response(response.choices[0].message.content)
            
            return {
                'status': 'success',
                'research': research_result,
                'legal_references': self._extract_legal_references(research_result),
                'related_topics': self._identify_related_topics(query, legal_area)
            }
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Erro na pesquisa jurídica: {e}")
            return self._fallback_legal_research(query, legal_area)
    
    def _build_analysis_prompt(self, content: str, context: LegalContext) -> str:
        """Construir prompt para análise de documento"""
        return f"""
        Analyze the following legal document with these parameters:
        - Document Type: {context.document_type.value}
        - Legal Area: {context.legal_area.value}
        - Court Level: {context.court_level or 'N/A'}
        - Jurisdiction: {context.jurisdiction or 'N/A'}
        
        Document Content:
        {content}
        
        Please provide:
        1. Document structure analysis
        2. Legal compliance assessment
        3. Potential risks or issues
        4. Improvement suggestions
        5. Missing essential clauses or elements
        """
    
    def _build_generation_prompt(self, 
                                document_type: DocumentType,
                                legal_area: LegalArea,
                                parameters: Dict[str, Any],
                                template: str) -> str:
        """Construir prompt para geração de documento"""
        params_str = '\n'.join([f"- {k}: {v}" for k, v in parameters.items()])
        
        return f"""
        Generate a {document_type.value} for {legal_area.value} law with these parameters:
        {params_str}
        
        Use this template as reference:
        {template}
        
        Requirements:
        1. Follow Brazilian legal standards
        2. Include all necessary legal clauses
        3. Use formal legal language
        4. Ensure legal compliance
        5. Add appropriate legal references
        """
    
    def _build_clause_suggestion_prompt(self, document_type: DocumentType, existing_content: str, context: LegalContext) -> str:
        """Construir prompt para sugestão de cláusulas"""
        return f"""
        Suggest additional clauses for this {document_type.value} in {context.legal_area.value} law:
        
        Existing content:
        {existing_content}
        
        Context:
        - Document Type: {document_type.value}
        - Legal Area: {context.legal_area.value}
        - Subject Matter: {context.subject_matter or 'General'}
        
        Please suggest missing essential clauses and improvements.
        """
    
    def _build_research_prompt(self, query: str, legal_area: LegalArea) -> str:
        """Construir prompt para pesquisa jurídica"""
        return f"""
        Conduct legal research on the following topic in {legal_area.value} law:
        
        Query: {query}
        
        Please provide:
        1. Relevant legislation
        2. Key legal principles
        3. Important case law
        4. Current legal trends
        5. Practical recommendations
        
        Focus on Brazilian law and jurisprudence.
        """
    
    def _get_contract_templates(self) -> Dict[str, str]:
        """Templates de contratos por área jurídica"""
        return {
            'civil': """
            CONTRATO DE [TIPO]
            
            CONTRATANTE: [NOME_CONTRATANTE], [QUALIFICACAO]
            CONTRATADO: [NOME_CONTRATADO], [QUALIFICACAO]
            
            CLÁUSULA 1ª - DO OBJETO
            CLÁUSULA 2ª - DAS OBRIGAÇÕES
            CLÁUSULA 3ª - DO PAGAMENTO
            CLÁUSULA 4ª - DO PRAZO
            CLÁUSULA 5ª - DAS PENALIDADES
            CLÁUSULA 6ª - DO FORO
            """,
            'trabalhista': """
            CONTRATO DE TRABALHO
            
            EMPREGADOR: [RAZAO_SOCIAL], [CNPJ]
            EMPREGADO: [NOME_COMPLETO], [CPF]
            
            CLÁUSULA 1ª - DA FUNÇÃO
            CLÁUSULA 2ª - DA REMUNERAÇÃO
            CLÁUSULA 3ª - DA JORNADA
            CLÁUSULA 4ª - DOS DIREITOS E DEVERES
            """,
            'empresarial': """
            CONTRATO EMPRESARIAL
            
            PARTES: [EMPRESAS_ENVOLVIDAS]
            
            CLÁUSULA 1ª - DO OBJETO SOCIAL
            CLÁUSULA 2ª - DAS RESPONSABILIDADES
            CLÁUSULA 3ª - DA GESTÃO
            CLÁUSULA 4ª - DA DISSOLUÇÃO
            """
        }
    
    def _get_petition_templates(self) -> Dict[str, str]:
        """Templates de petições"""
        return {
            'civil': """
            EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA [VARA]
            
            [NOME_AUTOR], [QUALIFICACAO], por meio de seu advogado que esta subscreve, vem respeitosamente à presença de Vossa Excelência propor
            
            AÇÃO [TIPO_ACAO]
            
            em face de [NOME_REU], [QUALIFICACAO], pelos fatos e fundamentos jurídicos a seguir expostos:
            
            I - DOS FATOS
            II - DO DIREITO
            III - DOS PEDIDOS
            """,
            'trabalhista': """
            EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DO TRABALHO DA [VARA]
            
            [NOME_RECLAMANTE], vem propor
            
            RECLAMAÇÃO TRABALHISTA
            
            em face de [NOME_RECLAMADA], pelos fatos que passa a expor:
            
            I - DA RELAÇÃO DE EMPREGO
            II - DOS DIREITOS PLEITEADOS
            III - DOS PEDIDOS
            """
        }
    
    def _get_legal_opinion_templates(self) -> Dict[str, str]:
        """Templates de pareceres"""
        return {
            'civil': "Template de parecer civil",
            'penal': "Template de parecer penal"
        }
    
    def _get_power_of_attorney_templates(self) -> Dict[str, str]:
        """Templates de procurações"""
        return {
            'civil': "Template de procuração civil"
        }
    
    def _get_appeal_templates(self) -> Dict[str, str]:
        """Templates de recursos"""
        return {
            'civil': "Template de recurso civil"
        }
    
    def _get_defense_templates(self) -> Dict[str, str]:
        """Templates de defesas"""
        return {
            'civil': "Template de defesa civil"
        }
    
    def _get_agreement_templates(self) -> Dict[str, str]:
        """Templates de acordos"""
        return {
            'civil': "Template de acordo civil"
        }
    
    def _get_notification_templates(self) -> Dict[str, str]:
        """Templates de notificações"""
        return {
            'civil': "Template de notificação civil"
        }
    
    def _get_contract_analysis_prompt(self) -> str:
        """Prompt sistema para análise de contratos"""
        return """
        Você é um especialista em análise de contratos jurídicos brasileiros. 
        Sua função é analisar documentos legais com foco em:
        - Compliance com a legislação brasileira
        - Identificação de riscos legais
        - Sugestões de melhorias
        - Verificação de cláusulas essenciais
        - Análise de linguagem jurídica apropriada
        
        Forneça análises detalhadas, práticas e baseadas na legislação vigente.
        """
    
    def _get_document_review_prompt(self) -> str:
        """Prompt sistema para revisão de documentos"""
        return """
        Você é um revisor jurídico especializado em documentos legais brasileiros.
        Analise documentos considerando:
        - Estrutura e formatação adequada
        - Correção da linguagem jurídica
        - Completude das informações
        - Conformidade com padrões legais
        - Identificação de inconsistências
        
        Seja preciso, detalhado e construtivo em suas análises.
        """
    
    def _get_legal_research_prompt(self) -> str:
        """Prompt sistema para pesquisa jurídica"""
        return """
        Você é um pesquisador jurídico especialista no direito brasileiro.
        Conduza pesquisas jurídicas focando em:
        - Legislação aplicável
        - Jurisprudência relevante
        - Doutrina especializada
        - Precedentes importantes
        - Tendências jurisprudenciais
        
        Forneça informações atualizadas, precisas e bem fundamentadas.
        """
    
    def _get_document_generation_prompt(self) -> str:
        """Prompt sistema para geração de documentos"""
        return """
        Você é um especialista em redação jurídica brasileira.
        Gere documentos jurídicos que sejam:
        - Tecnicamente corretos
        - Adequadamente estruturados
        - Conformes com a legislação
        - Redigidos em linguagem jurídica apropriada
        - Completos e abrangentes
        
        Use sempre a legislação brasileira vigente como referência.
        """
    
    def _get_clause_suggestion_prompt(self) -> str:
        """Prompt sistema para sugestão de cláusulas"""
        return """
        Você é um especialista em cláusulas contratuais do direito brasileiro.
        Sugira cláusulas que sejam:
        - Juridicamente válidas
        - Equilibradas entre as partes
        - Adequadas ao tipo de contrato
        - Protetivas dos interesses legítimos
        - Conformes com a legislação vigente
        
        Priorize sempre a segurança jurídica e a clareza.
        """
    
    # Métodos de fallback e utilitários...
    def _fallback_analysis(self, content: str, context: LegalContext) -> Dict[str, Any]:
        """Análise básica sem IA"""
        return {
            'status': 'fallback',
            'analysis': {
                'structure': 'Análise básica de estrutura - revisão manual recomendada',
                'compliance': 'Verificação de compliance necessária',
                'risks': 'Análise de riscos pendente'
            },
            'suggestions': ['Revisar com advogado especializado', 'Verificar legislação atualizada'],
            'risk_assessment': 'Pendente de análise profissional',
            'compliance_check': 'Requer verificação manual'
        }
    
    def _fallback_generation(self, document_type: DocumentType, legal_area: LegalArea, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Geração básica sem IA"""
        template = self.legal_templates.get(document_type, {}).get(legal_area.value, "Documento básico - requer personalização")
        
        return {
            'status': 'fallback',
            'content': template,
            'metadata': {
                'document_type': document_type.value,
                'legal_area': legal_area.value,
                'generated_at': datetime.utcnow().isoformat(),
                'parameters_used': parameters,
                'note': 'Template básico - personalização necessária'
            },
            'quality_score': 0.5
        }
    
    def _fallback_clause_suggestions(self, document_type: DocumentType, existing_content: str) -> Dict[str, Any]:
        """Sugestões básicas sem IA"""
        basic_suggestions = {
            DocumentType.CONTRATO: ['Cláusula de foro', 'Cláusula de vigência', 'Cláusula de rescisão', 'Cláusula de penalidades'],
            DocumentType.PETICAO: ['Fundamentação jurídica', 'Pedidos específicos', 'Qualificação das partes'],
            DocumentType.PROCURACAO: ['Poderes específicos', 'Prazo de validade', 'Substabelecimento']
        }
        
        suggestions = basic_suggestions.get(document_type, ['Cláusulas essenciais para validade jurídica'])
        
        return {
            'status': 'fallback',
            'suggestions': suggestions,
            'priority_clauses': ['Essenciais para validade jurídica'],
            'legal_precedents': [],
            'note': 'Sugestões básicas - consultoria jurídica recomendada'
        }
    
    def _fallback_legal_research(self, query: str, legal_area: LegalArea) -> Dict[str, Any]:
        """Pesquisa básica sem IA"""
        basic_sources = {
            LegalArea.CIVIL: ['Código Civil', 'CPC', 'Jurisprudência STJ'],
            LegalArea.TRABALHISTA: ['CLT', 'TST', 'Súmulas trabalhistas'],
            LegalArea.PENAL: ['Código Penal', 'CPP', 'STF jurisprudência']
        }
        
        sources = basic_sources.get(legal_area, ['Legislação específica', 'Jurisprudência aplicável'])
        
        return {
            'status': 'fallback',
            'research': {
                'summary': 'Pesquisa básica - aprofundamento recomendado',
                'key_points': [f'Consultar {source}' for source in sources],
                'recommendations': ['Buscar jurisprudência atualizada', 'Verificar alterações legislativas recentes']
            },
            'legal_references': sources,
            'related_topics': [],
            'note': 'Pesquisa preliminar - análise jurídica detalhada necessária'
        }
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parsear resposta de análise"""
        return {
            'structure': 'Análise estrutural do documento',
            'compliance': 'Avaliação de conformidade legal',
            'risks': 'Identificação de riscos jurídicos',
            'completeness': 'Análise de completude'
        }
    
    def _parse_clause_suggestions(self, response: str) -> List[Dict[str, str]]:
        """Parsear sugestões de cláusulas"""
        return [
            {'clause': 'Cláusula sugerida 1', 'importance': 'Alta', 'rationale': 'Justificativa legal'},
            {'clause': 'Cláusula sugerida 2', 'importance': 'Média', 'rationale': 'Proteção adicional'}
        ]
    
    def _parse_research_response(self, response: str) -> Dict[str, Any]:
        """Parsear resposta de pesquisa"""
        return {
            'summary': 'Resumo da pesquisa jurídica',
            'key_findings': 'Descobertas principais',
            'legal_basis': 'Fundamentação legal',
            'recommendations': 'Recomendações práticas'
        }
    
    def _generate_suggestions(self, analysis: Dict[str, Any], context: LegalContext) -> List[str]:
        """Gerar sugestões baseadas na análise"""
        return [
            'Revisar estrutura do documento',
            'Verificar conformidade legal',
            'Adicionar cláusulas de proteção'
        ]
    
    def _assess_risks(self, analysis: Dict[str, Any], context: LegalContext) -> str:
        """Avaliar riscos do documento"""
        return 'Risco médio - revisão recomendada'
    
    def _check_compliance(self, content: str, context: LegalContext) -> str:
        """Verificar compliance legal"""
        return 'Compliance parcial - verificação detalhada necessária'
    
    def _identify_priority_clauses(self, suggestions: List[Dict[str, str]], context: LegalContext) -> List[str]:
        """Identificar cláusulas prioritárias"""
        return ['Cláusulas essenciais identificadas']
    
    def _find_relevant_precedents(self, document_type: DocumentType, context: LegalContext) -> List[Dict[str, str]]:
        """Encontrar precedentes relevantes"""
        return [{'case': 'Precedente relevante', 'court': 'Tribunal', 'summary': 'Resumo'}]
    
    def _extract_legal_references(self, research_result: Dict[str, Any]) -> List[str]:
        """Extrair referências legais"""
        return ['Lei aplicável', 'Jurisprudência relevante']
    
    def _identify_related_topics(self, query: str, legal_area: LegalArea) -> List[str]:
        """Identificar tópicos relacionados"""
        return ['Tópico relacionado 1', 'Tópico relacionado 2']
    
    def _calculate_quality_score(self, content: str) -> float:
        """Calcular score de qualidade do documento"""
        # Métricas básicas de qualidade
        word_count = len(content.split())
        has_structure = bool(re.search(r'CLÁUSULA|ARTIGO|PARÁGRAFO', content, re.IGNORECASE))
        has_legal_terms = bool(re.search(r'CONSIDERANDO|RESOLVE|DETERMINA', content, re.IGNORECASE))
        has_formal_language = bool(re.search(r'EXCELENTÍSSIMO|MERITÍSSIMO|DOUTO', content, re.IGNORECASE))
        
        score = 0.2  # Base score
        if word_count > 100:
            score += 0.2
        if word_count > 500:
            score += 0.1
        if has_structure:
            score += 0.3
        if has_legal_terms:
            score += 0.2
        if has_formal_language:
            score += 0.2
        
        return min(score, 1.0)

# Instância global
legal_ai_service = LegalAIService() 