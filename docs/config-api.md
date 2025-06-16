# API de Configurações - JurisIA

## Visão Geral

A API de configurações permite gerenciar flags e configurações de ambiente (test/prod) da plataforma JurisIA. Esta funcionalidade permite configurar comportamentos diferentes da aplicação baseado no ambiente de execução.

## Autenticação

Todas as rotas requerem autenticação JWT. O token deve ser enviado no header:
```
Authorization: Bearer <token>
```

## Rotas Disponíveis

### 1. Configurar Flags (`POST /api/auth/set-flags`)

Define configurações baseadas em uma string de flags para um ambiente específico.

**Permissões**: Apenas usuários com papel `admin` ou `superuser`

**Body Request**:
```json
{
  "flags": "debug_mode=true,max_users=100,api_version=v2",
  "environment": "test"
}
```

**Parâmetros**:
- `flags` (string): String com as configurações no formato `key=value,key2=value2`
- `environment` (string): Ambiente alvo (`test` ou `prod`)

**Response Success (200)**:
```json
{
  "message": "Flags configuradas com sucesso para o ambiente test", 
  "environment": "test",
  "flags": {
    "debug_mode": true,
    "max_users": 100,
    "api_version": "v2"
  }
}
```

**Tipos de Valores Suportados**:
- `true/false` → convertido para boolean
- Números → convertido para integer
- Strings → mantido como string

### 2. Obter Flags (`GET /api/auth/flags`)

Retorna as configurações atuais para um ambiente específico.

**Query Parameters**:
- `environment` (string, opcional): Ambiente (`test` ou `prod`). Default: `test`

**Response Success (200)**:
```json
{
  "environment": "test",
  "flags": {
    "debug_mode": true,
    "ai_enabled": true,
    "document_limit": 100,
    "export_pdf": true,
    "export_docx": true,
    "max_file_size": 16777216,
    "api_version": "v2",
    "max_users": 50
  }
}
```

## Configurações Padrão

### Ambiente de Teste (test)
- `debug_mode`: true
- `ai_enabled`: true
- `document_limit`: 100
- `export_pdf`: true
- `export_docx`: true
- `max_file_size`: 16777216 (16MB)

### Ambiente de Produção (prod)
- `debug_mode`: false
- `ai_enabled`: true
- `document_limit`: 1000
- `export_pdf`: true
- `export_docx`: true
- `max_file_size`: 16777216 (16MB)
- `rate_limit_requests`: 1000
- `session_timeout`: 3600

## Exemplos de Uso

### Frontend JavaScript

```javascript
import { setFlagsFromString, getFlags } from '../services/authService';

// Configurar flags de desenvolvimento
try {
  const result = await setFlagsFromString(
    'debug_mode=true,api_version=v2,max_users=50', 
    'test'
  );
  console.log('Flags configuradas:', result);
} catch (error) {
  console.error('Erro:', error.message);
}

// Obter flags atuais
try {
  const flags = await getFlags('prod');
  console.log('Flags de produção:', flags);
} catch (error) {
  console.error('Erro:', error.message);
}
```

### Curl

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:5005/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@jurissaas.com","senha":"admin123"}' | \
  jq -r '.access_token')

# Configurar flags
curl -X POST http://localhost:5005/api/auth/set-flags \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "flags": "maintenance_mode=false,max_concurrent_users=500",
    "environment": "prod"
  }'

# Obter flags
curl -X GET "http://localhost:5005/api/auth/flags?environment=prod" \
  -H "Authorization: Bearer $TOKEN"
```

## Estrutura do Banco

As configurações são armazenadas na tabela `configs`:

```sql
CREATE TABLE configs (
    id INTEGER PRIMARY KEY,
    environment VARCHAR(20) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT,
    value_type VARCHAR(20) DEFAULT 'string',
    description TEXT,
    user_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Casos de Uso

1. **Configuração de Ambiente**: Diferentes limites de documentos entre test e prod
2. **Feature Flags**: Habilitar/desabilitar funcionalidades específicas
3. **Configurações de Performance**: Rate limits, timeouts, etc.
4. **Modo de Manutenção**: Controlar acesso durante updates
5. **Configurações de AI**: Habilitar/desabilitar funcionalidades de IA

## Notas de Segurança

- Apenas usuários admin podem modificar configurações
- Todas as mudanças são logadas com timestamp e usuário
- Configurações são validadas antes de serem aplicadas
- Environments são restritos a 'test' e 'prod' 