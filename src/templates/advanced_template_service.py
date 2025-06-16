from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import json
import re
from flask import current_app
from src.models.template import Template
from src.extensions import db

class TemplateCategory(Enum):
    """Categorias de templates"""
    CONTRATOS_CIVIL = "contratos_civil"
    CONTRATOS_TRABALHISTA = "contratos_trabalhista"
    CONTRATOS_EMPRESARIAL = "contratos_empresarial"
    PETICOES_INICIAL = "peticoes_inicial"
    PETICOES_RECURSO = "peticoes_recurso"
    PETICOES_DEFESA = "peticoes_defesa"
    PARECERES_JURIDICOS = "pareceres_juridicos"
    PROCURACOES = "procuracoes"
    ACORDOS_EXTRAJUDICIAIS = "acordos_extrajudiciais"
    NOTIFICACOES = "notificacoes"
    ATAS_REUNIAO = "atas_reuniao"
    ESCRITURAS = "escrituras"

class TemplateComplexity(Enum):
    """Níveis de complexidade"""
    BASICO = "basico"
    INTERMEDIARIO = "intermediario"
    AVANCADO = "avancado"
    ESPECIALISTA = "especialista"

class TemplateStatus(Enum):
    """Status do template"""
    ATIVO = "ativo"
    INATIVO = "inativo"
    EM_REVISAO = "em_revisao"
    DEPRECIADO = "depreciado"

@dataclass
class TemplateMetadata:
    """Metadados avançados do template"""
    category: TemplateCategory
    complexity: TemplateComplexity
    tags: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    legal_area: str = ""
    jurisdiction: str = "Brasil"
    court_level: Optional[str] = None
    estimated_time: int = 0  # minutos
    prerequisites: List[str] = field(default_factory=list)
    related_templates: List[int] = field(default_factory=list)
    version: str = "1.0"
    author: str = ""
    last_updated: datetime = field(default_factory=datetime.utcnow)
    usage_count: int = 0
    rating: float = 0.0
    reviews: List[Dict] = field(default_factory=list)

