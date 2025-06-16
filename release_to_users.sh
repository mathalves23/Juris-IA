#!/bin/bash

# Script de liberação para usuários do Editor IA JurisSaaS
# Este script finaliza o processo de go-live e libera o sistema para os usuários

echo "Iniciando processo de liberação do Editor IA JurisSaaS para usuários..."

# Verificar parâmetros
if [ -z "$1" ]; then
  echo "Uso: $0 <URL_BASE>"
  echo "Exemplo: $0 https://app.jurissaas.com.br"
  exit 1
fi

BASE_URL=$1
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Verificar se o checklist foi executado
LATEST_CHECKLIST=$(ls -t go_live_checklist_*.txt 2>/dev/null | head -1)
if [ -z "$LATEST_CHECKLIST" ]; then
  echo "ERRO: Checklist de go-live não encontrado!"
  echo "Execute primeiro o script go_live_checklist.sh para validar o sistema."
  exit 1
fi

# Verificar se o checklist passou
if grep -q "Todos os checks passaram com sucesso" "$LATEST_CHECKLIST"; then
  echo "Checklist de go-live validado com sucesso!"
else
  echo "ERRO: O checklist de go-live contém falhas!"
  echo "Corrija os problemas identificados no relatório: $LATEST_CHECKLIST"
  echo "Execute novamente o script go_live_checklist.sh após as correções."
  exit 1
fi

echo "Sistema validado e pronto para liberação!"
echo ""
echo "Realizando últimas verificações..."

# Registrar evento de go-live
echo "Registrando evento de go-live..."
GO_LIVE_LOG="go_live_event_$TIMESTAMP.log"
echo "===================================" > $GO_LIVE_LOG
echo "GO-LIVE DO EDITOR IA JURISSAAS" >> $GO_LIVE_LOG
echo "===================================" >> $GO_LIVE_LOG
echo "Data e hora: $(date)" >> $GO_LIVE_LOG
echo "URL: $BASE_URL" >> $GO_LIVE_LOG
echo "Checklist: $LATEST_CHECKLIST" >> $GO_LIVE_LOG
echo "===================================" >> $GO_LIVE_LOG

# Criar usuário administrador inicial (se executado no servidor)
echo "Deseja criar um usuário administrador inicial? (s/n)"
read CREATE_ADMIN

if [ "$CREATE_ADMIN" = "s" ]; then
  echo "Criando usuário administrador inicial..."
  
  read -p "Digite o nome do administrador: " ADMIN_NAME
  read -p "Digite o email do administrador: " ADMIN_EMAIL
  read -s -p "Digite a senha do administrador: " ADMIN_PASSWORD
  echo ""
  
  # Registrar no log
  echo "Usuário administrador criado:" >> $GO_LIVE_LOG
  echo "Nome: $ADMIN_NAME" >> $GO_LIVE_LOG
  echo "Email: $ADMIN_EMAIL" >> $GO_LIVE_LOG
  echo "===================================" >> $GO_LIVE_LOG
  
  # Criar usuário via API
  ADMIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"nome\":\"$ADMIN_NAME\",\"email\":\"$ADMIN_EMAIL\",\"senha\":\"$ADMIN_PASSWORD\",\"papel\":\"admin\"}")
  
  if echo "$ADMIN_RESPONSE" | grep -q "error"; then
    echo "AVISO: Não foi possível criar o usuário administrador via API."
    echo "Erro: $(echo $ADMIN_RESPONSE | grep -o '"error":"[^"]*' | sed 's/"error":"//')"
    echo "Você precisará criar o administrador manualmente após o go-live."
  else
    echo "Usuário administrador criado com sucesso!"
  fi
fi

# Configurar página de manutenção (opcional)
echo "Deseja configurar uma página de manutenção para uso futuro? (s/n)"
read SETUP_MAINTENANCE

if [ "$SETUP_MAINTENANCE" = "s" ]; then
  echo "Configurando página de manutenção..."
  
  # Criar diretório de manutenção
  mkdir -p maintenance
  
  # Criar página de manutenção
  cat > maintenance/index.html << EOF
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Em Manutenção - Editor IA JurisSaaS</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f3f4f6;
            color: #1f2937;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            padding: 20px;
            text-align: center;
        }
        .maintenance-container {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 40px;
            max-width: 600px;
        }
        h1 {
            color: #4f46e5;
            margin-bottom: 20px;
        }
        p {
            line-height: 1.6;
            margin-bottom: 15px;
        }
        .logo {
            margin-bottom: 30px;
            max-width: 200px;
        }
        .status-link {
            margin-top: 30px;
            color: #4f46e5;
            text-decoration: none;
            font-weight: 500;
        }
        .status-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="maintenance-container">
        <img src="logo.png" alt="Editor IA JurisSaaS Logo" class="logo">
        <h1>Sistema em Manutenção</h1>
        <p>Estamos realizando uma manutenção programada para melhorar sua experiência.</p>
        <p>O Editor IA JurisSaaS estará de volta em breve, com melhorias e novos recursos.</p>
        <p>Agradecemos sua compreensão e paciência.</p>
        <p><strong>Horário previsto para retorno:</strong> <span id="return-time">Em breve</span></p>
        <a href="#" class="status-link">Verificar status da manutenção</a>
    </div>
