"""
Sistema de OCR Inteligente para Documentos Jurídicos
Extrai dados estruturados e identifica elementos específicos
"""
import cv2
import pytesseract
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json
from datetime import datetime
import logging
import fitz  # PyMuPDF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

@dataclass
class ExtractedField:
    """Campo extraído pelo OCR"""
    field_type: str
    value: str
    confidence: float
    position: Tuple[int, int, int, int]  # x, y, width, height
    page: int

@dataclass
class DocumentStructure:
    """Estrutura do documento identificada"""
    document_type: str
    confidence: float
    fields: List[ExtractedField]
    metadata: Dict[str, Any]
    text_blocks: List[Dict]
    tables: List[Dict]

class IntelligentOCR:
    """Sistema de OCR inteligente para documentos jurídicos"""
    
    def __init__(self):
        # Padrões para diferentes tipos de documento
        self.document_patterns = {
            'contrato': {
                'keywords': ['contratante', 'contratado', 'cláusula', 'valor', 'prazo'],
                'required_fields': ['partes', 'objeto', 'valor', 'prazo'],
                'structure_indicators': ['cláusula', 'parágrafo', 'artigo']
            },
            'peticao': {
                'keywords': ['excelentíssimo', 'requerente', 'requerido', 'pedido'],
                'required_fields': ['juizo', 'partes', 'pedidos', 'fundamentacao'],
                'structure_indicators': ['dos fatos', 'do direito', 'dos pedidos']
            },
            'certidao': {
                'keywords': ['certidão', 'certifico', 'registro', 'cartório'],
                'required_fields': ['data', 'cartorio', 'livro', 'folha'],
                'structure_indicators': ['livro', 'folha', 'termo']
            },
            'procuracao': {
                'keywords': ['outorgante', 'outorgado', 'poderes', 'mandato'],
                'required_fields': ['outorgante', 'outorgado', 'poderes'],
                'structure_indicators': ['outorga', 'poderes', 'revogação']
            }
        }
        
        # Padrões regex para campos específicos
        self.field_patterns = {
            'cpf': r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
            'cnpj': r'\b\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}\b',
            'rg': r'\b\d{1,2}\.?\d{3}\.?\d{3}-?[0-9X]\b',
            'cep': r'\b\d{5}-?\d{3}\b',
            'telefone': r'\b\(?[1-9]{2}\)?\s?9?\d{4}-?\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'data': r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b',
            'valor_monetario': r'R\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?',
            'numero_processo': r'\b\d{7}-?\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b',
            'oab': r'\bOAB[\/\s]?[A-Z]{2}\s?\d+\b'
        }
        
        # Templates de documentos conhecidos
        self.document_templates = {
            'contrato_locacao': {
                'sections': [
                    'identificacao_partes',
                    'objeto_locacao',
                    'valor_aluguel',
                    'prazo_locacao',
                    'clausulas_gerais'
                ],
                'key_fields': ['locador', 'locatario', 'imovel', 'valor', 'prazo']
            },
            'petição_inicial': {
                'sections': [
                    'cabecalho',
                    'qualificacao_partes',
                    'dos_fatos',
                    'do_direito',
                    'dos_pedidos'
                ],
                'key_fields': ['autor', 'reu', 'causa_pedir', 'pedido']
            }
        }
    
    def process_document(self, file_path: str, document_type: Optional[str] = None) -> DocumentStructure:
        """Processar documento completo"""
        
        # Detectar tipo de arquivo
        if file_path.lower().endswith('.pdf'):
            return self._process_pdf(file_path, document_type)
        else:
            return self._process_image(file_path, document_type)
    
    def _process_pdf(self, pdf_path: str, document_type: Optional[str] = None) -> DocumentStructure:
        """Processar arquivo PDF"""
        doc = fitz.open(pdf_path)
        all_text_blocks = []
        all_fields = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Extrair texto com posições
            text_dict = page.get_text("dict")
            text_blocks = self._extract_text_blocks(text_dict, page_num)
            all_text_blocks.extend(text_blocks)
            
            # Extrair imagem da página para OCR se necessário
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            
            # Processar com OCR se texto não foi extraído adequadamente
            if not text_blocks or len(text_blocks) < 3:
                ocr_fields = self._ocr_image_data(img_data, page_num)
                all_fields.extend(ocr_fields)
        
        doc.close()
        
        # Combinar texto de todas as páginas
        full_text = " ".join([block['text'] for block in all_text_blocks])
        
        # Identificar tipo de documento se não fornecido
        if not document_type:
            document_type = self._identify_document_type(full_text)
        
        # Extrair campos específicos
        extracted_fields = self._extract_structured_fields(full_text, all_text_blocks)
        all_fields.extend(extracted_fields)
        
        # Identificar tabelas
        tables = self._identify_tables(all_text_blocks)
        
        return DocumentStructure(
            document_type=document_type,
            confidence=self._calculate_confidence(document_type, full_text),
            fields=all_fields,
            metadata={
                'pages': len(doc),
                'extraction_method': 'pdf_text',
                'timestamp': datetime.utcnow().isoformat()
            },
            text_blocks=all_text_blocks,
            tables=tables
        )
    
    def _process_image(self, image_path: str, document_type: Optional[str] = None) -> DocumentStructure:
        """Processar arquivo de imagem"""
        
        # Pré-processar imagem
        processed_image = self._preprocess_image(image_path)
        
        # OCR com diferentes configurações
        ocr_configs = [
            '--psm 6',  # Assumir bloco uniforme de texto
            '--psm 4',  # Assumir coluna única de texto
            '--psm 3',  # Segmentação automática de página
        ]
        
        best_result = None
        best_confidence = 0
        
        for config in ocr_configs:
            try:
                # Extrair texto com dados de posição
                data = pytesseract.image_to_data(
                    processed_image, 
                    config=config,
                    output_type=pytesseract.Output.DICT,
                    lang='por'
                )
                
                text_blocks = self._process_ocr_data(data)
                full_text = " ".join([block['text'] for block in text_blocks if block['text'].strip()])
                
                # Calcular confiança média
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                if avg_confidence > best_confidence:
                    best_confidence = avg_confidence
                    best_result = {
                        'text_blocks': text_blocks,
                        'full_text': full_text,
                        'confidence': avg_confidence
                    }
                    
            except Exception as e:
                logger.warning(f"OCR config {config} failed: {e}")
                continue
        
        if not best_result:
            raise Exception("OCR processing failed for all configurations")
        
        # Identificar tipo de documento
        if not document_type:
            document_type = self._identify_document_type(best_result['full_text'])
        
        # Extrair campos estruturados
        fields = self._extract_structured_fields(best_result['full_text'], best_result['text_blocks'])
        
        # Identificar tabelas
        tables = self._identify_tables(best_result['text_blocks'])
        
        return DocumentStructure(
            document_type=document_type,
            confidence=self._calculate_confidence(document_type, best_result['full_text']),
            fields=fields,
            metadata={
                'ocr_confidence': best_result['confidence'],
                'extraction_method': 'ocr',
                'timestamp': datetime.utcnow().isoformat()
            },
            text_blocks=best_result['text_blocks'],
            tables=tables
        )
    
    def _preprocess_image(self, image_path: str) -> Image.Image:
        """Pré-processar imagem para melhorar OCR"""
        
        # Carregar imagem
        image = Image.open(image_path)
        
        # Converter para escala de cinza
        if image.mode != 'L':
            image = image.convert('L')
        
        # Melhorar contraste
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Melhorar nitidez
        image = image.filter(ImageFilter.SHARPEN)
        
        # Redimensionar se muito pequena
        width, height = image.size
        if width < 1000 or height < 1000:
            factor = max(1000/width, 1000/height)
            new_size = (int(width * factor), int(height * factor))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Binarização (Threshold)
        image_array = np.array(image)
        
        # Aplicar threshold adaptativo
        image_cv = cv2.threshold(image_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Remover ruído
        kernel = np.ones((1,1), np.uint8)
        image_cv = cv2.morphologyEx(image_cv, cv2.MORPH_CLOSE, kernel)
        
        return Image.fromarray(image_cv)
    
    def _extract_text_blocks(self, text_dict: Dict, page_num: int) -> List[Dict]:
        """Extrair blocos de texto de PDF"""
        text_blocks = []
        
        for block in text_dict['blocks']:
            if 'lines' in block:
                for line in block['lines']:
                    line_text = ""
                    bbox = None
                    
                    for span in line['spans']:
                        line_text += span['text']
                        if bbox is None:
                            bbox = span['bbox']
                        else:
                            # Expandir bbox
                            bbox = [
                                min(bbox[0], span['bbox'][0]),
                                min(bbox[1], span['bbox'][1]),
                                max(bbox[2], span['bbox'][2]),
                                max(bbox[3], span['bbox'][3])
                            ]
                    
                    if line_text.strip():
                        text_blocks.append({
                            'text': line_text.strip(),
                            'bbox': bbox,
                            'page': page_num,
                            'font_size': line['spans'][0].get('size', 12) if line['spans'] else 12
                        })
        
        return text_blocks
    
    def _process_ocr_data(self, ocr_data: Dict) -> List[Dict]:
        """Processar dados do OCR"""
        text_blocks = []
        
        for i in range(len(ocr_data['text'])):
            if int(ocr_data['conf'][i]) > 30:  # Confiança mínima
                text = ocr_data['text'][i].strip()
                if text:
                    text_blocks.append({
                        'text': text,
                        'bbox': [
                            ocr_data['left'][i],
                            ocr_data['top'][i],
                            ocr_data['left'][i] + ocr_data['width'][i],
                            ocr_data['top'][i] + ocr_data['height'][i]
                        ],
                        'confidence': int(ocr_data['conf'][i]),
                        'page': 0
                    })
        
        return text_blocks
    
    def _identify_document_type(self, text: str) -> str:
        """Identificar tipo de documento"""
        text_lower = text.lower()
        
        scores = {}
        for doc_type, patterns in self.document_patterns.items():
            score = 0
            for keyword in patterns['keywords']:
                count = text_lower.count(keyword.lower())
                score += count
            scores[doc_type] = score
        
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return 'desconhecido'
    
    def _extract_structured_fields(self, text: str, text_blocks: List[Dict]) -> List[ExtractedField]:
        """Extrair campos estruturados do texto"""
        fields = []
        
        for field_type, pattern in self.field_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Tentar encontrar posição no texto
                position = self._find_text_position(match.group(), text_blocks)
                
                field = ExtractedField(
                    field_type=field_type,
                    value=match.group(),
                    confidence=0.8,  # Confiança baseada em regex
                    position=position or (0, 0, 0, 0),
                    page=0
                )
                fields.append(field)
        
        return fields
    
    def _find_text_position(self, search_text: str, text_blocks: List[Dict]) -> Optional[Tuple[int, int, int, int]]:
        """Encontrar posição de texto específico nos blocos"""
        for block in text_blocks:
            if search_text in block['text']:
                return tuple(block['bbox'])
        return None
    
    def _identify_tables(self, text_blocks: List[Dict]) -> List[Dict]:
        """Identificar tabelas no documento"""
        tables = []
        
        # Agrupar blocos por linha (y similar)
        lines = {}
        for block in text_blocks:
            y = int(block['bbox'][1] / 20) * 20  # Agrupar por proximidade vertical
            if y not in lines:
                lines[y] = []
            lines[y].append(block)
        
        # Identificar linhas com múltiplas colunas (possíveis tabelas)
        table_lines = []
        for y, blocks in lines.items():
            if len(blocks) >= 3:  # Pelo menos 3 colunas
                # Ordenar por posição x
                blocks.sort(key=lambda b: b['bbox'][0])
                table_lines.append({
                    'y': y,
                    'blocks': blocks,
                    'columns': len(blocks)
                })
        
        # Agrupar linhas consecutivas em tabelas
        if table_lines:
            table_lines.sort(key=lambda l: l['y'])
            current_table = [table_lines[0]]
            
            for i in range(1, len(table_lines)):
                # Se linhas estão próximas e têm número similar de colunas
                if (table_lines[i]['y'] - table_lines[i-1]['y'] < 50 and
                    abs(table_lines[i]['columns'] - table_lines[i-1]['columns']) <= 1):
                    current_table.append(table_lines[i])
                else:
                    # Finalizar tabela atual
                    if len(current_table) >= 2:  # Pelo menos 2 linhas
                        tables.append(self._format_table(current_table))
                    current_table = [table_lines[i]]
            
            # Adicionar última tabela
            if len(current_table) >= 2:
                tables.append(self._format_table(current_table))
        
        return tables
    
    def _format_table(self, table_lines: List[Dict]) -> Dict:
        """Formatar dados da tabela"""
        rows = []
        
        for line in table_lines:
            row = [block['text'] for block in line['blocks']]
            rows.append(row)
        
        return {
            'type': 'table',
            'rows': rows,
            'columns': len(rows[0]) if rows else 0,
            'confidence': 0.7
        }
    
    def _calculate_confidence(self, document_type: str, text: str) -> float:
        """Calcular confiança da identificação do documento"""
        if document_type == 'desconhecido':
            return 0.3
        
        if document_type in self.document_patterns:
            patterns = self.document_patterns[document_type]
            required_found = 0
            
            for field in patterns['required_fields']:
                # Verificar se campo foi encontrado no texto
                if any(keyword in text.lower() for keyword in [field.lower()]):
                    required_found += 1
            
            confidence = required_found / len(patterns['required_fields'])
            return min(0.95, max(0.5, confidence))
        
        return 0.6
    
    def _ocr_image_data(self, image_data: bytes, page_num: int) -> List[ExtractedField]:
        """Processar dados de imagem com OCR"""
        # Implementação simplificada - em produção usar processamento completo
        return []

# Funções utilitárias
def extract_document_data(file_path: str, document_type: Optional[str] = None) -> Dict:
    """Função principal para extração de dados"""
    ocr = IntelligentOCR()
    
    try:
        result = ocr.process_document(file_path, document_type)
        
        return {
            'success': True,
            'document_type': result.document_type,
            'confidence': result.confidence,
            'fields': [field.__dict__ for field in result.fields],
            'metadata': result.metadata,
            'tables': result.tables,
            'extracted_at': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error extracting document data: {e}")
        return {
            'success': False,
            'error': str(e),
            'extracted_at': datetime.utcnow().isoformat()
        }

def batch_process_documents(file_paths: List[str]) -> List[Dict]:
    """Processar múltiplos documentos em lote"""
    ocr = IntelligentOCR()
    results = []
    
    for file_path in file_paths:
        try:
            result = extract_document_data(file_path)
            result['file_path'] = file_path
            results.append(result)
        except Exception as e:
            results.append({
                'file_path': file_path,
                'success': False,
                'error': str(e)
            })
    
    return results 