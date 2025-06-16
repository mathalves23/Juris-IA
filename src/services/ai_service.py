"""
Serviço de Inteligência Artificial para processamento de documentos jurídicos
Integração com OpenAI GPT-4 para funcionalidades avançadas de IA jurídica
"""
from enum import Enum
from typing import Optional, Dict, Any, List
import json
import time
import os
from dataclasses import dataclass
from openai import OpenAI
from src.config import Config


class DocumentType(Enum):
    CONTRATO = "contrato"
    PETICAO_INICIAL = "peticao"
    PARECER = "parecer"
    ATA = "ata"
    PROCURACAO = "procuracao"
    RECURSO = "recurso"
    OUTROS = "outros"


class AITask(Enum):
    GENERATE = "generate"
    REVIEW = "review"
    SUMMARIZE = "summarize"
    ANALYZE = "analyze"
    CORRECT = "correct"
    EXTRACT_VARIABLES = "extract_variables"


@dataclass
class AIRequest:
    task: AITask
    content: str
    document_type: Optional[DocumentType] = None
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


@dataclass 
class AIResponse:
    success: bool
    content: str
    suggestions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None


class LegalAIService:
    def __init__(self):
        """Inicializa o serviço de IA com configurações OpenAI"""
        self.openai_api_key = Config.OPENAI_API_KEY
        self.model = Config.OPENAI_MODEL
        self.max_tokens = Config.OPENAI_MAX_TOKENS
        self.temperature = Config.OPENAI_TEMPERATURE
        
        # Inicializar cliente OpenAI
        if self.openai_api_key and self.openai_api_key.startswith('sk-'):
            self.client = OpenAI(api_key=self.openai_api_key)
            self.is_configured = True
            print("✅ OpenAI configurado e pronto para uso")
        else:
            self.client = None
            self.is_configured = False
            print("⚠️ OpenAI não configurado - usando respostas mock")
        
    async def process_request(self, request: AIRequest) -> AIResponse:
        """
        Processa uma solicitação de IA de forma assíncrona
        """
        start_time = time.time()
        
        try:
            if not self.is_configured:
                return self._create_mock_response(request, start_time)
            
            # Usar configurações da requisição ou padrão
            max_tokens = request.max_tokens or self.max_tokens
            temperature = request.temperature or self.temperature
            
            # Construir prompt baseado na tarefa
            system_prompt, user_prompt = self._build_prompts(request)
            
            # Fazer chamada para OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            processing_time = time.time() - start_time
            content = response.choices[0].message.content
            
            # Extrair sugestões se aplicável
            suggestions = self._extract_suggestions(content, request.task)
            
            return AIResponse(
                success=True,
                content=content,
                suggestions=suggestions,
                metadata={
                    "model": self.model,
                    "tokens_used": response.usage.total_tokens,
                    "task": request.task.value,
                    "document_type": request.document_type.value if request.document_type else None
                },
                confidence=0.85,  # Placeholder - poderia ser calculado baseado na resposta
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Erro na IA: {str(e)}"
            print(f"❌ {error_msg}")
            
            return AIResponse(
                success=False,
                content="",
                error=error_msg,
                metadata={
                    "task": request.task.value,
                    "document_type": request.document_type.value if request.document_type else None
                },
                processing_time=processing_time
            )
    
    def _build_prompts(self, request: AIRequest) -> tuple[str, str]:
        """
        Constrói prompts system e user baseados na tarefa e tipo de documento
        """
        # Prompt do sistema baseado no tipo de documento
        doc_context = ""
        if request.document_type:
            doc_contexts = {
                DocumentType.CONTRATO: "contratos e acordos comerciais",
                DocumentType.PETICAO_INICIAL: "petições iniciais e peças processuais",
                DocumentType.PARECER: "pareceres e análises jurídicas",
                DocumentType.PROCURACAO: "procurações e documentos de representação",
                DocumentType.RECURSO: "recursos e peças recursais",
                DocumentType.ATA: "atas e documentos corporativos"
            }
            doc_context = f" especializado em {doc_contexts.get(request.document_type, 'documentos jurídicos')}"
        
        system_prompt = f"""Você é um assistente jurídico especializado{doc_context}, com expertise em direito brasileiro.
        
        Suas responsabilidades incluem:
        - Elaborar documentos juridicamente precisos e bem fundamentados
        - Seguir as normas da ABNT e padrões jurídicos brasileiros
        - Usar linguagem técnica apropriada mas clara
        - Considerar legislação e jurisprudência atualizadas
        - Manter confidencialidade e ética profissional
        
        Sempre forneça respostas detalhadas, fundamentadas e profissionais."""
        
        # Prompt do usuário baseado na tarefa
        task_prompts = {
            AITask.GENERATE: self._build_generate_prompt(request),
            AITask.REVIEW: self._build_review_prompt(request),
            AITask.SUMMARIZE: self._build_summarize_prompt(request),
            AITask.ANALYZE: self._build_analyze_prompt(request),
            AITask.CORRECT: self._build_correct_prompt(request),
            AITask.EXTRACT_VARIABLES: self._build_extract_variables_prompt(request)
        }
        
        user_prompt = task_prompts.get(request.task, self._build_default_prompt(request))
        
        return system_prompt, user_prompt
    
    def _build_generate_prompt(self, request: AIRequest) -> str:
        context_info = ""
        if request.context:
            context_info = f"\n\nContexto adicional:\n{json.dumps(request.context, indent=2, ensure_ascii=False)}"
        
        return f"""Gere um documento jurídico completo baseado no seguinte prompt:

{request.content}

Tipo de documento: {request.document_type.value if request.document_type else 'Não especificado'}
{context_info}

Por favor, elabore um documento profissional, bem estruturado e juridicamente fundamentado."""

    def _build_review_prompt(self, request: AIRequest) -> str:
        return f"""Revise o seguinte documento jurídico e forneça uma análise detalhada:

{request.content}

Por favor, identifique:
1. Erros gramaticais e de formatação
2. Problemas jurídicos ou inconsistências
3. Sugestões de melhoria
4. Cláusulas que podem ser aprimoradas
5. Conformidade com normas jurídicas brasileiras

Forneça sua análise de forma estruturada e construtiva."""

    def _build_summarize_prompt(self, request: AIRequest) -> str:
        return f"""Faça um resumo executivo do seguinte documento jurídico:

{request.content}

O resumo deve incluir:
1. Objetivo principal do documento
2. Partes envolvidas
3. Principais cláusulas e condições
4. Direitos e obrigações
5. Prazos e valores relevantes
6. Pontos de atenção importantes

Mantenha o resumo claro, objetivo e informativo."""

    def _build_analyze_prompt(self, request: AIRequest) -> str:
        return f"""Analise o seguinte documento jurídico sob uma perspectiva técnica:

{request.content}

Por favor, forneça:
1. Análise de riscos jurídicos
2. Pontos fortes e fracos
3. Oportunidades de melhoria
4. Conformidade legal
5. Recomendações estratégicas
6. Possíveis consequências legais

Sua análise deve ser detalhada e fundamentada."""

    def _build_correct_prompt(self, request: AIRequest) -> str:
        return f"""Corrija e aprimore o seguinte documento jurídico:

{request.content}

Por favor:
1. Corrija erros gramaticais e ortográficos
2. Melhore a estrutura e formatação
3. Ajuste a linguagem jurídica quando necessário
4. Aprimore a clareza e precisão
5. Mantenha o sentido original

Forneça o documento corrigido e uma lista das principais alterações realizadas."""

    def _build_extract_variables_prompt(self, request: AIRequest) -> str:
        return f"""Analise o seguinte template/documento e extraia todas as variáveis que devem ser preenchidas:

{request.content}

Identifique:
1. Campos que precisam ser preenchidos (como nomes, datas, valores)
2. Variáveis marcadas com {{{{ }}}}, [ ], ou similar
3. Informações que variam entre documentos similares
4. Dados pessoais, empresariais ou específicos do caso

Liste as variáveis de forma organizada, indicando o tipo de informação esperada para cada uma."""

    def _build_default_prompt(self, request: AIRequest) -> str:
        return f"""Processe o seguinte conteúdo jurídico conforme solicitado:

{request.content}

Tarefa: {request.task.value}
Tipo de documento: {request.document_type.value if request.document_type else 'Não especificado'}

Forneça uma resposta profissional e detalhada."""
    
    def _extract_suggestions(self, content: str, task: AITask) -> List[str]:
        """Extrai sugestões da resposta da IA"""
        suggestions = []
        
        # Heurísticas simples para extrair sugestões baseadas na tarefa
        if task == AITask.REVIEW:
            if "sugestão" in content.lower() or "recomendo" in content.lower():
                lines = content.split('\n')
                for line in lines:
                    if any(word in line.lower() for word in ["sugestão", "recomendo", "melhorar", "considere"]):
                        suggestions.append(line.strip())
        
        return suggestions[:5]  # Limitar a 5 sugestões
    
    def _create_mock_response(self, request: AIRequest, start_time: float) -> AIResponse:
        """Cria resposta mock quando OpenAI não está configurado"""
        processing_time = time.time() - start_time
        
        mock_responses = {
            AITask.GENERATE: "Este é um documento jurídico gerado pela IA. O conteúdo seria personalizado baseado no prompt fornecido e seguiria as melhores práticas do direito brasileiro.",
            AITask.REVIEW: "Revisão concluída. O documento apresenta estrutura adequada com algumas oportunidades de melhoria na linguagem jurídica e organização das cláusulas.",
            AITask.SUMMARIZE: "Resumo: Este documento estabelece termos e condições entre as partes, define direitos e obrigações, e apresenta cláusulas de execução e rescisão.",
            AITask.ANALYZE: "Análise jurídica: O documento apresenta baixo a médio risco, com cláusulas bem estruturadas. Recomenda-se revisão de alguns pontos específicos.",
            AITask.CORRECT: "Correções aplicadas com sucesso. Principais ajustes: formatação, linguagem jurídica e estrutura de parágrafos.",
            AITask.EXTRACT_VARIABLES: "Variáveis identificadas: nome_contratante, nome_contratado, data_assinatura, valor_contrato, prazo_vigencia."
        }
        
        return AIResponse(
            success=True,
            content=mock_responses.get(request.task, "Processamento concluído com resposta simulada."),
            suggestions=["Esta é uma resposta simulada", "Configure OpenAI para respostas reais"],
            metadata={
                "mock": True,
                "task": request.task.value,
                "document_type": request.document_type.value if request.document_type else None
            },
            confidence=0.5,
            processing_time=processing_time
        )
    
    def extract_variables(self, texto: str) -> List[str]:
        """
        Extrai variáveis de um template (placeholders como {{variavel}})
        """
        import re
        pattern = r'\{\{([^}]+)\}\}'
        variables = re.findall(pattern, texto)
        return list(set(variables))  # Remove duplicatas
    
    def fill_template(self, template: str, variables: Dict[str, str]) -> str:
        """
        Preenche um template com as variáveis fornecidas
        """
        resultado = template
        for var, value in variables.items():
            placeholder = f"{{{{{var}}}}}"
            resultado = resultado.replace(placeholder, value)
        return resultado
    
    async def extract_variables_ai(self, content: str) -> List[str]:
        """
        Usa IA para extrair variáveis de um documento de forma inteligente
        """
        request = AIRequest(
            task=AITask.EXTRACT_VARIABLES,
            content=content
        )
        
        response = await self.process_request(request)
        
        if response.success:
            # Processar resposta da IA para extrair lista de variáveis
            variables = []
            lines = response.content.split('\n')
            for line in lines:
                if ':' in line and any(keyword in line.lower() for keyword in ['variável', 'campo', 'preencher']):
                    var_name = line.split(':')[0].strip()
                    variables.append(var_name)
            
            return variables
        
        # Fallback para método regex se IA falhar
        return self.extract_variables(content) 