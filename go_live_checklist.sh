#!/bin/bash

# Checklist final de go-live para o Editor IA JurisSaaS
# Este script verifica todos os componentes críticos antes da liberação para usuários

echo "Iniciando checklist final de go-live para o Editor IA JurisSaaS..."

# Verificar parâmetros
if [ -z "$1" ]; then
  echo "Uso: $0 <URL_BASE>"
  echo "Exemplo: $0 https://app.jurissaas.com.br"
  exit 1
fi

BASE_URL=$1
API_URL="$BASE_URL/api"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
REPORT_FILE="go_live_checklist_$TIMESTAMP.txt"

echo "URL base: $BASE_URL" | tee -a $REPORT_FILE
echo "URL da API: $API_URL" | tee -a $REPORT_FILE
echo "Data e hora: $(date)" | tee -a $REPORT_FILE
echo "----------------------------------------" | tee -a $REPORT_FILE

# Função para verificar e registrar resultados
check_item() {
  local item=$1
  local status=$2
  local details=$3
  
  if [ "$status" = "OK" ]; then
    echo "[✓] $item: $status" | tee -a $REPORT_FILE
  else
    echo "[✗] $item: $status - $details" | tee -a $REPORT_FILE
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
  fi
}

# Inicializar contador de falhas
FAILED_CHECKS=0

# 1. Verificar acesso ao frontend
echo "1. Verificando acesso ao frontend..." | tee -a $REPORT_FILE
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL")
if [ "$FRONTEND_STATUS" -eq 200 ]; then
  check_item "Acesso ao frontend" "OK" ""
else
  check_item "Acesso ao frontend" "FALHA" "Status HTTP: $FRONTEND_STATUS"
fi

# 2. Verificar acesso à API
echo "2. Verificando acesso à API..." | tee -a $REPORT_FILE
API_HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
if [ "$API_HEALTH_STATUS" -eq 200 ]; then
  check_item "Acesso à API" "OK" ""
else
  check_item "Acesso à API" "FALHA" "Status HTTP: $API_HEALTH_STATUS"
fi