class AdvancedTemplateService:
    """Serviço avançado de gerenciamento de templates"""
    
    def __init__(self):
        self.template_library = self._initialize_template_library()
        self.variable_patterns = self._initialize_variable_patterns()
        self.validation_rules = self._initialize_validation_rules()
    
    def create_template(self, 
                       title: str,
                       content: str,
                       metadata: TemplateMetadata,
                       user_id: int,
                       is_public: bool = False) -> Dict[str, Any]:
        """Criar template com metadados avançados"""
        try:
            # Validar conteúdo
            validation_result = self.validate_template_content(content, metadata)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': 'Template inválido',
                    'details': validation_result['errors']
                }
            
            # Extrair variáveis automaticamente
            variables = self.extract_variables(content)
            
            # Criar template no banco
            template = Template(
                titulo=title,
                conteudo=content,
                categoria=metadata.category.value,
                publico=is_public,
                user_id=user_id,
                metadados=self._serialize_metadata(metadata)
            )
            
            db.session.add(template)
            db.session.commit()
            
            # Indexar para busca
            self.index_template(template)
            
            return {
                'success': True,
                'template_id': template.id,
                'variables': variables,
                'quality_score': self.calculate_template_quality(content, metadata)
            }
            
        except Exception as e:
            db.session.rollback()
            if current_app:
                current_app.logger.error(f"Erro ao criar template: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_templates(self, 
                        query: str = "",
                        category: Optional[TemplateCategory] = None,
                        complexity: Optional[TemplateComplexity] = None,
                        legal_area: Optional[str] = None,
                        tags: Optional[List[str]] = None,
                        user_id: Optional[int] = None,
                        limit: int = 20,
                        offset: int = 0) -> Dict[str, Any]:
        """Busca avançada de templates"""
        try:
            # Construir query base
            query_builder = db.session.query(Template)
            
            # Filtros
            if category:
                query_builder = query_builder.filter(Template.categoria == category.value)
            
            if user_id:
                query_builder = query_builder.filter(
                    db.or_(Template.user_id == user_id, Template.publico == True)
                )
            else:
                query_builder = query_builder.filter(Template.publico == True)
            
            # Busca textual
            if query:
                search_filter = db.or_(
                    Template.titulo.contains(query),
                    Template.conteudo.contains(query)
                )
                query_builder = query_builder.filter(search_filter)
            
            # Busca por metadados
            if complexity or legal_area or tags:
                metadata_filters = []
                
                if complexity:
                    metadata_filters.append(
                        Template.metadados.contains(f'"complexity": "{complexity.value}"')
                    )
                
                if legal_area:
                    metadata_filters.append(
                        Template.metadados.contains(f'"legal_area": "{legal_area}"')
                    )
                
                if tags:
                    for tag in tags:
                        metadata_filters.append(
                            Template.metadados.contains(f'"{tag}"')
                        )
                
                if metadata_filters:
                    query_builder = query_builder.filter(db.and_(*metadata_filters))
            
            # Ordenação por relevância
            query_builder = query_builder.order_by(Template.updated_at.desc())
            
            # Paginação
            total = query_builder.count()
            templates = query_builder.offset(offset).limit(limit).all()
            
            # Processar resultados
            results = []
            for template in templates:
                metadata = self._deserialize_metadata(template.metadados)
                results.append({
                    'id': template.id,
                    'titulo': template.titulo,
                    'categoria': template.categoria,
                    'metadata': metadata,
                    'created_at': template.created_at.isoformat(),
                    'updated_at': template.updated_at.isoformat(),
                    'preview': template.conteudo[:200] + '...' if len(template.conteudo) > 200 else template.conteudo
                })
            
            return {
                'success': True,
                'results': results,
                'total': total,
                'page': offset // limit + 1,
                'pages': (total + limit - 1) // limit
            }
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Erro na busca de templates: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_from_template(self, 
                              template_id: int,
                              variables: Dict[str, Any],
                              user_id: int) -> Dict[str, Any]:
        """Gerar documento a partir de template"""
        try:
            template = Template.query.get(template_id)
            if not template:
                return {
                    'success': False,
                    'error': 'Template não encontrado'
                }
            
            # Verificar permissões
            if not template.publico and template.user_id != user_id:
                return {
                    'success': False,
                    'error': 'Acesso negado ao template'
                }
            
            # Processar variáveis
            content = self.process_template_variables(template.conteudo, variables)
            
            # Aplicar formatação
            formatted_content = self.apply_formatting(content)
            
            # Validar resultado
            validation = self.validate_generated_content(formatted_content)
            
            # Registrar uso
            self.register_template_usage(template_id, user_id)
            
            return {
                'success': True,
                'content': formatted_content,
                'validation': validation,
                'template_info': {
                    'title': template.titulo,
                    'category': template.categoria,
                    'version': self._get_template_version(template)
                }
            }
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Erro ao gerar documento: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def suggest_templates(self, 
                         context: Dict[str, Any],
                         user_id: int,
                         limit: int = 5) -> Dict[str, Any]:
        """Sugerir templates baseado no contexto"""
        try:
            suggestions = []
            
            # Análise do contexto
            document_type = context.get('document_type')
            legal_area = context.get('legal_area')
            complexity = context.get('complexity', 'basico')
            keywords = context.get('keywords', [])
            
            # Buscar templates similares
            if document_type:
                category_templates = self.search_templates(
                    category=self._map_document_type_to_category(document_type),
                    complexity=TemplateComplexity(complexity),
                    legal_area=legal_area,
                    user_id=user_id,
                    limit=limit
                )
                
                if category_templates['success']:
                    suggestions.extend(category_templates['results'])
            
            # Buscar por palavras-chave
            if keywords:
                keyword_query = ' '.join(keywords)
                keyword_templates = self.search_templates(
                    query=keyword_query,
                    legal_area=legal_area,
                    user_id=user_id,
                    limit=limit
                )
                
                if keyword_templates['success']:
                    # Adicionar apenas se não estiver já na lista
                    existing_ids = [t['id'] for t in suggestions]
                    for template in keyword_templates['results']:
                        if template['id'] not in existing_ids:
                            suggestions.append(template)
            
            # Ranking por relevância
            suggestions = self.rank_suggestions(suggestions, context)
            
            return {
                'success': True,
                'suggestions': suggestions[:limit],
                'context_analyzed': context
            }
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Erro ao sugerir templates: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_template_content(self, content: str, metadata: TemplateMetadata) -> Dict[str, Any]:
        """Validar conteúdo do template"""
        errors = []
        warnings = []
        
        # Validações básicas
        if len(content.strip()) < 50:
            errors.append("Conteúdo muito curto para ser um template válido")
        
        # Validar variáveis
        variables = self.extract_variables(content)
        required_missing = set(metadata.required_fields) - set(variables)
        if required_missing:
            warnings.append(f"Campos obrigatórios não encontrados: {list(required_missing)}")
        
        # Validar estrutura jurídica
        if metadata.category in [TemplateCategory.PETICOES_INICIAL, TemplateCategory.PETICOES_RECURSO]:
            if not re.search(r'EXCELENTÍSSIMO|MERITÍSSIMO', content, re.IGNORECASE):
                warnings.append("Template de petição deve conter tratamento formal ao juiz")
        
        # Validar formatação
        if metadata.category in [TemplateCategory.CONTRATOS_CIVIL, TemplateCategory.CONTRATOS_EMPRESARIAL]:
            if not re.search(r'CLÁUSULA|ARTIGO', content, re.IGNORECASE):
                warnings.append("Contratos devem ter estrutura de cláusulas")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'score': self.calculate_validation_score(content, metadata)
        }
    
    def extract_variables(self, content: str) -> List[str]:
        """Extrair variáveis do template"""
        # Padrões de variáveis: {{variavel}}, [VARIAVEL], {variavel}
        patterns = [
            r'\{\{([^}]+)\}\}',  # {{variavel}}
            r'\[([A-Z_][A-Z0-9_]*)\]',  # [VARIAVEL]
            r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}',  # {variavel}
            r'__([A-Z_][A-Z0-9_]*)__'  # __VARIAVEL__
        ]
        
        variables = set()
        for pattern in patterns:
            matches = re.findall(pattern, content)
            variables.update(matches)
        
        return sorted(list(variables))
    
    def process_template_variables(self, content: str, variables: Dict[str, Any]) -> str:
        """Processar variáveis no template"""
        result = content
        
        # Processar diferentes padrões de variáveis
        for var_name, value in variables.items():
            # Formattar valor
            formatted_value = self.format_variable_value(value, var_name)
            
            # Substituir diferentes padrões
            patterns = [
                f'{{{{{var_name}}}}}',  # {{variavel}}
                f'[{var_name.upper()}]',  # [VARIAVEL]
                f'{{{var_name}}}',  # {variavel}
                f'__{var_name.upper()}__'  # __VARIAVEL__
            ]
            
            for pattern in patterns:
                result = result.replace(pattern, formatted_value)
        
        return result
    
    def format_variable_value(self, value: Any, var_name: str) -> str:
        """Formatar valor de variável baseado no tipo"""
        if value is None:
            return "[CAMPO_OBRIGATÓRIO]"
        
        # Formatação específica por tipo de campo
        if 'data' in var_name.lower() or 'date' in var_name.lower():
            if isinstance(value, str):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return dt.strftime('%d de %B de %Y')
                except:
                    return str(value)
            elif hasattr(value, 'strftime'):
                return value.strftime('%d de %B de %Y')
        
        if 'valor' in var_name.lower() or 'price' in var_name.lower():
            try:
                numeric_value = float(str(value).replace(',', '.'))
                return f"R$ {numeric_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            except:
                return str(value)
        
        if 'cpf' in var_name.lower():
            cpf = re.sub(r'\D', '', str(value))
            if len(cpf) == 11:
                return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        
        if 'cnpj' in var_name.lower():
            cnpj = re.sub(r'\D', '', str(value))
            if len(cnpj) == 14:
                return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        
        return str(value)
    
    def apply_formatting(self, content: str) -> str:
        """Aplicar formatação final ao documento"""
        # Normalizar espaçamentos
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r' {2,}', ' ', content)
        
        # Formatação de parágrafos
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Identificar títulos e cláusulas
                if re.match(r'^(CLÁUSULA|ARTIGO|PARÁGRAFO|TÍTULO)', line, re.IGNORECASE):
                    formatted_lines.append('\n' + line.upper())
                elif re.match(r'^\d+\.', line):
                    formatted_lines.append('\n' + line)
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append('')
        
        return '\n'.join(formatted_lines)
    
    def calculate_template_quality(self, content: str, metadata: TemplateMetadata) -> float:
        """Calcular score de qualidade do template"""
        score = 0.0
        
        # Comprimento adequado
        length = len(content)
        if 500 <= length <= 5000:
            score += 0.2
        elif length > 5000:
            score += 0.15
        else:
            score += 0.1
        
        # Estrutura
        if re.search(r'CLÁUSULA|ARTIGO|PARÁGRAFO', content, re.IGNORECASE):
            score += 0.2
        
        # Variáveis
        variables = self.extract_variables(content)
        if len(variables) >= 3:
            score += 0.2
        elif len(variables) >= 1:
            score += 0.1
        
        # Linguagem jurídica
        legal_terms = ['CONSIDERANDO', 'RESOLVE', 'DETERMINA', 'CONTRATANTE', 'CONTRATADO']
        found_terms = sum(1 for term in legal_terms if term in content.upper())
        score += min(found_terms * 0.05, 0.2)
        
        # Metadados completos
        if metadata.required_fields:
            score += 0.1
        if metadata.tags:
            score += 0.05
        if metadata.legal_area:
            score += 0.05
        
        return min(score, 1.0)
    
    def _initialize_template_library(self) -> Dict[str, Any]:
        """Inicializar biblioteca de templates"""
        return {
            'categories': [category.value for category in TemplateCategory],
            'complexities': [complexity.value for complexity in TemplateComplexity],
            'predefined_variables': {
                'pessoa_fisica': ['nome_completo', 'cpf', 'rg', 'endereco', 'telefone', 'email'],
                'pessoa_juridica': ['razao_social', 'nome_fantasia', 'cnpj', 'endereco', 'telefone', 'email'],
                'contrato': ['objeto', 'prazo', 'valor', 'forma_pagamento', 'foro'],
                'peticao': ['vara', 'comarca', 'processo_numero', 'tipo_acao']
            }
        }
    
    def _initialize_variable_patterns(self) -> Dict[str, str]:
        """Inicializar padrões de variáveis"""
        return {
            'double_brace': r'\{\{([^}]+)\}\}',
            'square_bracket': r'\[([A-Z_][A-Z0-9_]*)\]',
            'single_brace': r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}',
            'underscore': r'__([A-Z_][A-Z0-9_]*)__'
        }
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Inicializar regras de validação"""
        return {
            'min_length': 50,
            'max_length': 50000,
            'required_patterns': {
                'contratos': [r'CLÁUSULA|ARTIGO'],
                'peticoes': [r'EXCELENTÍSSIMO|MERITÍSSIMO'],
                'procuracoes': [r'PROCURAÇÃO|PODERES']
            }
        }
    
    def _serialize_metadata(self, metadata: TemplateMetadata) -> str:
        """Serializar metadados para JSON"""
        return json.dumps({
            'category': metadata.category.value,
            'complexity': metadata.complexity.value,
            'tags': metadata.tags,
            'required_fields': metadata.required_fields,
            'optional_fields': metadata.optional_fields,
            'legal_area': metadata.legal_area,
            'jurisdiction': metadata.jurisdiction,
            'court_level': metadata.court_level,
            'estimated_time': metadata.estimated_time,
            'prerequisites': metadata.prerequisites,
            'related_templates': metadata.related_templates,
            'version': metadata.version,
            'author': metadata.author,
            'last_updated': metadata.last_updated.isoformat(),
            'usage_count': metadata.usage_count,
            'rating': metadata.rating,
            'reviews': metadata.reviews
        }, ensure_ascii=False)
    
    def _deserialize_metadata(self, json_str: str) -> Dict[str, Any]:
        """Deserializar metadados do JSON"""
        if not json_str:
            return {
                'category': 'contratos_civil',
                'complexity': 'basico',
                'tags': [],
                'required_fields': [],
                'optional_fields': [],
                'legal_area': '',
                'jurisdiction': 'Brasil',
                'court_level': None,
                'estimated_time': 0,
                'prerequisites': [],
                'related_templates': [],
                'version': '1.0',
                'author': '',
                'last_updated': datetime.utcnow().isoformat(),
                'usage_count': 0,
                'rating': 0.0,
                'reviews': []
            }
        
        try:
            data = json.loads(json_str)
            return data
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Erro ao deserializar metadados: {e}")
            return {
                'category': 'contratos_civil',
                'complexity': 'basico',
                'tags': [],
                'required_fields': [],
                'optional_fields': [],
                'legal_area': '',
                'jurisdiction': 'Brasil',
                'court_level': None,
                'estimated_time': 0,
                'prerequisites': [],
                'related_templates': [],
                'version': '1.0',
                'author': '',
                'last_updated': datetime.utcnow().isoformat(),
                'usage_count': 0,
                'rating': 0.0,
                'reviews': []
            }
    
    def _map_document_type_to_category(self, document_type: str) -> TemplateCategory:
        """Mapear tipo de documento para categoria"""
        mapping = {
            'contrato': TemplateCategory.CONTRATOS_CIVIL,
            'peticao': TemplateCategory.PETICOES_INICIAL,
            'parecer': TemplateCategory.PARECERES_JURIDICOS,
            'procuracao': TemplateCategory.PROCURACOES,
            'acordo': TemplateCategory.ACORDOS_EXTRAJUDICIAIS,
            'notificacao': TemplateCategory.NOTIFICACOES
        }
        return mapping.get(document_type.lower(), TemplateCategory.CONTRATOS_CIVIL)
    
    def rank_suggestions(self, suggestions: List[Dict], context: Dict[str, Any]) -> List[Dict]:
        """Classificar sugestões por relevância"""
        for suggestion in suggestions:
            score = 0.0
            
            # Pontuação por categoria
            if suggestion.get('categoria') == context.get('document_type'):
                score += 0.3
            
            # Pontuação por área jurídica
            metadata = suggestion.get('metadata', {})
            if metadata.get('legal_area') == context.get('legal_area'):
                score += 0.2
            
            # Pontuação por complexidade
            if metadata.get('complexity') == context.get('complexity', 'basico'):
                score += 0.2
            
            # Pontuação por uso frequente
            usage_count = metadata.get('usage_count', 0)
            score += min(usage_count / 100, 0.2)
            
            # Pontuação por avaliação
            rating = metadata.get('rating', 0.0)
            score += rating / 5.0 * 0.1
            
            suggestion['relevance_score'] = score
        
        return sorted(suggestions, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    def calculate_validation_score(self, content: str, metadata: TemplateMetadata) -> float:
        """Calcular score de validação"""
        score = 1.0
        
        # Penalizar por problemas
        if len(content) < 50:
            score -= 0.3
        
        variables = self.extract_variables(content)
        required_missing = set(metadata.required_fields) - set(variables)
        score -= len(required_missing) * 0.1
        
        return max(score, 0.0)
    
    def validate_generated_content(self, content: str) -> Dict[str, Any]:
        """Validar conteúdo gerado"""
        issues = []
        
        # Verificar campos não preenchidos
        unfilled = re.findall(r'\[CAMPO_OBRIGATÓRIO\]', content)
        if unfilled:
            issues.append(f"{len(unfilled)} campos obrigatórios não preenchidos")
        
        # Verificar formatação
        if not re.search(r'\w', content):
            issues.append("Conteúdo vazio ou inválido")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'quality_score': 1.0 - (len(issues) * 0.2)
        }
    
    def register_template_usage(self, template_id: int, user_id: int):
        """Registrar uso do template"""
        try:
            template = Template.query.get(template_id)
            if template and template.metadados:
                metadata = json.loads(template.metadados)
                metadata['usage_count'] = metadata.get('usage_count', 0) + 1
                template.metadados = json.dumps(metadata, ensure_ascii=False)
                db.session.commit()
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Erro ao registrar uso: {e}")
    
    def index_template(self, template: Template):
        """Indexar template para busca (placeholder)"""
        # Implementar indexação para busca mais eficiente
        pass
    
    def _get_template_version(self, template: Template) -> str:
        """Obter versão do template"""
        if template.metadados:
            try:
                metadata = json.loads(template.metadados)
                return metadata.get('version', '1.0')
            except:
                pass
        return '1.0'

# Instância global
advanced_template_service = AdvancedTemplateService() 