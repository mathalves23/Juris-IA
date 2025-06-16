# 📚 DOCUMENTAÇÃO COMPLETA DA API - JURISSAAS

## 📋 Visão Geral

A API do JurisSaaS é uma API RESTful que fornece funcionalidades completas para gerenciamento de documentos jurídicos, templates inteligentes, análise por IA e muito mais.

### 🔗 URL Base
```
https://api.jurissaas.com/api
```

### 📊 Versão da API
```
v1.0
```

### 🔐 Autenticação
A API utiliza **JWT (JSON Web Tokens)** para autenticação. Inclua o token no header de todas as requisições protegidas:

```http
Authorization: Bearer <seu_jwt_token>
```

## 🔑 Autenticação

### POST /auth/register
Registrar novo usuário

**Request:**
```json
{
  "nome": "João Silva",
  "email": "joao@escritorio.com",
  "senha": "MinhaSenh@123"
}
```

**Response (201):**
```json
{
  "message": "Usuário criado com sucesso",
  "user_id": 123
}
```

**Validações:**
- Nome: 2-100 caracteres
- Email: formato válido e único
- Senha: mínimo 8 caracteres, incluindo maiúscula, minúscula e número

### POST /auth/login
Realizar login

**Request:**
```json
{
  "email": "joao@escritorio.com",
  "senha": "MinhaSenh@123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 123,
    "nome": "João Silva",
    "email": "joao@escritorio.com",
    "foto_url": null,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "expires_in": 3600
}
```

### POST /auth/refresh
Renovar token de acesso

**Headers:**
```http
Authorization: Bearer <refresh_token>
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "expires_in": 3600
}
```

