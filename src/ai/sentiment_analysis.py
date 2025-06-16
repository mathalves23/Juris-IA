"""
Análise de Sentimento Jurídico
Detecta tons agressivos, conciliatórios e neutros em documentos jurídicos
"""
import re
import nltk
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib
import logging

logger = logging.getLogger(__name__)

@dataclass
class SentimentResult:
    """Resultado da análise de sentimento"""
    sentiment: str  # 'aggressive', 'conciliatory', 'neutral'
    confidence: float
    key_phrases: List[str]
    tone_indicators: Dict[str, List[str]]
    recommendations: List[str]
    risk_score: float  # 0-100

class LegalSentimentAnalyzer:
    """Analisador de sentimento especializado em textos jurídicos"""
    
    def __init__(self):
        self.aggressive_patterns = [
            # Padrões agressivos
            r'\b(exijo|demando|requeiro imperativamente)\b',
            r'\b(inadmissível|inaceitável|vergonhoso)\b',
            r'\b(negligência|imperícia|imprudência)\b',
            r'\b(má-fé|dolo|fraude)\b',
            r'\b(imediatamente|urgentemente|prontamente)\b',
            r'\b(sob pena de|caso contrário|do contrário)\b',
            r'\b(responsabilização|penalização|sanção)\b',
            r'\b(grave|gravíssimo|inadiável)\b'
        ]
        
        self.conciliatory_patterns = [
            # Padrões conciliatórios
            r'\b(solicito|peço|requeiro respeitosamente)\b',
            r'\b(amigável|cordial|respeitoso)\b',
            r'\b(acordo|composição|entendimento)\b',
            r'\b(colaboração|cooperação|parceria)\b',
            r'\b(diálogo|conversa|negociação)\b',
            r'\b(consideração|atenção|análise)\b',
            r'\b(possível|viável|razoável)\b',
            r'\b(cordialmente|atenciosamente|respeitosamente)\b'
        ]
        
        self.neutral_patterns = [
            # Padrões neutros/formais
            r'\b(conforme|segundo|de acordo com)\b',
            r'\b(legislação|jurisprudência|doutrina)\b',
            r'\b(procedimento|processo|tramitação)\b',
            r'\b(protocolo|autuação|distribuição)\b',
            r'\b(vencimento|prazo|termo)\b',
            r'\b(comunicação|notificação|intimação)\b'
        ]
        
        # Palavras de intensidade
        self.intensifiers = {
            'high': ['muito', 'extremamente', 'gravemente', 'urgentemente'],
            'medium': ['bastante', 'consideravelmente', 'significativamente'],
            'low': ['um pouco', 'ligeiramente', 'levemente']
        }
        
        # Contextos jurídicos específicos
        self.legal_contexts = {
            'litigation': ['ação', 'processo', 'demanda', 'litígio'],
            'contract': ['contrato', 'acordo', 'cláusula', 'termo'],
            'negotiation': ['negociação', 'proposta', 'contraoferta'],
            'complaint': ['reclamação', 'denúncia', 'queixa']
        }
    
    def analyze_sentiment(self, text: str, context: Optional[str] = None) -> SentimentResult:
        """Analisar sentimento do texto jurídico"""
        
        # Pré-processamento
        text_clean = self._preprocess_text(text)
        
        # Contar padrões por categoria
        aggressive_matches = self._count_patterns(text_clean, self.aggressive_patterns)
        conciliatory_matches = self._count_patterns(text_clean, self.conciliatory_patterns)
        neutral_matches = self._count_patterns(text_clean, self.neutral_patterns)
        
        # Detectar intensificadores
        intensity_score = self._analyze_intensity(text_clean)
        
        # Detectar contexto legal
        detected_context = self._detect_legal_context(text_clean)
        
        # Calcular scores
        total_matches = aggressive_matches + conciliatory_matches + neutral_matches
        
        if total_matches == 0:
            sentiment = 'neutral'
            confidence = 0.5
        else:
            aggressive_ratio = aggressive_matches / total_matches
            conciliatory_ratio = conciliatory_matches / total_matches
            neutral_ratio = neutral_matches / total_matches
            
            # Determinar sentimento predominante
            if aggressive_ratio > 0.4:
                sentiment = 'aggressive'
                confidence = min(0.9, 0.6 + aggressive_ratio)
            elif conciliatory_ratio > 0.4:
                sentiment = 'conciliatory'
                confidence = min(0.9, 0.6 + conciliatory_ratio)
            else:
                sentiment = 'neutral'
                confidence = min(0.9, 0.6 + neutral_ratio)
        
        # Ajustar confiança baseado na intensidade
        confidence = min(0.95, confidence + (intensity_score * 0.1))
        
        # Extrair frases-chave
        key_phrases = self._extract_key_phrases(text_clean, sentiment)
        
        # Gerar indicadores de tom
        tone_indicators = self._generate_tone_indicators(
            text_clean, aggressive_matches, conciliatory_matches, neutral_matches
        )
        
        # Gerar recomendações
        recommendations = self._generate_recommendations(
            sentiment, confidence, detected_context, intensity_score
        )
        
        # Calcular score de risco
        risk_score = self._calculate_risk_score(
            sentiment, confidence, intensity_score, aggressive_matches
        )
        
        return SentimentResult(
            sentiment=sentiment,
            confidence=confidence,
            key_phrases=key_phrases,
            tone_indicators=tone_indicators,
            recommendations=recommendations,
            risk_score=risk_score
        )
    
    def _preprocess_text(self, text: str) -> str:
        """Pré-processar texto para análise"""
        # Remover caracteres especiais e normalizar
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _count_patterns(self, text: str, patterns: List[str]) -> int:
        """Contar ocorrências de padrões"""
        count = 0
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            count += len(matches)
        return count
    
    def _analyze_intensity(self, text: str) -> float:
        """Analisar intensidade do texto"""
        intensity_score = 0
        
        for level, words in self.intensifiers.items():
            for word in words:
                count = len(re.findall(rf'\b{word}\b', text, re.IGNORECASE))
                if level == 'high':
                    intensity_score += count * 0.8
                elif level == 'medium':
                    intensity_score += count * 0.5
                else:
                    intensity_score += count * 0.2
        
        return min(1.0, intensity_score / 10)  # Normalizar entre 0-1
    
    def _detect_legal_context(self, text: str) -> str:
        """Detectar contexto jurídico do texto"""
        context_scores = {}
        
        for context, keywords in self.legal_contexts.items():
            score = 0
            for keyword in keywords:
                count = len(re.findall(rf'\b{keyword}\b', text, re.IGNORECASE))
                score += count
            context_scores[context] = score
        
        if not context_scores or max(context_scores.values()) == 0:
            return 'general'
        
        return max(context_scores, key=context_scores.get)
    
    def _extract_key_phrases(self, text: str, sentiment: str) -> List[str]:
        """Extrair frases-chave baseadas no sentimento"""
        phrases = []
        
        # Dividir em sentenças
        sentences = re.split(r'[.!?]+', text)
        
        # Buscar padrões relevantes por sentimento
        if sentiment == 'aggressive':
            patterns = self.aggressive_patterns
        elif sentiment == 'conciliatory':
            patterns = self.conciliatory_patterns
        else:
            patterns = self.neutral_patterns
        
        for sentence in sentences[:5]:  # Primeiras 5 sentenças
            for pattern in patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    clean_sentence = sentence.strip()
                    if len(clean_sentence) > 10 and clean_sentence not in phrases:
                        phrases.append(clean_sentence[:100] + '...' if len(clean_sentence) > 100 else clean_sentence)
                    break
        
        return phrases[:3]  # Retornar até 3 frases-chave
    
    def _generate_tone_indicators(self, text: str, aggressive: int, 
                                 conciliatory: int, neutral: int) -> Dict[str, List[str]]:
        """Gerar indicadores específicos de tom"""
        indicators = {
            'aggressive_signals': [],
            'conciliatory_signals': [],
            'formal_language': [],
            'emotional_words': []
        }
        
        # Detectar sinais agressivos
        if aggressive > 0:
            aggressive_words = re.findall(
                r'\b(exijo|demando|inadmissível|negligência|má-fé)\b', 
                text, re.IGNORECASE
            )
            indicators['aggressive_signals'] = list(set(aggressive_words))
        
        # Detectar sinais conciliatórios
        if conciliatory > 0:
            conciliatory_words = re.findall(
                r'\b(solicito|amigável|acordo|colaboração|respeitosamente)\b', 
                text, re.IGNORECASE
            )
            indicators['conciliatory_signals'] = list(set(conciliatory_words))
        
        # Detectar linguagem formal
        formal_words = re.findall(
            r'\b(conforme|segundo|legislação|jurisprudência|procedimento)\b', 
            text, re.IGNORECASE
        )
        indicators['formal_language'] = list(set(formal_words))
        
        # Detectar palavras emocionais
        emotional_words = re.findall(
            r'\b(frustrante|preocupante|satisfatório|decepcionante|inaceitável)\b', 
            text, re.IGNORECASE
        )
        indicators['emotional_words'] = list(set(emotional_words))
        
        return indicators
    
    def _generate_recommendations(self, sentiment: str, confidence: float, 
                                 context: str, intensity: float) -> List[str]:
        """Gerar recomendações baseadas na análise"""
        recommendations = []
        
        if sentiment == 'aggressive' and confidence > 0.7:
            recommendations.extend([
                "Considere revisar o tom para uma abordagem mais diplomática",
                "Substitua expressões imperativas por solicitações respeitosas",
                "Adicione fundamentação legal para sustentar as demandas"
            ])
            
            if intensity > 0.5:
                recommendations.append("Reduza a intensidade da linguagem para evitar escalada de conflito")
        
        elif sentiment == 'conciliatory':
            recommendations.extend([
                "Tom apropriado para negociação e acordo",
                "Mantenha a cordialidade ao apresentar argumentos",
                "Considere incluir propostas concretas de solução"
            ])
        
        elif sentiment == 'neutral':
            if context == 'negotiation':
                recommendations.append("Considere adicionar elementos mais persuasivos ao texto")
            elif context == 'litigation':
                recommendations.append("Tom adequado para peças processuais formais")
        
        # Recomendações por contexto
        if context == 'contract':
            recommendations.append("Assegure clareza e precisão nas cláusulas")
        elif context == 'complaint':
            recommendations.append("Balance assertividade com profissionalismo")
        
        return recommendations[:3]  # Máximo 3 recomendações
    
    def _calculate_risk_score(self, sentiment: str, confidence: float, 
                             intensity: float, aggressive_matches: int) -> float:
        """Calcular score de risco do documento"""
        base_risk = {
            'aggressive': 70,
            'neutral': 30,
            'conciliatory': 10
        }.get(sentiment, 30)
        
        # Ajustar por confiança
        risk_score = base_risk * confidence
        
        # Ajustar por intensidade
        risk_score += (intensity * 20)
        
        # Ajustar por quantidade de padrões agressivos
        risk_score += (aggressive_matches * 5)
        
        return min(100, max(0, risk_score))
    
    def analyze_document_evolution(self, versions: List[Dict]) -> Dict:
        """Analisar evolução do sentimento ao longo das versões"""
        if len(versions) < 2:
            return {"error": "Necessário pelo menos 2 versões para análise"}
        
        evolution = []
        
        for i, version in enumerate(versions):
            result = self.analyze_sentiment(version['content'])
            evolution.append({
                'version': i + 1,
                'timestamp': version.get('timestamp'),
                'sentiment': result.sentiment,
                'confidence': result.confidence,
                'risk_score': result.risk_score
            })
        
        # Calcular tendência
        risk_scores = [v['risk_score'] for v in evolution]
        if len(risk_scores) >= 2:
            trend = risk_scores[-1] - risk_scores[0]
            trend_direction = 'increasing' if trend > 5 else 'decreasing' if trend < -5 else 'stable'
        else:
            trend_direction = 'stable'
        
        return {
            'evolution': evolution,
            'trend': trend_direction,
            'risk_change': risk_scores[-1] - risk_scores[0] if len(risk_scores) >= 2 else 0,
            'recommendation': self._get_evolution_recommendation(trend_direction)
        }
    
    def _get_evolution_recommendation(self, trend: str) -> str:
        """Obter recomendação baseada na evolução"""
        recommendations = {
            'increasing': "O tom está se tornando mais agressivo. Considere revisar a estratégia de comunicação.",
            'decreasing': "Boa evolução - o tom está se tornando mais diplomático.",
            'stable': "O tom permanece consistente ao longo das versões."
        }
        return recommendations.get(trend, "")

# Exemplo de uso
def create_sentiment_analyzer():
    """Factory para criar analisador de sentimento"""
    return LegalSentimentAnalyzer()

# Análise em lote
def analyze_multiple_documents(analyzer: LegalSentimentAnalyzer, 
                              documents: List[Dict]) -> List[Dict]:
    """Analisar múltiplos documentos"""
    results = []
    
    for doc in documents:
        try:
            result = analyzer.analyze_sentiment(
                doc['content'], 
                doc.get('context')
            )
            
            results.append({
                'document_id': doc.get('id'),
                'title': doc.get('title'),
                'analysis': result.__dict__,
                'analyzed_at': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error analyzing document {doc.get('id')}: {e}")
            results.append({
                'document_id': doc.get('id'),
                'error': str(e)
            })
    
    return results 