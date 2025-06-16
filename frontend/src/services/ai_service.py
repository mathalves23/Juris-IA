from openai import OpenAI
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import logging
import asyncio
from datetime import datetime
from src.config import Config

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Tipos de documentos jurídicos."""
    PETICAO_INICIAL = "peticao_inicial"
    CONTRATO = "contrato"
    RECURSO = "recurso"
    PARECER = "parecer"
    PROCURACAO = "procuracao"
    DEFESA = "defesa"
    MEMORIAIS = "memoriais"
    ALEGACOES = "alegacoes"


class AITask(Enum):
    """Tipos de tarefas de IA."""
    GENERATE = "generate"
    REVIEW = "review"
    SUMMARIZE = "summarize"
    TRANSLATE = "translate"
    OPTIMIZE = "optimize"
    VALIDATE = "validate"


@dataclass
class AIRequest:
    """Estrutura de requisição para IA."""
    task: AITask
    content: str
    document_type: Optional[DocumentType] = None
    context: Optional[Dict] = None
    user_id: Optional[int] = None
    language: str = "pt-BR"


@dataclass
class AIResponse:
    """Estrutura de resposta da IA."""
    success: bool
    content: str
    metadata: Dict
    suggestions: List[str]
    confidence: float
    processing_time: float
    tokens_used: int


class LegalAIService:
    """Serviço avançado de IA jurídica."""
    
    def __init__(self):
        self.client = None
        if Config.is_openai_configured():
            self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Templates de contexto jurídico
        self.legal_contexts = {
            DocumentType.PETICAO_INICIAL: {
                "context": "Você é especialista em petições iniciais do direito brasileiro",
                "instructions": "Estruture conforme CPC, inclua fundamentação jurídica sólida",
                "required_sections": ["qualificação", "fatos", "direito", "pedidos"]
            },
            DocumentType.CONTRATO: {
                "context": "Você é especialista em contratos do direito civil brasileiro",
                "instructions": "Inclua cláusulas essenciais, observando o Código Civil",
                "required_sections": ["partes", "objeto", "preço", "prazo", "rescisão"]
            }
        }
    
    async def process_request(self, request: AIRequest) -> AIResponse:
        """Processar requisição de IA."""
        start_time = datetime.now()
        
        try:
            if request.task == AITask.GENERATE:
                response = await self._generate_content(request)
            elif request.task == AITask.REVIEW:
                response = await self._review_content(request)
            elif request.task == AITask.SUMMARIZE:
                response = await self._summarize_content(request)
            else:
                raise ValueError(f"Tarefa não suportada: {request.task}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            response.processing_time = processing_time
            
            return response
            
        except Exception as e:
            logger.error(f"Erro no processamento de IA: {str(e)}")
            return AIResponse(
                success=False,
                content=f"Erro no processamento: {str(e)}",
                metadata={"error": str(e)},
                suggestions=[],
                confidence=0.0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                tokens_used=0
            )
    
    async def _generate_content(self, request: AIRequest) -> AIResponse:
        """Gerar conteúdo jurídico."""
        if not self.client:
            return self._fallback_generation(request)
        
        # Preparar contexto específico
        context = self._build_legal_context(request)
        
        # Criar prompt otimizado
        prompt = self._build_optimized_prompt(request, context)
        
        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": context.get("system_prompt", "Você é um assistente jurídico especializado.")},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=Config.OPENAI_MAX_TOKENS,
                temperature=Config.OPENAI_TEMPERATURE
            )
            
            generated_content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            return AIResponse(
                success=True,
                content=generated_content,
                metadata={"model": Config.OPENAI_MODEL, "tokens": tokens_used},
                suggestions=[],
                confidence=0.85,
                processing_time=0.0,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            logger.error(f"Erro na geração OpenAI: {str(e)}")
            return self._fallback_generation(request)
    
    async def _review_content(self, request: AIRequest) -> AIResponse:
        """Revisar conteúdo jurídico."""
        content = request.content
        suggestions = []
        
        # Verificações básicas
        if len(content) < 100:
            suggestions.append("Conteúdo muito curto - considere expandir")
        
        if not re.search(r'[.!?]$', content.strip()):
            suggestions.append("Documento deve terminar com pontuação adequada")
        
        return AIResponse(
            success=True,
            content="Revisão concluída",
            metadata={"issues_found": len(suggestions)},
            suggestions=suggestions,
            confidence=0.90,
            processing_time=0.0,
            tokens_used=0
        )
    
    async def _summarize_content(self, request: AIRequest) -> AIResponse:
        """Resumir conteúdo jurídico."""
        content = request.content
        
        # Resumo básico
        sentences = content.split('.')
        key_sentences = sentences[:3] if len(sentences) > 3 else sentences
        summary = '. '.join(key_sentences) + '.'
        
        return AIResponse(
            success=True,
            content=summary,
            metadata={"original_length": len(content), "summary_length": len(summary)},
            suggestions=[],
            confidence=0.80,
            processing_time=0.0,
            tokens_used=0
        )
    
    def _build_legal_context(self, request: AIRequest) -> Dict:
        """Construir contexto jurídico específico."""
        base_context = {
            "system_prompt": "Você é um assistente jurídico especializado em direito brasileiro."
        }
        
        if request.document_type and request.document_type in self.legal_contexts:
            doc_context = self.legal_contexts[request.document_type]
            base_context.update(doc_context)
        
        return base_context
    
    def _build_optimized_prompt(self, request: AIRequest, context: Dict) -> str:
        """Construir prompt otimizado."""
        prompt_parts = []
        
        prompt_parts.append(f"Tarefa: {request.task.value}")
        
        if "instructions" in context:
            prompt_parts.append(f"Instruções: {context['instructions']}")
        
        if request.document_type:
            prompt_parts.append(f"Tipo de documento: {request.document_type.value}")
        
        prompt_parts.append(f"Conteúdo: {request.content}")
        prompt_parts.append("Gere um texto em português brasileiro, com linguagem jurídica formal.")
        
        return "\n\n".join(prompt_parts)
    
    def _fallback_generation(self, request: AIRequest) -> AIResponse:
        """Geração de fallback quando OpenAI não está disponível."""
        fallback_templates = {
            "contrato": """
            CONTRATO DE PRESTAÇÃO DE SERVIÇOS
            
            Por este instrumento particular, as partes:
            CONTRATANTE: [NOME E QUALIFICAÇÃO]
            CONTRATADO: [NOME E QUALIFICAÇÃO]
            
            Têm entre si justo e acordado o seguinte:
            
            CLÁUSULA 1ª - DO OBJETO
            O presente contrato tem por objeto [DESCRIÇÃO].
            
            CLÁUSULA 2ª - DO VALOR
            O valor dos serviços será de R$ [VALOR].
            """,
            
            "peticao": """
            EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO
            
            [NOME DO AUTOR] vem, respeitosamente, propor a presente
            
            AÇÃO [TIPO]
            
            em face de [NOME DO RÉU], pelos fatos a seguir expostos:
            
            DOS FATOS
            [DESCRIÇÃO DOS FATOS]
            
            DOS PEDIDOS
            Requer-se o deferimento dos pedidos.
            """
        }
        
        content_lower = request.content.lower()
        template_key = "contrato" if "contrato" in content_lower else "peticao"
        generated_content = fallback_templates.get(template_key, "Conteúdo jurídico gerado.")
        
        return AIResponse(
            success=True,
            content=generated_content,
            metadata={"source": "fallback_template"},
            suggestions=["Configure OpenAI para funcionalidade completa"],
            confidence=0.60,
            processing_time=0.0,
            tokens_used=0
        ) 