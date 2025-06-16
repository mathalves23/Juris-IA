import re
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, date
from flask import current_app

class ValidationSeverity(Enum):
    """Níveis de severidade de validação"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ValidationCategory(Enum):
    """Categorias de validação"""
    REQUIRED = "required"
    FORMAT = "format"
    BUSINESS = "business"
    SECURITY = "security"
    LEGAL = "legal"

@dataclass
class ValidationRule:
    """Regra de validação"""
    name: str
    field: str
    validator: Callable
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    category: ValidationCategory = ValidationCategory.FORMAT
    conditions: Optional[Dict[str, Any]] = None

@dataclass
class ValidationResult:
    """Resultado de validação"""
    field: str
    rule_name: str
    message: str
    severity: ValidationSeverity
    category: ValidationCategory
    value: Any = None
    suggestions: List[str] = None

class AdvancedValidator:
    """Sistema de validação avançado"""
    
    def __init__(self):
        self.rules = {}
        self.custom_validators = {}
        self._setup_default_validators()
        self._setup_default_rules()
    
    def add_rule(self, entity_type: str, rule: ValidationRule):
        """Adicionar regra de validação"""
        if entity_type not in self.rules:
            self.rules[entity_type] = []
        self.rules[entity_type].append(rule)
    
    def validate(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validar dados de acordo com as regras"""
        results = []
        rules = self.rules.get(entity_type, [])
        
        for rule in rules:
            # Verificar condições
            if rule.conditions and not self._check_conditions(rule.conditions, data):
                continue
            
            # Obter valor do campo
            value = self._get_field_value(data, rule.field)
            
            try:
                # Executar validação
                is_valid = rule.validator(value, data)
                
                if not is_valid:
                    result = ValidationResult(
                        field=rule.field,
                        rule_name=rule.name,
                        message=rule.message,
                        severity=rule.severity,
                        category=rule.category,
                        value=value,
                        suggestions=self._get_suggestions(rule, value)
                    )
                    results.append(result)
                    
            except Exception as e:
                # Erro na validação
                result = ValidationResult(
                    field=rule.field,
                    rule_name=rule.name,
                    message=f"Erro na validação: {str(e)}",
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.FORMAT,
                    value=value
                )
                results.append(result)
        
        # Organizar resultados
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        warnings = [r for r in results if r.severity == ValidationSeverity.WARNING]
        infos = [r for r in results if r.severity == ValidationSeverity.INFO]
        
        return {
            'valid': len(errors) == 0,
            'score': self._calculate_validation_score(results, len(rules)),
            'errors': [self._format_result(r) for r in errors],
            'warnings': [self._format_result(r) for r in warnings],
            'info': [self._format_result(r) for r in infos],
            'summary': {
                'total_rules': len(rules),
                'errors_count': len(errors),
                'warnings_count': len(warnings),
                'passed_count': len(rules) - len(results)
            }
        }
    
    def validate_user_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validar dados de usuário"""
        return self.validate('user', data)
    
    def validate_document_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validar dados de documento"""
        return self.validate('document', data)
    
    def validate_template_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validar dados de template"""
        return self.validate('template', data)
    
    def _setup_default_validators(self):
        """Configurar validadores padrão"""
        
        # Validadores básicos
        self.custom_validators = {
            'required': lambda value, data: value is not None and str(value).strip() != '',
            'email': lambda value, data: self._validate_email(value),
            'cpf': lambda value, data: self._validate_cpf(value),
            'cnpj': lambda value, data: self._validate_cnpj(value),
            'phone': lambda value, data: self._validate_phone(value),
            'password_strength': lambda value, data: self._validate_password_strength(value),
            'min_length': lambda value, data: len(str(value)) >= data.get('min_length', 0),
            'max_length': lambda value, data: len(str(value)) <= data.get('max_length', 1000),
            'numeric': lambda value, data: str(value).replace('.', '').replace(',', '').isdigit(),
            'date_format': lambda value, data: self._validate_date_format(value),
            'url': lambda value, data: self._validate_url(value),
            'legal_document': lambda value, data: self._validate_legal_document(value),
            'no_script': lambda value, data: self._validate_no_script(value),
            'sanitized': lambda value, data: self._validate_sanitized(value)
        }
    
    def _setup_default_rules(self):
        """Configurar regras padrão"""
        
        # Regras para usuário
        user_rules = [
            ValidationRule(
                name='nome_required',
                field='nome',
                validator=self.custom_validators['required'],
                message='Nome é obrigatório',
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.REQUIRED
            ),
            ValidationRule(
                name='nome_length',
                field='nome',
                validator=lambda v, d: 2 <= len(str(v)) <= 100,
                message='Nome deve ter entre 2 e 100 caracteres',
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT
            ),
            ValidationRule(
                name='email_required',
                field='email',
                validator=self.custom_validators['required'],
                message='Email é obrigatório',
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.REQUIRED
            ),
            ValidationRule(
                name='email_format',
                field='email',
                validator=self.custom_validators['email'],
                message='Email deve ter formato válido',
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT
            ),
            ValidationRule(
                name='senha_required',
                field='senha',
                validator=self.custom_validators['required'],
                message='Senha é obrigatória',
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.REQUIRED
            ),
            ValidationRule(
                name='senha_strength',
                field='senha',
                validator=self.custom_validators['password_strength'],
                message='Senha deve ter pelo menos 8 caracteres, incluindo maiúscula, minúscula e número',
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.SECURITY
            )
        ]
        
        # Regras para documento
        document_rules = [
            ValidationRule(
                name='titulo_required',
                field='titulo',
                validator=self.custom_validators['required'],
                message='Título é obrigatório',
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.REQUIRED
            ),
            ValidationRule(
                name='titulo_length',
                field='titulo',
                validator=lambda v, d: 3 <= len(str(v)) <= 200,
                message='Título deve ter entre 3 e 200 caracteres',
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT
            ),
            ValidationRule(
                name='conteudo_required',
                field='conteudo',
                validator=self.custom_validators['required'],
                message='Conteúdo é obrigatório',
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.REQUIRED
            ),
            ValidationRule(
                name='conteudo_length',
                field='conteudo',
                validator=lambda v, d: len(str(v)) >= 10,
                message='Conteúdo deve ter pelo menos 10 caracteres',
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT
            ),
            ValidationRule(
                name='conteudo_legal',
                field='conteudo',
                validator=self.custom_validators['legal_document'],
                message='Documento deve conter estrutura jurídica adequada',
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.LEGAL
            ),
            ValidationRule(
                name='conteudo_security',
                field='conteudo',
                validator=self.custom_validators['no_script'],
                message='Conteúdo não deve conter scripts maliciosos',
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SECURITY
            )
        ]
        
        # Regras para template
        template_rules = [
            ValidationRule(
                name='titulo_required',
                field='titulo',
                validator=self.custom_validators['required'],
                message='Título do template é obrigatório',
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.REQUIRED
            ),
            ValidationRule(
                name='conteudo_required',
                field='conteudo',
                validator=self.custom_validators['required'],
                message='Conteúdo do template é obrigatório',
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.REQUIRED
            ),
            ValidationRule(
                name='categoria_required',
                field='categoria',
                validator=self.custom_validators['required'],
                message='Categoria é obrigatória',
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.REQUIRED
            ),
            ValidationRule(
                name='template_variables',
                field='conteudo',
                validator=lambda v, d: self._validate_template_variables(v),
                message='Template deve conter variáveis válidas',
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.BUSINESS
            )
        ]
        
        self.rules = {
            'user': user_rules,
            'document': document_rules,
            'template': template_rules
        }
    
    def _validate_email(self, email: str) -> bool:
        """Validar formato de email"""
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _validate_cpf(self, cpf: str) -> bool:
        """Validar CPF"""
        if not cpf:
            return False
        
        # Remover formatação
        cpf = re.sub(r'\D', '', cpf)
        
        # Verificar tamanho
        if len(cpf) != 11:
            return False
        
        # Verificar sequências inválidas
        if cpf == cpf[0] * 11:
            return False
        
        # Calcular dígitos verificadores
        def calculate_digit(cpf_digits):
            total = sum(int(digit) * weight for digit, weight in zip(cpf_digits, range(len(cpf_digits) + 1, 1, -1)))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # Verificar primeiro dígito
        if int(cpf[9]) != calculate_digit(cpf[:9]):
            return False
        
        # Verificar segundo dígito
        if int(cpf[10]) != calculate_digit(cpf[:10]):
            return False
        
        return True
    
    def _validate_cnpj(self, cnpj: str) -> bool:
        """Validar CNPJ"""
        if not cnpj:
            return False
        
        # Remover formatação
        cnpj = re.sub(r'\D', '', cnpj)
        
        # Verificar tamanho
        if len(cnpj) != 14:
            return False
        
        # Verificar sequências inválidas
        if cnpj == cnpj[0] * 14:
            return False
        
        # Calcular dígitos verificadores
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        
        def calculate_digit(cnpj_digits, weights):
            total = sum(int(digit) * weight for digit, weight in zip(cnpj_digits, weights))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # Verificar primeiro dígito
        if int(cnpj[12]) != calculate_digit(cnpj[:12], weights1):
            return False
        
        # Verificar segundo dígito
        if int(cnpj[13]) != calculate_digit(cnpj[:13], weights2):
            return False
        
        return True
    
    def _validate_phone(self, phone: str) -> bool:
        """Validar telefone brasileiro"""
        if not phone:
            return False
        
        # Remover formatação
        phone = re.sub(r'\D', '', phone)
        
        # Verificar tamanho (10 ou 11 dígitos)
        if len(phone) not in [10, 11]:
            return False
        
        # Verificar se começa com DDD válido
        ddd = phone[:2]
        valid_ddds = ['11', '12', '13', '14', '15', '16', '17', '18', '19',  # SP
                      '21', '22', '24',  # RJ
                      '27', '28',  # ES
                      '31', '32', '33', '34', '35', '37', '38',  # MG
                      '41', '42', '43', '44', '45', '46',  # PR
                      '47', '48', '49',  # SC
                      '51', '53', '54', '55',  # RS
                      '61',  # DF
                      '62', '64',  # GO
                      '63',  # TO
                      '65', '66',  # MT
                      '67',  # MS
                      '68',  # AC
                      '69',  # RO
                      '71', '73', '74', '75', '77',  # BA
                      '79',  # SE
                      '81', '87',  # PE
                      '82',  # AL
                      '83',  # PB
                      '84',  # RN
                      '85', '88',  # CE
                      '86', '89',  # PI
                      '91', '93', '94',  # PA
                      '92', '97',  # AM
                      '95',  # RR
                      '96',  # AP
                      '98', '99']  # MA
        
        return ddd in valid_ddds
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validar força da senha"""
        if not password:
            return False
        
        # Mínimo 8 caracteres
        if len(password) < 8:
            return False
        
        # Deve conter pelo menos uma maiúscula
        if not re.search(r'[A-Z]', password):
            return False
        
        # Deve conter pelo menos uma minúscula
        if not re.search(r'[a-z]', password):
            return False
        
        # Deve conter pelo menos um número
        if not re.search(r'\d', password):
            return False
        
        return True
    
    def _validate_date_format(self, date_str: str) -> bool:
        """Validar formato de data"""
        if not date_str:
            return False
        
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
        
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    def _validate_url(self, url: str) -> bool:
        """Validar URL"""
        if not url:
            return False
        
        pattern = r'^https?:\/\/(?:[-\w.])+(?:\:[0-9]+)?(?:\/(?:[\w\/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
        return bool(re.match(pattern, url))
    
    def _validate_legal_document(self, content: str) -> bool:
        """Validar se é um documento jurídico válido"""
        if not content:
            return False
        
        # Verificar estrutura básica
        legal_indicators = [
            r'CLÁUSULA|ARTIGO|PARÁGRAFO',
            r'CONSIDERANDO|RESOLVE|DETERMINA',
            r'CONTRATANTE|CONTRATADO',
            r'EXCELENTÍSSIMO|MERITÍSSIMO',
            r'PROCURAÇÃO|PODERES'
        ]
        
        found_indicators = 0
        for pattern in legal_indicators:
            if re.search(pattern, content, re.IGNORECASE):
                found_indicators += 1
        
        return found_indicators >= 1
    
    def _validate_no_script(self, content: str) -> bool:
        """Validar que não contém scripts maliciosos"""
        if not content:
            return True
        
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'document\.\w+',
            r'window\.\w+'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False
        
        return True
    
    def _validate_sanitized(self, content: str) -> bool:
        """Validar que o conteúdo está sanitizado"""
        if not content:
            return True
        
        # Verificar tags HTML perigosas
        dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form', 'input']
        
        for tag in dangerous_tags:
            if f'<{tag}' in content.lower():
                return False
        
        return True
    
    def _validate_template_variables(self, content: str) -> bool:
        """Validar variáveis do template"""
        if not content:
            return False
        
        # Verificar se tem pelo menos uma variável
        variable_patterns = [
            r'\{\{[^}]+\}\}',  # {{variavel}}
            r'\[([A-Z_][A-Z0-9_]*)\]',  # [VARIAVEL]
            r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}',  # {variavel}
        ]
        
        for pattern in variable_patterns:
            if re.search(pattern, content):
                return True
        
        return False
    
    def _get_field_value(self, data: Dict[str, Any], field: str) -> Any:
        """Obter valor do campo, suportando notação ponto"""
        keys = field.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _check_conditions(self, conditions: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Verificar se as condições são atendidas"""
        for field, expected_value in conditions.items():
            actual_value = self._get_field_value(data, field)
            if actual_value != expected_value:
                return False
        return True
    
    def _get_suggestions(self, rule: ValidationRule, value: Any) -> List[str]:
        """Obter sugestões para correção"""
        suggestions = []
        
        if rule.name == 'email_format':
            suggestions.append('Use o formato: nome@dominio.com')
        elif rule.name == 'senha_strength':
            suggestions.extend([
                'Use pelo menos 8 caracteres',
                'Inclua letras maiúsculas e minúsculas',
                'Adicione pelo menos um número',
                'Considere usar caracteres especiais'
            ])
        elif rule.name == 'cpf':
            suggestions.append('Use o formato: 000.000.000-00')
        elif rule.name == 'cnpj':
            suggestions.append('Use o formato: 00.000.000/0000-00')
        elif rule.name == 'phone':
            suggestions.append('Use o formato: (00) 00000-0000')
        
        return suggestions
    
    def _calculate_validation_score(self, results: List[ValidationResult], total_rules: int) -> float:
        """Calcular score de validação"""
        if total_rules == 0:
            return 1.0
        
        error_penalty = sum(1 for r in results if r.severity == ValidationSeverity.ERROR)
        warning_penalty = sum(0.5 for r in results if r.severity == ValidationSeverity.WARNING)
        
        total_penalty = error_penalty + warning_penalty
        passed_rules = total_rules - len(results)
        
        score = passed_rules / total_rules
        score -= (total_penalty / total_rules)
        
        return max(0.0, min(1.0, score))
    
    def _format_result(self, result: ValidationResult) -> Dict[str, Any]:
        """Formatar resultado de validação"""
        formatted = {
            'field': result.field,
            'rule': result.rule_name,
            'message': result.message,
            'severity': result.severity.value,
            'category': result.category.value
        }
        
        if result.value is not None:
            formatted['value'] = result.value
        
        if result.suggestions:
            formatted['suggestions'] = result.suggestions
        
        return formatted

# Instância global
advanced_validator = AdvancedValidator() 