### GET /auth/me
Obter dados do usuário autenticado

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 123,
  "nome": "João Silva",
  "email": "joao@escritorio.com",
  "foto_url": "https://example.com/foto.jpg",
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-20T14:30:00Z",
  "subscription": {
    "plan": "premium",
    "expires_at": "2024-12-31T23:59:59Z",
    "features": ["ai_analysis", "unlimited_templates", "export_pdf"]
  }
}
```

### PUT /auth/me
Atualizar perfil do usuário

**Request:**
```json
{
  "nome": "João Santos Silva",
  "foto_url": "https://example.com/nova-foto.jpg"
}
```

**Response (200):**
```json
{
  "message": "Perfil atualizado com sucesso",
  "user": {
    "id": 123,
    "nome": "João Santos Silva",
    "email": "joao@escritorio.com",
    "foto_url": "https://example.com/nova-foto.jpg"
  }
}
```

## 📄 Documentos

### GET /documents
Listar documentos do usuário

**Query Parameters:**
- `page` (opcional): Página (padrão: 1)
- `per_page` (opcional): Itens por página (padrão: 20, máximo: 100)
- `search` (opcional): Busca por título ou conteúdo
- `status` (opcional): Filtrar por status (rascunho, finalizado, arquivado)
- `template_id` (opcional): Filtrar por template
- `sort` (opcional): Ordenação (created_at, updated_at, titulo)
- `order` (opcional): Direção (asc, desc)

**Response (200):**
```json
{
  "documents": [
    {
      "id": 456,
      "titulo": "Contrato de Prestação de Serviços",
      "status": "finalizado",
      "template_id": 789,
      "template_titulo": "Contrato Padrão",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-16T15:45:00Z",
      "word_count": 1250,
      "ai_score": 0.85
    }
  ],
  "pagination": {
    "page": 1,
    "pages": 5,
    "per_page": 20,
    "total": 95
  },
  "stats": {
    "total_documents": 95,
    "drafts": 12,
    "completed": 78,
    "archived": 5
  }
}
```

### POST /documents
Criar novo documento

**Request:**
```json
{
  "titulo": "Novo Contrato",
  "conteudo": "Conteúdo do documento...",
  "template_id": 789,
  "status": "rascunho",
  "metadata": {
    "client_name": "Empresa XYZ",
    "contract_type": "service",
    "value": 15000.00
  }
}
```

**Response (201):**
```json
{
  "id": 457,
  "titulo": "Novo Contrato",
  "status": "rascunho",
  "created_at": "2024-01-20T16:00:00Z",
  "validation": {
    "valid": true,
    "score": 0.78,
    "warnings": ["Adicionar cláusula de foro"],
    "errors": []
  }
}
```

### GET /documents/{id}
Obter documento específico

**Response (200):**
```json
{
  "id": 456,
  "titulo": "Contrato de Prestação de Serviços",
  "conteudo": "Conteúdo completo do documento...",
  "status": "finalizado",
  "template_id": 789,
  "user_id": 123,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-16T15:45:00Z",
  "metadata": {
    "client_name": "Empresa XYZ",
    "contract_type": "service",
    "value": 15000.00,
    "ai_analysis": {
      "score": 0.85,
      "risks": ["baixo"],
      "suggestions": ["Revisar cláusula de pagamento"]
    }
  }
}
```

### PUT /documents/{id}
Atualizar documento

**Request:**
```json
{
  "titulo": "Contrato Atualizado",
  "conteudo": "Novo conteúdo...",
  "status": "finalizado"
}
```

**Response (200):**
```json
{
  "message": "Documento atualizado com sucesso",
  "validation": {
    "valid": true,
    "score": 0.82,
    "changes_detected": ["content", "status"]
  }
}
```

### DELETE /documents/{id}
Excluir documento

**Response (200):**
```json
{
  "message": "Documento excluído com sucesso"
}
```

## 📋 Templates

### GET /templates
Listar templates

**Query Parameters:**
- `page`, `per_page`: Paginação
- `search`: Busca textual
- `category`: Filtrar por categoria
- `complexity`: Filtrar por complexidade (basico, intermediario, avancado)
- `legal_area`: Filtrar por área jurídica
- `public_only`: Mostrar apenas templates públicos (boolean)

**Response (200):**
```json
{
  "templates": [
    {
      "id": 789,
      "titulo": "Contrato de Prestação de Serviços",
      "categoria": "contratos_civil",
      "publico": true,
      "autor": "Sistema",
      "rating": 4.5,
      "usage_count": 234,
      "created_at": "2024-01-01T00:00:00Z",
      "metadata": {
        "complexity": "intermediario",
        "legal_area": "civil",
        "estimated_time": 30,
        "tags": ["contrato", "servicos", "civil"]
      },
      "preview": "CONTRATO DE PRESTAÇÃO DE SERVIÇOS..."
    }
  ],
  "pagination": {
    "page": 1,
    "pages": 8,
    "per_page": 20,
    "total": 156
  }
}
```

### POST /templates
Criar novo template

**Request:**
```json
{
  "titulo": "Meu Template Personalizado",
  "conteudo": "CONTRATO DE {{TIPO}}\n\nCONTRATANTE: {{NOME_CONTRATANTE}}...",
  "categoria": "contratos_civil",
  "publico": false,
  "metadata": {
    "complexity": "basico",
    "legal_area": "civil",
    "tags": ["contrato", "personalizado"],
    "required_fields": ["TIPO", "NOME_CONTRATANTE", "NOME_CONTRATADO"],
    "estimated_time": 15
  }
}
```

**Response (201):**
```json
{
  "id": 790,
  "message": "Template criado com sucesso",
  "variables_detected": ["TIPO", "NOME_CONTRATANTE", "NOME_CONTRATADO"],
  "quality_score": 0.78,
  "validation": {
    "valid": true,
    "warnings": ["Considere adicionar cláusula de foro"]
  }
}
```

### POST /templates/{id}/generate
Gerar documento a partir de template

**Request:**
```json
{
  "variables": {
    "TIPO": "Consultoria Jurídica",
    "NOME_CONTRATANTE": "João Silva",
    "NOME_CONTRATADO": "Escritório ABC",
    "VALOR": 5000.00,
    "PRAZO": "60 dias"
  },
  "auto_save": true
}
```

**Response (200):**
```json
{
  "content": "CONTRATO DE CONSULTORIA JURÍDICA\n\nCONTRATANTE: João Silva...",
  "document_id": 458,
  "validation": {
    "valid": true,
    "quality_score": 0.89,
    "missing_fields": [],
    "suggestions": ["Revisar valores monetários"]
  }
}
```

## 🤖 Inteligência Artificial

### POST /ai/analyze
Analisar documento com IA

**Request:**
```json
{
  "content": "Conteúdo do documento para análise...",
  "document_type": "contrato",
  "legal_area": "civil",
  "analysis_depth": "detailed"
}
```

**Response (200):**
```json
{
  "analysis": {
    "overall_score": 0.82,
    "structure_score": 0.85,
    "legal_compliance": 0.80,
    "risk_assessment": "medium",
    "suggestions": [
      {
        "type": "improvement",
        "priority": "high",
        "description": "Adicionar cláusula de resolução de conflitos",
        "location": "section_6"
      }
    ],
    "identified_clauses": [
      {
        "type": "payment",
        "content": "Pagamento em 30 dias",
        "status": "valid"
      }
    ],
    "missing_clauses": ["foro", "vigencia"],
    "legal_references": [
      {
        "law": "Código Civil",
        "article": "Art. 421",
        "relevance": "high"
      }
    ]
  },
  "processing_time": 2.3
}
```

### POST /ai/suggest-clauses
Sugerir cláusulas para documento

**Request:**
```json
{
  "document_type": "contrato",
  "legal_area": "trabalhista",
  "existing_content": "Conteúdo parcial do documento...",
  "context": {
    "contract_value": 50000,
    "duration": "12 meses",
    "parties": ["employer", "employee"]
  }
}
```

**Response (200):**
```json
{
  "suggestions": [
    {
      "clause_type": "rescission",
      "title": "Cláusula de Rescisão",
      "content": "O presente contrato poderá ser rescindido...",
      "importance": "essential",
      "legal_basis": "CLT Art. 482"
    }
  ],
  "priority_clauses": ["rescission", "payment", "obligations"],
  "estimated_completion": 0.75
}
```

### POST /ai/legal-research
Pesquisa jurídica assistida por IA

**Request:**
```json
{
  "query": "Responsabilidade civil por danos morais",
  "legal_area": "civil",
  "jurisdiction": "brasil",
  "depth": "comprehensive"
}
```

**Response (200):**
```json
{
  "research": {
    "summary": "Resumo da pesquisa sobre responsabilidade civil...",
    "key_concepts": ["dano moral", "nexo causal", "culpa"],
    "legislation": [
      {
        "law": "Código Civil",
        "articles": ["Art. 186", "Art. 927"],
        "summary": "Fundamentos da responsabilidade civil"
      }
    ],
    "jurisprudence": [
      {
        "court": "STJ",
        "case": "REsp 1.234.567",
        "summary": "Precedente importante sobre danos morais",
        "date": "2023-05-15"
      }
    ],
    "recommendations": [
      "Analisar nexo causal",
      "Quantificar danos",
      "Verificar excludentes de responsabilidade"
    ]
  }
}
```

## 📤 Upload e Exportação

### POST /upload/document
Upload de documento para análise

**Request (multipart/form-data):**
```
file: [arquivo.pdf/.docx/.txt]
document_type: "contrato"
auto_analyze: true
```

**Response (200):**
```json
{
  "file_id": "uuid-file-id",
  "original_name": "contrato.pdf",
  "file_size": 245760,
  "extracted_text": "Texto extraído do documento...",
  "document_created": true,
  "document_id": 459,
  "analysis": {
    "confidence": 0.92,
    "detected_type": "contrato_prestacao_servicos",
    "suggestions": ["Revisar formatação"]
  }
}
```

### GET /export/document/{id}
Exportar documento

**Query Parameters:**
- `format`: pdf, docx, txt, html (padrão: pdf)
- `template`: layout de exportação
- `watermark`: adicionar marca d'água (boolean)

**Response (200):**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="documento.pdf"

[Binary content]
```

