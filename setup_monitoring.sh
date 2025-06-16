#!/bin/bash

# Script de configuração de monitoramento e logs para o Editor IA JurisSaaS
# Este script configura ferramentas básicas de monitoramento e centralização de logs

echo "Iniciando configuração de monitoramento e logs para o Editor IA JurisSaaS..."

# Verificar se está sendo executado como root
if [ "$EUID" -ne 0 ]; then
  echo "Este script deve ser executado como root (sudo)."
  exit 1
fi

# Solicitar informações do ambiente
read -p "Digite o caminho para o diretório da aplicação [/var/www/jurissaas]: " APP_DIR
APP_DIR=${APP_DIR:-/var/www/jurissaas}

if [ ! -d "$APP_DIR" ]; then
  echo "Erro: Diretório da aplicação $APP_DIR não encontrado."
  echo "Execute primeiro o script setup_production.sh para configurar o ambiente."
  exit 1
fi

# Criar diretório de logs
echo "Criando diretório de logs..."
mkdir -p /var/log/jurissaas
chown www-data:www-data /var/log/jurissaas

# Configurar rotação de logs
echo "Configurando rotação de logs..."
cat > /etc/logrotate.d/jurissaas << EOF
/var/log/jurissaas/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload jurissaas-backend >/dev/null 2>&1 || true
    endscript
}
EOF

# Instalar ferramentas de monitoramento
echo "Instalando ferramentas de monitoramento..."
apt update
apt install -y prometheus prometheus-node-exporter grafana

# Configurar Prometheus
echo "Configurando Prometheus..."
cat > /etc/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      # - alertmanager:9093

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
    - targets: ['localhost:9090']

  - job_name: 'node_exporter'
    static_configs:
    - targets: ['localhost:9100']

  - job_name: 'jurissaas_backend'
    metrics_path: '/metrics'
    static_configs:
    - targets: ['localhost:5000']
EOF

# Reiniciar Prometheus
echo "Reiniciando Prometheus..."
systemctl restart prometheus
systemctl enable prometheus

# Configurar Grafana
echo "Configurando Grafana..."
systemctl restart grafana-server
systemctl enable grafana-server

# Criar script de monitoramento personalizado
echo "Criando script de monitoramento personalizado..."
cat > /usr/local/bin/jurissaas-monitor.sh << EOF
#!/bin/bash

# Script de monitoramento para o Editor IA JurisSaaS
# Verifica o status dos serviços e envia alertas se necessário

# Verificar backend
if ! systemctl is-active --quiet jurissaas-backend; then
  echo "[ALERTA] Serviço jurissaas-backend não está em execução!" | tee -a /var/log/jurissaas/monitor.log
  # Tentar reiniciar
  systemctl restart jurissaas-backend
  sleep 5
  if ! systemctl is-active --quiet jurissaas-backend; then
    echo "[CRÍTICO] Falha ao reiniciar jurissaas-backend!" | tee -a /var/log/jurissaas/monitor.log
    # Aqui você pode adicionar código para enviar e-mail ou SMS de alerta
  fi
fi

# Verificar Nginx
if ! systemctl is-active --quiet nginx; then
  echo "[ALERTA] Serviço Nginx não está em execução!" | tee -a /var/log/jurissaas/monitor.log
  # Tentar reiniciar
  systemctl restart nginx
  sleep 5
  if ! systemctl is-active --quiet nginx; then
    echo "[CRÍTICO] Falha ao reiniciar Nginx!" | tee -a /var/log/jurissaas/monitor.log
    # Aqui você pode adicionar código para enviar e-mail ou SMS de alerta
  fi
fi

# Verificar MySQL
if ! systemctl is-active --quiet mysql; then
  echo "[ALERTA] Serviço MySQL não está em execução!" | tee -a /var/log/jurissaas/monitor.log
  # Tentar reiniciar
  systemctl restart mysql
  sleep 5
  if ! systemctl is-active --quiet mysql; then
    echo "[CRÍTICO] Falha ao reiniciar MySQL!" | tee -a /var/log/jurissaas/monitor.log
    # Aqui você pode adicionar código para enviar e-mail ou SMS de alerta
  fi
fi

# Verificar uso de disco
DISK_USAGE=\$(df -h / | awk 'NR==2 {print \$5}' | sed 's/%//')
if [ \$DISK_USAGE -gt 90 ]; then
  echo "[ALERTA] Uso de disco acima de 90%: \$DISK_USAGE%" | tee -a /var/log/jurissaas/monitor.log
  # Aqui você pode adicionar código para enviar e-mail ou SMS de alerta
