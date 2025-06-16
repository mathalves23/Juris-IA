import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
from cerberus import Validator
from dataclasses import dataclass
from enum import Enum


class ValidationError(Exception):
    """Exceção para erros de validação."""
    
    def __init__(self, message: str, errors: Dict = None):
        self.message = message
        self.errors = errors or {}
        super().__init__(self.message)


@dataclass
class ValidationResult:
    """Resultado da validação."""
    is_valid: bool
    errors: Dict[str, List[str]]
    warnings: Dict[str, List[str]]
    sanitized_data: Dict[str, Any]


class DocumentValidationRules:
    """Regras de validação para documentos jurídicos."""
    
    # Schemas Cerberus para validação
    DOCUMENT_SCHEMA = {
        'titulo': {
            'type': 'string',
            'required': True,
            'minlength': 3,
            'maxlength': 200,
            'regex': r'^[a-zA-ZÀ-ÿ0-9\s\-\.\,\(\)]+$'
        },
        'conteudo': {
            'type': 'string',
            'required': True,
            'minlength': 10,
            'maxlength': 100000
        },
        'status': {
            'type': 'string',
            'required': False,
            'allowed': ['rascunho', 'revisao', 'finalizado', 'arquivado']
        },
        'template_id': {
            'type': 'integer',
            'required': False,
            'min': 1
        }
    }
    
    TEMPLATE_SCHEMA = {
        'titulo': {
            'type': 'string',
            'required': True,
            'minlength': 3,
            'maxlength': 200
        },
        'conteudo': {
            'type': 'string',
            'required': True,
            'minlength': 10,
            'maxlength': 50000
        },
        'categoria': {
            'type': 'string',
            'required': False,
            'maxlength': 100
        },
        'publico': {
            'type': 'boolean',
            'required': False
        }
    }
    
    USER_SCHEMA = {
        'nome': {
            'type': 'string',
            'required': True,
            'minlength': 2,
            'maxlength': 100,
            'regex': r'^[a-zA-ZÀ-ÿ\s]+$'
        },
        'email': {
            'type': 'string',
            'required': True,
            'regex': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        },
        'senha': {
            'type': 'string',
            'required': True,
            'minlength': 8,
            'maxlength': 128
        },
        'foto_url': {
            'type': 'string',
            'required': False,
            'regex': r'^https?://.*\.(jpg|jpeg|png|gif|webp)$'
        }
    }