## 📊 Analytics e Relatórios

### GET /analytics/dashboard
Dashboard de analytics do usuário

**Response (200):**
```json
{
  "period": "last_30_days",
  "stats": {
    "documents_created": 15,
    "templates_used": 8,
    "ai_analyses": 12,
    "export_count": 25
  },
  "trends": {
    "documents_growth": 0.23,
    "most_used_template": {
      "id": 789,
      "title": "Contrato Padrão",
      "usage_count": 5
    }
  },
  "recent_activity": [
    {
      "type": "document_created",
      "timestamp": "2024-01-20T14:30:00Z",
      "document_title": "Novo Contrato"
    }
  ]
}
```

## 🔧 Sistema e Monitoramento

### GET /health
Health check da aplicação

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T16:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "ai_service": "available"
  },
  "metrics": {
    "response_time": 0.045,
    "memory_usage": "67%",
    "active_connections": 15
  }
}
```

### GET /cache/stats
Estatísticas do cache (admin apenas)

**Response (200):**
```json
{
  "strategy": "hybrid",
  "hit_rate": 85.2,
  "total_requests": 1250,
  "cache_size": "45MB",
  "redis_status": "connected",
  "memory_keys": 145
}
```

## ⚠️ Códigos de Erro

### Códigos HTTP Padrão

| Código | Descrição | Exemplo |
|---------|-----------|---------|
| 200 | Sucesso | Operação realizada com sucesso |
| 201 | Criado | Recurso criado com sucesso |
| 400 | Bad Request | Dados inválidos na requisição |
| 401 | Unauthorized | Token inválido ou expirado |
| 403 | Forbidden | Acesso negado ao recurso |
| 404 | Not Found | Recurso não encontrado |
| 422 | Unprocessable Entity | Dados válidos mas não processáveis |
| 429 | Too Many Requests | Rate limit excedido |
| 500 | Internal Server Error | Erro interno do servidor |

### Formato de Erro Padrão

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dados de entrada inválidos",
    "details": {
      "field": "email",
      "issue": "Formato de email inválido"
    },
    "timestamp": "2024-01-20T16:00:00Z",
    "request_id": "req_123456789"
  }
}
```

## 🔒 Rate Limiting

A API implementa rate limiting para proteger contra abuso:

| Endpoint | Limite | Janela |
|----------|--------|--------|
| `/auth/login` | 5 tentativas | 5 minutos |
| `/auth/register` | 3 registros | 1 hora |
| `/ai/*` | 20 requests | 1 hora |
| `/upload/*` | 10 uploads | 1 hora |
| Geral | 100 requests | 1 hora |

### Headers de Rate Limiting

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642694400
```

## 📝 Changelog

### v1.0.0 (2024-01-20)
- Lançamento inicial da API
- Funcionalidades básicas de CRUD
- Integração com IA
- Sistema de templates avançado
- Cache e performance otimizados
- Rate limiting implementado
- Documentação completa 