# 3. Verificar certificado SSL
echo "3. Verificando certificado SSL..." | tee -a $REPORT_FILE
SSL_VALID=$(echo | openssl s_client -connect ${BASE_URL#https://}:443 2>/dev/null | openssl x509 -noout -checkend 0)
if [ $? -eq 0 ]; then
  SSL_EXPIRY=$(echo | openssl s_client -connect ${BASE_URL#https://}:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
  SSL_DAYS_LEFT=$(( ( $(date -d "$SSL_EXPIRY" +%s) - $(date +%s) ) / 86400 ))
  check_item "Certificado SSL" "OK" "Expira em $SSL_DAYS_LEFT dias"
else
  check_item "Certificado SSL" "FALHA" "Certificado inválido ou expirado"
fi

# 4. Verificar serviços do sistema
echo "4. Verificando serviços do sistema..." | tee -a $REPORT_FILE
# Nota: Esta verificação só funciona se executada no servidor de produção
if systemctl is-active --quiet jurissaas-backend 2>/dev/null; then
  check_item "Serviço backend" "OK" ""
else
  check_item "Serviço backend" "AVISO" "Não foi possível verificar (execute este script no servidor de produção)"
fi

if systemctl is-active --quiet nginx 2>/dev/null; then
  check_item "Serviço Nginx" "OK" ""
else
  check_item "Serviço Nginx" "AVISO" "Não foi possível verificar (execute este script no servidor de produção)"
fi

if systemctl is-active --quiet mysql 2>/dev/null; then
  check_item "Serviço MySQL" "OK" ""
else
  check_item "Serviço MySQL" "AVISO" "Não foi possível verificar (execute este script no servidor de produção)"
fi

# 5. Verificar funcionalidades críticas
echo "5. Verificando funcionalidades críticas..." | tee -a $REPORT_FILE

# 5.1 Teste de registro/login
echo "5.1 Testando autenticação..." | tee -a $REPORT_FILE
TEST_EMAIL="go_live_test@jurissaas.com.br"
TEST_PASSWORD="GoLive@123"
TEST_NAME="Usuário Teste Go-Live"

REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"nome\":\"$TEST_NAME\",\"email\":\"$TEST_EMAIL\",\"senha\":\"$TEST_PASSWORD\"}")

if echo "$REGISTER_RESPONSE" | grep -q "error"; then
  # Tentar login caso o usuário já exista
  LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"senha\":\"$TEST_PASSWORD\"}")
  
  if echo "$LOGIN_RESPONSE" | grep -q "error"; then
    check_item "Autenticação" "FALHA" "Erro no login: $(echo $LOGIN_RESPONSE | grep -o '"error":"[^"]*' | sed 's/"error":"//')"
  else
    check_item "Autenticação" "OK" "Login bem-sucedido"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')
  fi
else
  check_item "Autenticação" "OK" "Registro bem-sucedido"
  ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')
fi

if [ -z "$ACCESS_TOKEN" ]; then
  check_item "Token de acesso" "FALHA" "Não foi possível obter token"
else
  check_item "Token de acesso" "OK" ""
  
  # 5.2 Teste de criação de documento
  echo "5.2 Testando criação de documento..." | tee -a $REPORT_FILE
  CREATE_DOC_RESPONSE=$(curl -s -X POST "$API_URL/documents" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"titulo\":\"Documento de Teste Go-Live\",\"conteudo\":\"<p>Conteúdo de teste para go-live</p>\",\"status\":\"Rascunho\"}")
  
  if echo "$CREATE_DOC_RESPONSE" | grep -q "error"; then
    check_item "Criação de documento" "FALHA" "Erro: $(echo $CREATE_DOC_RESPONSE | grep -o '"error":"[^"]*' | sed 's/"error":"//')"
  else
    check_item "Criação de documento" "OK" ""
    
    # Extrair ID do documento
    DOC_ID=$(echo "$CREATE_DOC_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | sed 's/"id"://')
    
    if [ -z "$DOC_ID" ]; then
      check_item "ID do documento" "FALHA" "Não foi possível extrair o ID"
    else
      check_item "ID do documento" "OK" "ID: $DOC_ID"
      
      # 5.3 Teste de IA
      echo "5.3 Testando integração com IA..." | tee -a $REPORT_FILE
      AI_RESPONSE=$(curl -s -X POST "$API_URL/ai/generate" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"prompt\":\"Escreva uma breve introdução sobre direito civil\",\"document_id\":$DOC_ID}")
      
      if echo "$AI_RESPONSE" | grep -q "error"; then
        check_item "Integração com IA" "FALHA" "Erro: $(echo $AI_RESPONSE | grep -o '"error":"[^"]*' | sed 's/"error":"//')"
      else
        check_item "Integração com IA" "OK" ""
      fi
    fi
  fi
fi

# 6. Verificar monitoramento
echo "6. Verificando monitoramento..." | tee -a $REPORT_FILE
# Nota: Esta verificação só funciona se executada no servidor de produção
if systemctl is-active --quiet prometheus 2>/dev/null; then
  check_item "Prometheus" "OK" ""
else
  check_item "Prometheus" "AVISO" "Não foi possível verificar (execute este script no servidor de produção)"
fi

if systemctl is-active --quiet grafana-server 2>/dev/null; then
  check_item "Grafana" "OK" ""
else
  check_item "Grafana" "AVISO" "Não foi possível verificar (execute este script no servidor de produção)"
fi

# 7. Verificar backup
echo "7. Verificando backup..." | tee -a $REPORT_FILE
# Nota: Esta verificação só funciona se executada no servidor de produção
if [ -f "/usr/local/bin/backup-jurissaas.sh" ] && [ -x "/usr/local/bin/backup-jurissaas.sh" ]; then
  check_item "Script de backup" "OK" ""
else
  check_item "Script de backup" "AVISO" "Não foi possível verificar (execute este script no servidor de produção)"
fi

# Verificar se há entradas de cron para backup
CRON_BACKUP=$(crontab -l 2>/dev/null | grep backup-jurissaas)
if [ -n "$CRON_BACKUP" ]; then
  check_item "Agendamento de backup" "OK" ""
else
  check_item "Agendamento de backup" "AVISO" "Não foi possível verificar (execute este script no servidor de produção)"
fi

# 8. Resumo final
echo "----------------------------------------" | tee -a $REPORT_FILE
echo "Resumo do checklist de go-live:" | tee -a $REPORT_FILE
if [ $FAILED_CHECKS -eq 0 ]; then
  echo "✓ Todos os checks passaram com sucesso!" | tee -a $REPORT_FILE
  echo "O sistema está pronto para ser liberado para os usuários." | tee -a $REPORT_FILE
else
  echo "✗ $FAILED_CHECKS checks falharam. Corrija os problemas antes de liberar o sistema." | tee -a $REPORT_FILE
fi

echo "----------------------------------------" | tee -a $REPORT_FILE
echo "Relatório salvo em: $REPORT_FILE"
echo ""
echo "Para liberar o sistema para os usuários, execute:"
echo "  ./release_to_users.sh $BASE_URL"