class LegalContentValidator:
    """Validador específico para conteúdo jurídico."""
    
    def __init__(self):
        self.legal_patterns = {
            'artigo': r'\bart\.?\s*\d+[ºª]?',
            'lei': r'\blei\s+n[ºª]?\s*\d+',
            'codigo': r'\bcódigo\s+(civil|penal|processo\s+civil)',
            'clausula': r'\bcláusula\s+\d+[ºª]?',
            'paragrafo': r'\b§\s*\d+[ºª]?',
            'inciso': r'\binciso\s+[IVX]+',
            'alinea': r'\balínea\s+[a-z]\)',
        }
        
        self.required_sections = {
            'contrato': ['partes', 'objeto', 'valor', 'prazo'],
            'peticao': ['qualificacao', 'fatos', 'direito', 'pedidos'],
            'recurso': ['preliminares', 'merito', 'pedidos']
        }
    
    def validate_legal_structure(self, content: str, doc_type: str = None) -> ValidationResult:
        """Validar estrutura jurídica do documento."""
        errors = {}
        warnings = {}
        
        # Verificar comprimento mínimo
        if len(content) < 100:
            errors['content'] = ['Conteúdo muito curto para documento jurídico']
        
        # Verificar formatação básica
        if not re.search(r'[.!?]$', content.strip()):
            warnings['formatting'] = ['Documento deve terminar com pontuação adequada']
        
        # Verificar parágrafos muito longos
        paragraphs = content.split('\n\n')
        long_paragraphs = [i for i, p in enumerate(paragraphs) if len(p) > 1000]
        if long_paragraphs:
            warnings['formatting'] = warnings.get('formatting', [])
            warnings['formatting'].append(f'Parágrafos muito longos: {long_paragraphs}')
        
        # Verificar seções obrigatórias por tipo
        if doc_type and doc_type.lower() in self.required_sections:
            missing_sections = []
            required = self.required_sections[doc_type.lower()]
            
            for section in required:
                if section.lower() not in content.lower():
                    missing_sections.append(section)
            
            if missing_sections:
                errors['structure'] = [f'Seções obrigatórias ausentes: {", ".join(missing_sections)}']
        
        # Verificar referências jurídicas
        legal_refs = []
        for pattern_name, pattern in self.legal_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                legal_refs.extend(matches)
        
        if not legal_refs and len(content) > 500:
            warnings['legal_refs'] = ['Considere adicionar referências jurídicas (artigos, leis, etc.)']
        
        # Verificar formatação de valores monetários
        money_pattern = r'R\$\s*\d+(?:[.,]\d{2})?'
        money_matches = re.findall(money_pattern, content)
        if money_matches:
            warnings['formatting'] = warnings.get('formatting', [])
            warnings['formatting'].append('Valores monetários encontrados - considere escrever por extenso')
        
        # Verificar datas
        date_pattern = r'\d{1,2}/\d{1,2}/\d{2}(?!\d)'
        short_dates = re.findall(date_pattern, content)
        if short_dates:
            warnings['formatting'] = warnings.get('formatting', [])
            warnings['formatting'].append('Use formato de data completo (dd/mm/aaaa)')
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data={'content': content}
        )
    
    def validate_contract_clauses(self, content: str) -> ValidationResult:
        """Validar cláusulas de contrato."""
        errors = {}
        warnings = {}
        
        essential_clauses = [
            'objeto', 'valor', 'prazo', 'pagamento', 'rescisão'
        ]
        
        missing_clauses = []
        for clause in essential_clauses:
            if clause.lower() not in content.lower():
                missing_clauses.append(clause)
        
        if missing_clauses:
            warnings['clauses'] = [f'Cláusulas recomendadas ausentes: {", ".join(missing_clauses)}']
        
        # Verificar numeração de cláusulas
        clause_pattern = r'cláusula\s+(\d+)[ºª]?'
        clauses = re.findall(clause_pattern, content, re.IGNORECASE)
        
        if clauses:
            clause_numbers = [int(c) for c in clauses]
            expected = list(range(1, len(clause_numbers) + 1))
            
            if clause_numbers != expected:
                errors['numbering'] = ['Numeração de cláusulas incorreta']
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data={'content': content}
        )


