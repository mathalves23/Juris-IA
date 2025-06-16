"""
Chatbot Jurídico Especializado
Assistente inteligente para consultas jurídicas rápidas
"""
import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from enum import Enum
import random

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Tipos de consulta jurídica"""
    PROCEDURAL = "procedural"
    CONTRACTUAL = "contractual"
    CIVIL = "civil"
    CRIMINAL = "criminal"
    LABOR = "labor"
    CORPORATE = "corporate"
    TAX = "tax"
    CONSUMER = "consumer"
    FAMILY = "family"
    GENERAL = "general"

@dataclass
class ChatResponse:
    """Resposta do chatbot"""
    message: str
    confidence: float
    query_type: QueryType
    legal_references: List[Dict]
    suggestions: List[str]
    follow_up_questions: List[str]
    metadata: Dict

class LegalKnowledgeBase:
    """Base de conhecimento jurídico"""
    
    def __init__(self):
        # Base de conhecimento estruturada
        self.knowledge_base = {
            QueryType.PROCEDURAL: {
                'keywords': ['processo', 'prazo', 'petição', 'recurso', 'tribunal', 'juiz'],
                'responses': {
                    'prazo_recurso': {
                        'pattern': r'prazo.*recurso|recurso.*prazo',
                        'response': 'O prazo para recurso de apelação é de 15 dias, conforme art. 1003 do CPC. Para recursos especial e extraordinário, o prazo é de 15 dias após a publicação do acórdão.',
                        'references': [
                            {'law': 'CPC', 'article': 'Art. 1003', 'description': 'Prazo para apelação'},
                            {'law': 'CPC', 'article': 'Art. 1029', 'description': 'Prazo para recursos superiores'}
                        ]
                    },
                    'peticao_inicial': {
                        'pattern': r'petição inicial|inicial.*requisitos',
                        'response': 'A petição inicial deve conter: I) indicação do juízo; II) qualificação das partes; III) fatos e fundamentos jurídicos; IV) pedido; V) valor da causa; VI) provas, conforme art. 319 do CPC.',
                        'references': [
                            {'law': 'CPC', 'article': 'Art. 319', 'description': 'Requisitos da petição inicial'}
                        ]
                    }
                }
            },
            QueryType.CONTRACTUAL: {
                'keywords': ['contrato', 'cláusula', 'rescisão', 'multa', 'inadimplemento'],
                'responses': {
                    'rescisao_contrato': {
                        'pattern': r'rescisão.*contrato|rescindir.*contrato',
                        'response': 'A rescisão contratual pode ocorrer por: 1) Mútuo consentimento; 2) Inadimplemento de uma das partes; 3) Caso fortuito ou força maior; 4) Cláusula resolutiva expressa. Ver arts. 474 a 480 do Código Civil.',
                        'references': [
                            {'law': 'Código Civil', 'article': 'Arts. 474-480', 'description': 'Extinção dos contratos'}
                        ]
                    },
                    'clausula_penal': {
                        'pattern': r'cláusula penal|multa.*contrato',
                        'response': 'A cláusula penal não pode exceder o valor da obrigação principal (art. 412 CC). É reduzida proporcionalmente se a obrigação for cumprida em parte ou se for excessiva.',
                        'references': [
                            {'law': 'Código Civil', 'article': 'Art. 412', 'description': 'Limite da cláusula penal'}
                        ]
                    }
                }
            },
            QueryType.LABOR: {
                'keywords': ['trabalhista', 'empregado', 'salário', 'demissão', 'férias', 'rescisão'],
                'responses': {
                    'aviso_previo': {
                        'pattern': r'aviso prévio|demissão.*aviso',
                        'response': 'O aviso prévio é de 30 dias, acrescido de 3 dias por ano de serviço, até o máximo de 90 dias (Lei 12.506/2011). Pode ser trabalhado ou indenizado.',
                        'references': [
                            {'law': 'CLT', 'article': 'Art. 487', 'description': 'Aviso prévio'},
                            {'law': 'Lei 12.506/2011', 'article': 'Art. 1º', 'description': 'Proporcionalidade do aviso prévio'}
                        ]
                    },
                    'ferias': {
                        'pattern': r'férias.*direito|período.*férias',
                        'response': 'O empregado tem direito a 30 dias de férias a cada 12 meses de trabalho. As férias devem ser concedidas nos 12 meses seguintes ao período aquisitivo (art. 134 CLT).',
                        'references': [
                            {'law': 'CLT', 'article': 'Art. 129', 'description': 'Direito a férias'},
                            {'law': 'CLT', 'article': 'Art. 134', 'description': 'Época da concessão'}
                        ]
                    }
                }
            },
            QueryType.CIVIL: {
                'keywords': ['dano', 'responsabilidade', 'indenização', 'posse', 'propriedade'],
                'responses': {
                    'dano_moral': {
                        'pattern': r'dano moral|indenização.*moral',
                        'response': 'O dano moral é a lesão a direitos da personalidade. Não requer prova do prejuízo, sendo presumido. O valor deve ser fixado considerando gravidade da ofensa, condição das partes e caráter educativo.',
                        'references': [
                            {'law': 'Código Civil', 'article': 'Art. 186', 'description': 'Ato ilícito'},
                            {'law': 'Código Civil', 'article': 'Art. 927', 'description': 'Obrigação de indenizar'}
                        ]
                    },
                    'usucapiao': {
                        'pattern': r'usucapião|posse.*tempo',
                        'response': 'Usucapião extraordinária: 15 anos de posse mansa e pacífica. Usucapião ordinária: 10 anos com justo título e boa-fé. Prazos podem ser reduzidos com moradia ou investimentos produtivos.',
                        'references': [
                            {'law': 'Código Civil', 'article': 'Art. 1238', 'description': 'Usucapião extraordinária'},
                            {'law': 'Código Civil', 'article': 'Art. 1242', 'description': 'Usucapião ordinária'}
                        ]
                    }
                }
            },
            QueryType.CONSUMER: {
                'keywords': ['consumidor', 'fornecedor', 'produto', 'serviço', 'garantia', 'vício'],
                'responses': {
                    'direito_arrependimento': {
                        'pattern': r'arrependimento|desistir.*compra',
                        'response': 'O consumidor pode desistir de compra feita fora do estabelecimento comercial em 7 dias, sem justificativa (art. 49 CDC). Aplica-se a compras online, telefone, domicílio.',
                        'references': [
                            {'law': 'CDC', 'article': 'Art. 49', 'description': 'Direito de arrependimento'}
                        ]
                    },
                    'vicio_produto': {
                        'pattern': r'vício.*produto|defeito.*produto',
                        'response': 'O fornecedor tem 30 dias (produtos não duráveis) ou 90 dias (produtos duráveis) para sanar vícios de qualidade. Não sanado, o consumidor pode exigir substituição, restituição ou abatimento proporcional.',
                        'references': [
                            {'law': 'CDC', 'article': 'Art. 26', 'description': 'Prazo para reclamação'},
                            {'law': 'CDC', 'article': 'Art. 18', 'description': 'Vícios de qualidade'}
                        ]
                    }
                }
            }
        }
        
        # Respostas genéricas para casos não específicos
        self.generic_responses = [
            "Para uma análise precisa do seu caso, recomendo consultar um advogado especializado na área.",
            "Cada situação tem particularidades. É importante buscar orientação jurídica personalizada.",
            "A legislação brasileira é extensa. Para sua situação específica, procure um profissional habilitado."
        ]
        
        # FAQ comum
        self.faq = {
            'como_encontrar_advogado': 'Você pode encontrar advogados através da OAB de seu estado, consulte o site da seccional local.',
            'quanto_custa_advogado': 'Os honorários advocatícios variam conforme a complexidade do caso e região. Consulte a tabela da OAB local.',
            'assistencia_juridica_gratuita': 'Quem não pode pagar advogado tem direito à assistência jurídica gratuita através da Defensoria Pública.',
            'como_entrar_processo': 'Para ingressar com ação judicial, é necessário contratar advogado, exceto em Juizados Especiais (causas até 20 salários mínimos).'
        }

class LegalChatbot:
    """Chatbot jurídico inteligente"""
    
    def __init__(self):
        self.knowledge_base = LegalKnowledgeBase()
        self.conversation_history = []
        self.user_context = {}
        
        # Padrões para identificação de consultas
        self.intent_patterns = {
            'greeting': [r'oi', r'olá', r'bom dia', r'boa tarde', r'boa noite'],
            'thanks': [r'obrigad[oa]', r'valeu', r'muito obrigad[oa]'],
            'help': [r'ajuda', r'como funciona', r'o que você faz'],
            'legal_query': [r'posso', r'tenho direito', r'é legal', r'é permitido', r'como proceder'],
            'procedure': [r'como fazer', r'qual procedimento', r'passos', r'etapas'],
            'deadline': [r'prazo', r'quando', r'até quando', r'tempo limite'],
            'cost': [r'quanto custa', r'valor', r'preço', r'honorários'],
            'document': [r'documento', r'modelo', r'template', r'petição']
        }
    
    def process_query(self, user_input: str, user_id: Optional[str] = None) -> ChatResponse:
        """Processar consulta do usuário"""
        
        # Normalizar entrada
        normalized_input = self._normalize_input(user_input)
        
        # Identificar intenção
        intent = self._identify_intent(normalized_input)
        
        # Identificar tipo de consulta jurídica
        query_type = self._classify_legal_query(normalized_input)
        
        # Gerar resposta baseada na intenção
        if intent == 'greeting':
            response = self._handle_greeting()
        elif intent == 'thanks':
            response = self._handle_thanks()
        elif intent == 'help':
            response = self._handle_help()
        else:
            response = self._handle_legal_query(normalized_input, query_type)
        
        # Salvar no histórico
        self._update_conversation_history(user_input, response, user_id)
        
        return response
    
    def _normalize_input(self, text: str) -> str:
        """Normalizar entrada do usuário"""
        # Converter para minúsculas
        text = text.lower()
        
        # Remover caracteres especiais desnecessários
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remover espaços extras
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _identify_intent(self, text: str) -> str:
        """Identificar intenção do usuário"""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return intent
        
        return 'legal_query'
    
    def _classify_legal_query(self, text: str) -> QueryType:
        """Classificar tipo de consulta jurídica"""
        scores = {}
        
        for query_type, data in self.knowledge_base.knowledge_base.items():
            score = 0
            for keyword in data['keywords']:
                if keyword in text:
                    score += 1
            scores[query_type] = score
        
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return QueryType.GENERAL
    
    def _handle_greeting(self) -> ChatResponse:
        """Lidar com cumprimentos"""
        greetings = [
            "Olá! Sou seu assistente jurídico. Como posso ajudá-lo hoje?",
            "Oi! Estou aqui para esclarecer suas dúvidas jurídicas. O que gostaria de saber?",
            "Olá! Pode me consultar sobre questões de direito brasileiro. Em que posso ajudar?"
        ]
        
        return ChatResponse(
            message=random.choice(greetings),
            confidence=1.0,
            query_type=QueryType.GENERAL,
            legal_references=[],
            suggestions=[
                "Dúvidas sobre contratos",
                "Questões trabalhistas",
                "Direitos do consumidor",
                "Processos judiciais"
            ],
            follow_up_questions=[
                "Sobre qual área do direito você gostaria de saber?",
                "Tem alguma situação específica em mente?"
            ],
            metadata={'type': 'greeting'}
        )
    
    def _handle_thanks(self) -> ChatResponse:
        """Lidar com agradecimentos"""
        thanks_responses = [
            "De nada! Fico feliz em ajudar com suas dúvidas jurídicas.",
            "Por nada! Estou sempre aqui para esclarecer questões legais.",
            "É um prazer ajudar! Lembre-se: para casos específicos, consulte sempre um advogado."
        ]
        
        return ChatResponse(
            message=random.choice(thanks_responses),
            confidence=1.0,
            query_type=QueryType.GENERAL,
            legal_references=[],
            suggestions=[
                "Tem mais alguma dúvida?",
                "Precisa de orientação para encontrar um advogado?",
                "Quer saber sobre assistência jurídica gratuita?"
            ],
            follow_up_questions=[],
            metadata={'type': 'thanks'}
        )
    
    def _handle_help(self) -> ChatResponse:
        """Lidar com pedidos de ajuda"""
        help_message = """
        Sou um assistente jurídico especializado em direito brasileiro. Posso ajudar com:
        
        📋 **Informações gerais** sobre leis e procedimentos
        ⚖️ **Direitos e deveres** em diferentes situações
        📝 **Orientações sobre documentos** e prazos
        🏢 **Questões trabalhistas, contratuais e do consumidor**
        
        ⚠️ **Importante**: Minhas respostas são informativas. Para casos específicos, sempre consulte um advogado.
        """
        
        return ChatResponse(
            message=help_message,
            confidence=1.0,
            query_type=QueryType.GENERAL,
            legal_references=[],
            suggestions=[
                "Como encontrar um advogado?",
                "Assistência jurídica gratuita",
                "Prazos processuais",
                "Direitos do trabalhador"
            ],
            follow_up_questions=[
                "Sobre qual área específica você gostaria de saber mais?"
            ],
            metadata={'type': 'help'}
        )
    
    def _handle_legal_query(self, text: str, query_type: QueryType) -> ChatResponse:
        """Lidar com consultas jurídicas"""
        
        # Buscar resposta específica na base de conhecimento
        if query_type in self.knowledge_base.knowledge_base:
            knowledge = self.knowledge_base.knowledge_base[query_type]
            
            for response_key, response_data in knowledge['responses'].items():
                pattern = response_data['pattern']
                if re.search(pattern, text):
                    return ChatResponse(
                        message=response_data['response'],
                        confidence=0.9,
                        query_type=query_type,
                        legal_references=response_data['references'],
                        suggestions=self._generate_suggestions(query_type),
                        follow_up_questions=self._generate_follow_up_questions(query_type),
                        metadata={'matched_pattern': pattern, 'response_key': response_key}
                    )
        
        # Verificar FAQ
        faq_response = self._check_faq(text)
        if faq_response:
            return faq_response
        
        # Resposta genérica se não encontrar match específico
        return self._generate_generic_response(query_type, text)
    
    def _check_faq(self, text: str) -> Optional[ChatResponse]:
        """Verificar FAQ"""
        for faq_key, faq_answer in self.knowledge_base.faq.items():
            # Criar padrão baseado na chave
            pattern = faq_key.replace('_', '.*')
            if re.search(pattern, text):
                return ChatResponse(
                    message=faq_answer,
                    confidence=0.8,
                    query_type=QueryType.GENERAL,
                    legal_references=[],
                    suggestions=["Como posso ajudar mais?"],
                    follow_up_questions=["Tem outras dúvidas?"],
                    metadata={'type': 'faq', 'faq_key': faq_key}
                )
        return None
    
    def _generate_generic_response(self, query_type: QueryType, text: str) -> ChatResponse:
        """Gerar resposta genérica"""
        
        # Tentar extrair palavras-chave importantes
        keywords = self._extract_keywords(text)
        
        generic_message = random.choice(self.knowledge_base.generic_responses)
        
        if keywords:
            generic_message += f"\n\nPalavras-chave identificadas: {', '.join(keywords[:3])}"
        
        generic_message += "\n\n💡 **Dica**: Seja mais específico com sua pergunta para obter uma resposta mais precisa."
        
        return ChatResponse(
            message=generic_message,
            confidence=0.3,
            query_type=query_type,
            legal_references=[],
            suggestions=self._generate_suggestions(query_type),
            follow_up_questions=[
                "Pode detalhar melhor sua situação?",
                "Que tipo de orientação específica você precisa?"
            ],
            metadata={'type': 'generic', 'keywords': keywords}
        )
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrair palavras-chave do texto"""
        # Palavras jurídicas importantes
        legal_keywords = [
            'contrato', 'processo', 'tribunal', 'advogado', 'recurso', 'petição',
            'prazo', 'multa', 'indenização', 'dano', 'direito', 'obrigação',
            'trabalhista', 'empregado', 'salário', 'demissão', 'consumidor',
            'produto', 'serviço', 'garantia', 'civil', 'criminal', 'penal'
        ]
        
        found_keywords = []
        for keyword in legal_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _generate_suggestions(self, query_type: QueryType) -> List[str]:
        """Gerar sugestões baseadas no tipo de consulta"""
        suggestions_map = {
            QueryType.PROCEDURAL: [
                "Prazos processuais",
                "Como interpor recurso",
                "Requisitos da petição inicial",
                "Custas judiciais"
            ],
            QueryType.CONTRACTUAL: [
                "Rescisão de contrato",
                "Cláusulas abusivas",
                "Inadimplemento contratual",
                "Tipos de contrato"
            ],
            QueryType.LABOR: [
                "Direitos do trabalhador",
                "Demissão e rescisão",
                "Horas extras",
                "Assédio no trabalho"
            ],
            QueryType.CONSUMER: [
                "Direitos do consumidor",
                "Troca e devolução",
                "Garantia de produtos",
                "Cobrança indevida"
            ],
            QueryType.CIVIL: [
                "Responsabilidade civil",
                "Danos morais",
                "Direitos reais",
                "Usucapião"
            ]
        }
        
        return suggestions_map.get(query_type, [
            "Encontrar advogado",
            "Assistência jurídica gratuita",
            "Tipos de processo",
            "Direitos básicos"
        ])
    
    def _generate_follow_up_questions(self, query_type: QueryType) -> List[str]:
        """Gerar perguntas de acompanhamento"""
        follow_up_map = {
            QueryType.PROCEDURAL: [
                "Você já tem um processo em andamento?",
                "Precisa de orientação sobre prazos específicos?"
            ],
            QueryType.CONTRACTUAL: [
                "Que tipo de contrato está em questão?",
                "Já tentou resolver amigavelmente?"
            ],
            QueryType.LABOR: [
                "Você é empregado ou empregador?",
                "A situação já foi comunicada ao RH?"
            ],
            QueryType.CONSUMER: [
                "Já tentou contato com o fornecedor?",
                "Tem nota fiscal do produto/serviço?"
            ]
        }
        
        return follow_up_map.get(query_type, [
            "Gostaria de mais detalhes sobre algum ponto?",
            "Precisa de orientação sobre próximos passos?"
        ])
    
    def _update_conversation_history(self, user_input: str, response: ChatResponse, user_id: Optional[str]):
        """Atualizar histórico da conversa"""
        conversation_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'user_input': user_input,
            'response': response.message,
            'query_type': response.query_type.value,
            'confidence': response.confidence
        }
        
        self.conversation_history.append(conversation_entry)
        
        # Manter apenas últimas 50 interações
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def get_conversation_summary(self, user_id: str) -> Dict:
        """Obter resumo da conversa do usuário"""
        user_conversations = [
            conv for conv in self.conversation_history 
            if conv.get('user_id') == user_id
        ]
        
        if not user_conversations:
            return {'message': 'Nenhuma conversa encontrada'}
        
        # Estatísticas
        query_types = [conv['query_type'] for conv in user_conversations]
        most_common_type = max(set(query_types), key=query_types.count)
        
        return {
            'total_queries': len(user_conversations),
            'most_common_query_type': most_common_type,
            'average_confidence': sum(conv['confidence'] for conv in user_conversations) / len(user_conversations),
            'last_interaction': user_conversations[-1]['timestamp'],
            'conversation_history': user_conversations[-10:]  # Últimas 10 interações
        }

# Função principal para usar o chatbot
def ask_legal_question(question: str, user_id: Optional[str] = None) -> Dict:
    """Função principal para fazer perguntas ao chatbot jurídico"""
    chatbot = LegalChatbot()
    
    try:
        response = chatbot.process_query(question, user_id)
        
        return {
            'success': True,
            'response': response.message,
            'confidence': response.confidence,
            'query_type': response.query_type.value,
            'legal_references': response.legal_references,
            'suggestions': response.suggestions,
            'follow_up_questions': response.follow_up_questions,
            'metadata': response.metadata
        }
    
    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        return {
            'success': False,
            'error': str(e),
            'fallback_message': 'Desculpe, ocorreu um erro. Tente reformular sua pergunta ou consulte um advogado.'
        } 