fi

# Verificar uso de memória
MEM_AVAILABLE=\$(free -m | awk 'NR==2 {print \$7}')
if [ \$MEM_AVAILABLE -lt 100 ]; then
  echo "[ALERTA] Memória disponível abaixo de 100MB: \$MEM_AVAILABLE MB" | tee -a /var/log/jurissaas/monitor.log
  # Aqui você pode adicionar código para enviar e-mail ou SMS de alerta
fi

# Verificar certificado SSL
DOMAIN=\$(grep server_name /etc/nginx/sites-enabled/* | head -1 | awk '{print \$2}' | sed 's/;//')
if [ ! -z "\$DOMAIN" ]; then
  SSL_EXPIRY=\$(openssl s_client -connect \$DOMAIN:443 -servername \$DOMAIN 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
  SSL_EXPIRY_EPOCH=\$(date -d "\$SSL_EXPIRY" +%s)
  CURRENT_EPOCH=\$(date +%s)
  DAYS_LEFT=\$(( (\$SSL_EXPIRY_EPOCH - \$CURRENT_EPOCH) / 86400 ))
  
  if [ \$DAYS_LEFT -lt 15 ]; then
    echo "[ALERTA] Certificado SSL para \$DOMAIN expira em \$DAYS_LEFT dias!" | tee -a /var/log/jurissaas/monitor.log
    # Aqui você pode adicionar código para enviar e-mail ou SMS de alerta
  fi
fi

# Verificar API OpenAI
API_KEY=\$(grep OPENAI_API_KEY $APP_DIR/backend/.env | cut -d= -f2)
if [ ! -z "\$API_KEY" ]; then
  API_STATUS=\$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer \$API_KEY" https://api.openai.com/v1/models)
  if [ "\$API_STATUS" != "200" ]; then
    echo "[ALERTA] API OpenAI não está respondendo corretamente (status \$API_STATUS)!" | tee -a /var/log/jurissaas/monitor.log
    # Aqui você pode adicionar código para enviar e-mail ou SMS de alerta
  fi
fi

echo "Monitoramento concluído em \$(date)" >> /var/log/jurissaas/monitor.log
EOF

chmod +x /usr/local/bin/jurissaas-monitor.sh

# Configurar cron job para executar o script de monitoramento a cada 5 minutos
echo "Configurando cron job para monitoramento..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/jurissaas-monitor.sh") | crontab -

# Configurar log centralizado para a aplicação
echo "Configurando log centralizado para a aplicação..."
cat > $APP_DIR/backend/logging_config.py << EOF
import logging
import os
from logging.handlers import RotatingFileHandler

def configure_logging(app):
    if not os.path.exists('/var/log/jurissaas'):
        os.makedirs('/var/log/jurissaas')
    
    file_handler = RotatingFileHandler('/var/log/jurissaas/application.log', maxBytes=10485760, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('JurisSaaS Editor IA startup')
    
    return app
EOF

# Atualizar arquivo main.py para incluir configuração de logging
echo "Atualizando arquivo main.py para incluir configuração de logging..."
if grep -q "configure_logging" $APP_DIR/backend/src/main.py; then
  echo "Configuração de logging já existe no arquivo main.py"
else
  # Fazer backup do arquivo original
  cp $APP_DIR/backend/src/main.py $APP_DIR/backend/src/main.py.bak
  
  # Inserir importação e configuração de logging
  sed -i '1s/^/from logging_config import configure_logging\n/' $APP_DIR/backend/src/main.py
  sed -i '/app = Flask/a app = configure_logging(app)' $APP_DIR/backend/src/main.py
fi

echo "Configuração de monitoramento e logs concluída com sucesso!"
echo ""
echo "Serviços configurados:"
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000 (usuário: admin, senha inicial: admin)"
echo "- Logs centralizados: /var/log/jurissaas/"
echo ""
echo "Script de monitoramento: /usr/local/bin/jurissaas-monitor.sh"
echo "Executado a cada 5 minutos via cron"
echo ""
echo "Para visualizar os logs da aplicação:"
echo "  tail -f /var/log/jurissaas/application.log"
echo ""
echo "Para visualizar os logs de monitoramento:"
echo "  tail -f /var/log/jurissaas/monitor.log"