class DataValidator:
    """Validador principal de dados."""
    
    def __init__(self):
        self.legal_validator = LegalContentValidator()
        self.cerberus_validator = Validator()
    
    def validate_document(self, data: Dict) -> ValidationResult:
        """Validar dados de documento."""
        errors = {}
        
        # Validações básicas
        if not data.get('titulo'):
            errors['titulo'] = ['Título é obrigatório']
        elif len(data['titulo']) < 3:
            errors['titulo'] = ['Título deve ter pelo menos 3 caracteres']
        
        if not data.get('conteudo'):
            errors['conteudo'] = ['Conteúdo é obrigatório']
        elif len(data['conteudo']) < 10:
            errors['conteudo'] = ['Conteúdo deve ter pelo menos 10 caracteres']
        
        if errors:
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings={},
                sanitized_data={}
            )
        
        # Sanitizar dados
        sanitized = self._sanitize_document_data(data)
        
        return ValidationResult(
            is_valid=True,
            errors={},
            warnings={},
            sanitized_data=sanitized
        )
    
    def validate_template(self, data: Dict) -> ValidationResult:
        """Validar dados de template."""
        if not self.cerberus_validator.validate(data, DocumentValidationRules.TEMPLATE_SCHEMA):
            return ValidationResult(
                is_valid=False,
                errors=self.cerberus_validator.errors,
                warnings={},
                sanitized_data={}
            )
        
        sanitized = self._sanitize_template_data(data)
        
        return ValidationResult(
            is_valid=True,
            errors={},
            warnings={},
            sanitized_data=sanitized
        )
    
    def validate_user(self, data: Dict) -> ValidationResult:
        """Validar dados de usuário."""
        errors = {}
        
        # Validar nome
        if not data.get('nome'):
            errors['nome'] = ['Nome é obrigatório']
        elif len(data['nome'].strip()) < 2:
            errors['nome'] = ['Nome deve ter pelo menos 2 caracteres']
        
        # Validar email
        if not data.get('email'):
            errors['email'] = ['Email é obrigatório']
        elif not self._validate_email(data['email']):
            errors['email'] = ['Email inválido']
        
        # Validar senha
        if 'senha' in data:
            password_result = self._validate_password_strength(data['senha'])
            if not password_result.is_valid:
                errors.update(password_result.errors)
        
        if errors:
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings={},
                sanitized_data={}
            )
        
        sanitized = self._sanitize_user_data(data)
        
        return ValidationResult(
            is_valid=True,
            errors={},
            warnings={},
            sanitized_data=sanitized
        )
    
    def validate_ai_request(self, data: Dict) -> ValidationResult:
        """Validar requisição de IA."""
        errors = {}
        
        # Verificar prompt
        if 'prompt' not in data or not data['prompt'].strip():
            errors['prompt'] = ['Prompt é obrigatório']
        elif len(data['prompt']) > 5000:
            errors['prompt'] = ['Prompt muito longo (máximo 5000 caracteres)']
        
        # Verificar tipo de documento
        if 'document_type' in data:
            allowed_types = ['contrato', 'peticao', 'recurso', 'parecer']
            if data['document_type'].lower() not in allowed_types:
                errors['document_type'] = [f'Tipo inválido. Permitidos: {", ".join(allowed_types)}']
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings={},
            sanitized_data=data
        )
    
    def _validate_email(self, email: str) -> bool:
        """Validar formato do email."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password_strength(self, password: str) -> ValidationResult:
        """Validar força da senha."""
        errors = {}
        
        if len(password) < 8:
            errors['senha'] = ['Senha deve ter pelo menos 8 caracteres']
        
        if not re.search(r'[a-z]', password):
            errors['senha'] = errors.get('senha', [])
            errors['senha'].append('Senha deve conter pelo menos uma letra minúscula')
        
        if not re.search(r'[A-Z]', password):
            errors['senha'] = errors.get('senha', [])
            errors['senha'].append('Senha deve conter pelo menos uma letra maiúscula')
        
        if not re.search(r'\d', password):
            errors['senha'] = errors.get('senha', [])
            errors['senha'].append('Senha deve conter pelo menos um número')
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings={},
            sanitized_data={'password': password}
        )
    
    def _sanitize_document_data(self, data: Dict) -> Dict:
        """Sanitizar dados de documento."""
        sanitized = {}
        
        if 'titulo' in data:
            sanitized['titulo'] = data['titulo'].strip()
        
        if 'conteudo' in data:
            # Remover caracteres de controle
            content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', data['conteudo'])
            # Normalizar quebras de linha
            content = re.sub(r'\r\n|\r', '\n', content)
            sanitized['conteudo'] = content.strip()
        
        if 'status' in data:
            sanitized['status'] = data['status'].lower()
        
        return sanitized
    
    def _sanitize_template_data(self, data: Dict) -> Dict:
        """Sanitizar dados de template."""
        sanitized = {}
        
        if 'titulo' in data:
            sanitized['titulo'] = data['titulo'].strip()
        
        if 'conteudo' in data:
            content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', data['conteudo'])
            content = re.sub(r'\r\n|\r', '\n', content)
            sanitized['conteudo'] = content.strip()
        
        if 'categoria' in data:
            sanitized['categoria'] = data['categoria'].strip().title()
        
        if 'publico' in data:
            sanitized['publico'] = bool(data['publico'])
        
        return sanitized
    
    def _sanitize_user_data(self, data: Dict) -> Dict:
        """Sanitizar dados de usuário."""
        sanitized = {}
        
        if 'nome' in data:
            # Capitalizar nome
            nome = ' '.join(word.capitalize() for word in data['nome'].strip().split())
            sanitized['nome'] = nome
        
        if 'email' in data:
            sanitized['email'] = data['email'].lower().strip()
        
        if 'senha' in data:
            sanitized['senha'] = data['senha']  # Não modificar senha
        
        if 'foto_url' in data:
            sanitized['foto_url'] = data['foto_url'].strip()
        
        return sanitized


# Instância global do validador
validator = DataValidator()


def validate_json_input(schema: Dict):
    """Decorator para validação automática de entrada JSON."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            
            if not request.is_json:
                return jsonify({'error': 'Content-Type deve ser application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Dados JSON inválidos'}), 400
            
            # Validar com schema fornecido
            cerberus_validator = Validator()
            if not cerberus_validator.validate(data, schema):
                return jsonify({
                    'error': 'Dados inválidos',
                    'details': cerberus_validator.errors
                }), 400
            
            # Adicionar dados validados aos kwargs
            kwargs['validated_data'] = cerberus_validator.document
            
            return func(*args, **kwargs)
        return wrapper
    return decorator 