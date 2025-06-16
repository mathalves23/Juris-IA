"""
Sistema de Tradução Jurídica Especializada
Tradução português ↔ inglês com contexto jurídico
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from googletrans import Translator
import json

logger = logging.getLogger(__name__)

@dataclass
class TranslationResult:
    """Resultado da tradução jurídica"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    legal_terms: List[Dict]
    formatting_preserved: bool
    metadata: Dict

class LegalTranslator:
    """Tradutor especializado em documentos jurídicos"""
    
    def __init__(self):
        self.translator = Translator()
        
        # Dicionário de termos jurídicos PT-EN
        self.legal_terms_pt_en = {
            # Termos contratuais
            'contratante': 'contracting party',
            'contratado': 'contractor',
            'locador': 'lessor',
            'locatário': 'lessee',
            'fiador': 'guarantor',
            'avalista': 'surety',
            'cláusula': 'clause',
            'parágrafo': 'paragraph',
            'artigo': 'article',
            'rescisão': 'termination',
            'distrato': 'mutual agreement to terminate',
            'multa': 'penalty',
            
            # Termos processuais
            'petição inicial': 'initial petition',
            'contestação': 'answer',
            'tréplica': 'surrejoinder',
            'sentença': 'judgment',
            'acórdão': 'appellate court decision',
            'recurso': 'appeal',
            'embargos': 'motion for clarification',
            'mandado de segurança': 'writ of mandamus',
            'habeas corpus': 'habeas corpus',
            'ação civil pública': 'class action lawsuit',
            
            # Termos de direito civil
            'usucapião': 'adverse possession',
            'posse': 'possession',
            'propriedade': 'ownership',
            'servidão': 'easement',
            'hipoteca': 'mortgage',
            'penhor': 'pledge',
            'anticrese': 'antichresis',
            'dano moral': 'moral damages',
            'dano material': 'material damages',
            'lucros cessantes': 'lost profits',
            
            # Termos de direito empresarial
            'sociedade limitada': 'limited liability company',
            'sociedade anônima': 'corporation',
            'quotas': 'quotas',
            'ações': 'shares',
            'administrador': 'manager',
            'sócio': 'partner',
            'deliberação': 'resolution',
            'assembleia': 'meeting',
            
            # Termos trabalhistas
            'carteira de trabalho': 'work permit',
            'fundo de garantia': 'severance fund',
            'décimo terceiro': 'thirteenth salary',
            'férias': 'vacation',
            'aviso prévio': 'notice period',
            'justa causa': 'just cause',
            'rescisão indireta': 'constructive dismissal'
        }
        
        # Dicionário reverso EN-PT
        self.legal_terms_en_pt = {v: k for k, v in self.legal_terms_pt_en.items()}
        
        # Padrões de formatação jurídica
        self.formatting_patterns = {
            'clause_number': r'(Cláusula|Artigo|Art\.)\s+(\d+)[ºª°]?',
            'paragraph': r'(Parágrafo|§)\s+(\d+)[ºª°]?',
            'item': r'(Item|Inciso)\s+([IVX]+|\d+)',
            'date': r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}',
            'currency': r'R\$\s*[\d.,]+',
            'percentage': r'\d+[,.]?\d*\s*%',
            'law_reference': r'Lei\s+n[ºª°]?\s*[\d./]+',
            'article_reference': r'art\.\s*\d+'
        }
        
        # Templates de documentos
        self.document_templates = {
            'contract': {
                'header': 'CONTRACT',
                'parties_section': 'PARTIES',
                'terms_section': 'TERMS AND CONDITIONS',
                'signature_section': 'SIGNATURES'
            },
            'petition': {
                'header': 'PETITION',
                'court_section': 'TO THE HONORABLE COURT',
                'facts_section': 'STATEMENT OF FACTS',
                'law_section': 'LEGAL GROUNDS',
                'request_section': 'PRAYER FOR RELIEF'
            }
        }
    
    def translate_document(self, text: str, target_language: str = 'en', 
                          document_type: Optional[str] = None) -> TranslationResult:
        """Traduzir documento jurídico completo"""
        
        # Detectar idioma de origem
        source_language = self._detect_language(text)
        
        # Preservar formatação
        formatted_segments = self._extract_formatting(text)
        
        # Traduzir por segmentos
        translated_segments = []
        legal_terms_found = []
        
        for segment in formatted_segments:
            if segment['type'] == 'text':
                # Traduzir texto normal
                translated_text = self._translate_with_legal_context(
                    segment['content'], source_language, target_language
                )
                translated_segments.append({
                    'type': 'text',
                    'content': translated_text,
                    'original': segment['content']
                })
                
                # Identificar termos jurídicos
                terms = self._identify_legal_terms(segment['content'], source_language)
                legal_terms_found.extend(terms)
                
            else:
                # Preservar formatação especial
                translated_segments.append(segment)
        
        # Reconstituir documento
        final_translation = self._reconstruct_document(translated_segments, document_type)
        
        # Calcular confiança
        confidence = self._calculate_translation_confidence(text, final_translation)
        
        return TranslationResult(
            original_text=text,
            translated_text=final_translation,
            source_language=source_language,
            target_language=target_language,
            confidence=confidence,
            legal_terms=legal_terms_found,
            formatting_preserved=True,
            metadata={
                'document_type': document_type,
                'segments_count': len(formatted_segments),
                'translated_at': datetime.utcnow().isoformat()
            }
        )
    
    def _detect_language(self, text: str) -> str:
        """Detectar idioma do texto"""
        try:
            detected = self.translator.detect(text[:500])  # Primeiros 500 caracteres
            return detected.lang
        except:
            # Fallback baseado em palavras-chave
            portuguese_indicators = ['contrato', 'cláusula', 'direito', 'lei', 'artigo']
            english_indicators = ['contract', 'clause', 'right', 'law', 'article']
            
            text_lower = text.lower()
            pt_count = sum(1 for word in portuguese_indicators if word in text_lower)
            en_count = sum(1 for word in english_indicators if word in text_lower)
            
            return 'pt' if pt_count > en_count else 'en'
    
    def _extract_formatting(self, text: str) -> List[Dict]:
        """Extrair e preservar formatação do documento"""
        segments = []
        current_pos = 0
        
        # Encontrar todos os padrões de formatação
        all_matches = []
        for pattern_name, pattern in self.formatting_patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                all_matches.append({
                    'start': match.start(),
                    'end': match.end(),
                    'type': pattern_name,
                    'content': match.group(),
                    'groups': match.groups()
                })
        
        # Ordenar por posição
        all_matches.sort(key=lambda x: x['start'])
        
        # Dividir texto em segmentos
        for match in all_matches:
            # Adicionar texto antes do match
            if current_pos < match['start']:
                segments.append({
                    'type': 'text',
                    'content': text[current_pos:match['start']].strip()
                })
            
            # Adicionar o match preservado
            segments.append({
                'type': 'formatting',
                'subtype': match['type'],
                'content': match['content'],
                'groups': match['groups']
            })
            
            current_pos = match['end']
        
        # Adicionar texto restante
        if current_pos < len(text):
            segments.append({
                'type': 'text',
                'content': text[current_pos:].strip()
            })
        
        # Filtrar segmentos vazios
        return [seg for seg in segments if seg['content'].strip()]
    
    def _translate_with_legal_context(self, text: str, source_lang: str, target_lang: str) -> str:
        """Traduzir texto com contexto jurídico"""
        
        # Substituir termos jurídicos conhecidos
        if source_lang == 'pt' and target_lang == 'en':
            terms_dict = self.legal_terms_pt_en
        elif source_lang == 'en' and target_lang == 'pt':
            terms_dict = self.legal_terms_en_pt
        else:
            terms_dict = {}
        
        # Pré-processar termos jurídicos
        preprocessed_text = text
        term_placeholders = {}
        
        for i, (term, translation) in enumerate(terms_dict.items()):
            if term.lower() in text.lower():
                placeholder = f"__LEGAL_TERM_{i}__"
                preprocessed_text = re.sub(
                    re.escape(term), placeholder, 
                    preprocessed_text, flags=re.IGNORECASE
                )
                term_placeholders[placeholder] = translation
        
        # Traduzir texto pré-processado
        try:
            translated = self.translator.translate(
                preprocessed_text, 
                src=source_lang, 
                dest=target_lang
            ).text
        except Exception as e:
            logger.error(f"Translation error: {e}")
            translated = preprocessed_text
        
        # Restaurar termos jurídicos traduzidos
        for placeholder, translation in term_placeholders.items():
            translated = translated.replace(placeholder, translation)
        
        return translated
    
    def _identify_legal_terms(self, text: str, language: str) -> List[Dict]:
        """Identificar termos jurídicos no texto"""
        legal_terms = []
        
        if language == 'pt':
            terms_dict = self.legal_terms_pt_en
        elif language == 'en':
            terms_dict = self.legal_terms_en_pt
        else:
            return legal_terms
        
        text_lower = text.lower()
        
        for term, translation in terms_dict.items():
            if term.lower() in text_lower:
                # Encontrar posições do termo
                for match in re.finditer(re.escape(term), text, re.IGNORECASE):
                    legal_terms.append({
                        'term': match.group(),
                        'translation': translation,
                        'position': (match.start(), match.end()),
                        'category': self._categorize_legal_term(term)
                    })
        
        return legal_terms
    
    def _categorize_legal_term(self, term: str) -> str:
        """Categorizar termo jurídico"""
        categories = {
            'contractual': ['contratante', 'contratado', 'cláusula', 'rescisão'],
            'procedural': ['petição', 'contestação', 'sentença', 'recurso'],
            'civil': ['posse', 'propriedade', 'usucapião', 'dano'],
            'corporate': ['sociedade', 'ações', 'quotas', 'administrador'],
            'labor': ['carteira', 'férias', 'aviso prévio', 'justa causa']
        }
        
        term_lower = term.lower()
        for category, keywords in categories.items():
            if any(keyword in term_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def _reconstruct_document(self, segments: List[Dict], document_type: Optional[str]) -> str:
        """Reconstituir documento traduzido"""
        result = []
        
        for segment in segments:
            if segment['type'] == 'text':
                result.append(segment['content'])
            elif segment['type'] == 'formatting':
                # Traduzir elementos de formatação se necessário
                translated_formatting = self._translate_formatting(segment)
                result.append(translated_formatting)
        
        return ' '.join(result)
    
    def _translate_formatting(self, segment: Dict) -> str:
        """Traduzir elementos de formatação"""
        subtype = segment['subtype']
        content = segment['content']
        
        # Mapear elementos de formatação PT-EN
        formatting_translations = {
            'Cláusula': 'Clause',
            'Artigo': 'Article',
            'Art.': 'Art.',
            'Parágrafo': 'Paragraph',
            'Item': 'Item',
            'Inciso': 'Section'
        }
        
        translated = content
        for pt_term, en_term in formatting_translations.items():
            translated = re.sub(pt_term, en_term, translated, flags=re.IGNORECASE)
        
        return translated
    
    def _calculate_translation_confidence(self, original: str, translated: str) -> float:
        """Calcular confiança da tradução"""
        
        # Fatores para cálculo de confiança
        factors = {
            'length_similarity': 0.3,  # Similaridade de comprimento
            'structure_preservation': 0.3,  # Preservação da estrutura
            'legal_terms_accuracy': 0.4  # Precisão dos termos jurídicos
        }
        
        # Similaridade de comprimento
        length_ratio = min(len(translated), len(original)) / max(len(translated), len(original))
        length_score = length_ratio
        
        # Preservação da estrutura (baseado em número de parágrafos/seções)
        original_paragraphs = len(original.split('\n\n'))
        translated_paragraphs = len(translated.split('\n\n'))
        structure_score = min(translated_paragraphs, original_paragraphs) / max(translated_paragraphs, original_paragraphs)
        
        # Precisão dos termos jurídicos (assumindo que foram traduzidos corretamente)
        legal_terms_score = 0.8  # Score fixo para termos jurídicos conhecidos
        
        # Calcular confiança final
        confidence = (
            factors['length_similarity'] * length_score +
            factors['structure_preservation'] * structure_score +
            factors['legal_terms_accuracy'] * legal_terms_score
        )
        
        return min(0.95, max(0.3, confidence))
    
    def translate_specific_terms(self, terms: List[str], source_lang: str, target_lang: str) -> Dict[str, str]:
        """Traduzir termos específicos"""
        translations = {}
        
        if source_lang == 'pt' and target_lang == 'en':
            terms_dict = self.legal_terms_pt_en
        elif source_lang == 'en' and target_lang == 'pt':
            terms_dict = self.legal_terms_en_pt
        else:
            terms_dict = {}
        
        for term in terms:
            # Primeiro tentar dicionário jurídico
            if term.lower() in terms_dict:
                translations[term] = terms_dict[term.lower()]
            else:
                # Usar tradutor geral
                try:
                    translated = self.translator.translate(term, src=source_lang, dest=target_lang).text
                    translations[term] = translated
                except:
                    translations[term] = term  # Manter original se falhar
        
        return translations
    
    def get_bilingual_glossary(self, document_text: str) -> Dict:
        """Gerar glossário bilíngue para documento"""
        
        # Detectar idioma
        source_lang = self._detect_language(document_text)
        target_lang = 'en' if source_lang == 'pt' else 'pt'
        
        # Identificar termos jurídicos
        legal_terms = self._identify_legal_terms(document_text, source_lang)
        
        # Criar glossário
        glossary = {
            'source_language': source_lang,
            'target_language': target_lang,
            'terms': {}
        }
        
        for term_info in legal_terms:
            term = term_info['term']
            translation = term_info['translation']
            category = term_info['category']
            
            if term not in glossary['terms']:
                glossary['terms'][term] = {
                    'translation': translation,
                    'category': category,
                    'occurrences': 1
                }
            else:
                glossary['terms'][term]['occurrences'] += 1
        
        return glossary

# Funções utilitárias
def translate_legal_document(text: str, target_language: str = 'en', 
                           document_type: Optional[str] = None) -> Dict:
    """Função principal para tradução de documentos jurídicos"""
    translator = LegalTranslator()
    
    try:
        result = translator.translate_document(text, target_language, document_type)
        
        return {
            'success': True,
            'original_text': result.original_text,
            'translated_text': result.translated_text,
            'source_language': result.source_language,
            'target_language': result.target_language,
            'confidence': result.confidence,
            'legal_terms': result.legal_terms,
            'metadata': result.metadata
        }
    
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return {
            'success': False,
            'error': str(e),
            'original_text': text
        }

def create_bilingual_contract(portuguese_text: str) -> Dict:
    """Criar contrato bilíngue (PT-EN)"""
    translator = LegalTranslator()
    
    # Traduzir para inglês
    translation_result = translator.translate_document(portuguese_text, 'en', 'contract')
    
    # Criar glossário
    glossary = translator.get_bilingual_glossary(portuguese_text)
    
    return {
        'portuguese_version': portuguese_text,
        'english_version': translation_result.translated_text,
        'bilingual_glossary': glossary,
        'confidence': translation_result.confidence,
        'created_at': datetime.utcnow().isoformat()
    } 