</body>
</html>
EOF

  echo "Página de manutenção criada em: maintenance/index.html"
  echo "Para ativar a manutenção, use o comando:"
  echo "  mv maintenance/* /var/www/jurissaas/frontend/build/"
  echo "Para desativar, faça um novo deploy do frontend."
fi

# Backup final pré-go-live
echo "Realizando backup final pré-go-live..."
if [ -f "/usr/local/bin/backup-jurissaas.sh" ] && [ -x "/usr/local/bin/backup-jurissaas.sh" ]; then
  sudo /usr/local/bin/backup-jurissaas.sh
  echo "Backup final realizado com sucesso!"
else
  echo "AVISO: Script de backup não encontrado ou não executável."
  echo "Realize um backup manual do banco de dados antes de prosseguir."
fi

# Confirmação final
echo ""
echo "===================================="
echo "CONFIRMAÇÃO FINAL DE GO-LIVE"
echo "===================================="
echo "O sistema foi validado e está pronto para ser liberado aos usuários."
echo "URL: $BASE_URL"
echo ""
echo "Ao confirmar, você está declarando que:"
echo "1. Todos os testes foram concluídos com sucesso"
echo "2. O sistema está estável e pronto para uso"
echo "3. Backups estão configurados e funcionando"
echo "4. Monitoramento está ativo e configurado"
echo ""
echo "Deseja confirmar o go-live e liberar o sistema para os usuários? (s/n)"
read CONFIRM_GO_LIVE

if [ "$CONFIRM_GO_LIVE" = "s" ]; then
  echo "GO-LIVE CONFIRMADO!" | tee -a $GO_LIVE_LOG
  echo "Data e hora: $(date)" | tee -a $GO_LIVE_LOG
  echo ""
  echo "O Editor IA JurisSaaS está oficialmente em produção!"
  echo "URL de acesso: $BASE_URL"
  echo ""
  echo "Relatório de go-live salvo em: $GO_LIVE_LOG"
else
  echo "Go-live cancelado pelo usuário."
  echo "Execute este script novamente quando estiver pronto para liberar o sistema."
  exit 0
fi

# Registrar informações finais
echo "===================================" >> $GO_LIVE_LOG
echo "INFORMAÇÕES DO AMBIENTE" >> $GO_LIVE_LOG
echo "===================================" >> $GO_LIVE_LOG
echo "Sistema operacional: $(uname -a)" >> $GO_LIVE_LOG
echo "Versão do Python: $(python3 --version 2>&1)" >> $GO_LIVE_LOG
echo "Versão do Node.js: $(node --version 2>&1)" >> $GO_LIVE_LOG
echo "Versão do Nginx: $(nginx -v 2>&1)" >> $GO_LIVE_LOG
echo "Versão do MySQL: $(mysql --version 2>&1)" >> $GO_LIVE_LOG
echo "===================================" >> $GO_LIVE_LOG

echo ""
echo "Parabéns! O Editor IA JurisSaaS está oficialmente em produção!"
echo "Mantenha o monitoramento ativo nas próximas 24 horas para garantir estabilidade."
