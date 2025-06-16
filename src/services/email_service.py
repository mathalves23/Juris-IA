import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.config import Config

class EmailService:
    """Serviço de envio de emails com múltiplos provedores"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.from_email = Config.FROM_EMAIL
        
        # Configurações SMTP
        self.smtp_server = Config.MAIL_SERVER
        self.smtp_port = Config.MAIL_PORT
        self.smtp_username = Config.MAIL_USERNAME
        self.smtp_password = Config.MAIL_PASSWORD
        self.use_tls = Config.MAIL_USE_TLS
        
        # SendGrid (se disponível)
        self.sendgrid_api_key = Config.SENDGRID_API_KEY
        
    def _get_email_templates(self) -> Dict[str, Dict[str, str]]:
        """Templates de email"""
        base_style = """
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }
            .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px; }
            .content { padding: 20px 0; line-height: 1.6; color: #333; }
            .button { display: inline-block; padding: 12px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }
            .footer { text-align: center; padding: 20px 0; border-top: 1px solid #eee; color: #666; font-size: 12px; }
            .alert { background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 15px 0; color: #856404; }
        </style>
        """
        
        return {
            'password_reset': {
                'subject': f'🔐 {Config.APP_NAME} - Redefinir Senha',
                'html': f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Redefinir Senha - {Config.APP_NAME}</title>
                    {base_style}
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🔐 Redefinir Senha</h1>
                            <p>{Config.APP_NAME} - Plataforma Jurídica Inteligente</p>
                        </div>
                        <div class="content">
                            <p>Olá, <strong>{{{{ user_name }}}}</strong>!</p>
                            
                            <p>Recebemos uma solicitação para redefinir a senha da sua conta no {Config.APP_NAME}.</p>
                            
                            <div class="alert">
                                <strong>⚠️ Atenção:</strong> Se você não solicitou esta redefinição, ignore este email. Sua senha permanecerá inalterada.
                            </div>
                            
                            <p>Para continuar, clique no botão abaixo:</p>
                            
                            <p style="text-align: center;">
                                <a href="{{{{ reset_link }}}}" class="button">🔄 Redefinir Senha</a>
                            </p>
                            
                            <p>Ou copie e cole este link em seu navegador:</p>
                            <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace;">
                                {{{{ reset_link }}}}
                            </p>
                            
                            <p><strong>⏰ Este link expira em {{{{ expiry_time }}}} minutos.</strong></p>
                            
                            <hr>
                            <p><strong>Informações de Segurança:</strong></p>
                            <ul>
                                <li>🕐 Solicitação feita em: {{{{ request_time }}}}</li>
                                <li>🌐 IP: {{{{ ip_address }}}}</li>
                                <li>💻 Dispositivo: {{{{ user_agent }}}}</li>
                            </ul>
                        </div>
                        <div class="footer">
                            <p>© 2024 {Config.COMPANY_NAME} - Todos os direitos reservados</p>
                            <p>📧 Dúvidas? Entre em contato: <a href="mailto:{Config.SUPPORT_EMAIL}">{Config.SUPPORT_EMAIL}</a></p>
                        </div>
                    </div>
                </body>
                </html>
                """
            },
            
            'email_verification': {
                'subject': f'✅ {Config.APP_NAME} - Verificar Email',
                'html': f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Verificar Email - {Config.APP_NAME}</title>
                    {base_style}
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>✅ Verificar Email</h1>
                            <p>{Config.APP_NAME} - Plataforma Jurídica Inteligente</p>
                        </div>
                        <div class="content">
                            <p>Olá, <strong>{{{{ user_name }}}}</strong>!</p>
                            
                            <p>🎉 Bem-vindo ao {Config.APP_NAME}! Para completar seu cadastro, precisamos verificar seu endereço de email.</p>
                            
                            <p style="text-align: center;">
                                <a href="{{{{ verification_link }}}}" class="button">✅ Verificar Email</a>
                            </p>
                            
                            <p>Ou copie e cole este link em seu navegador:</p>
                            <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace;">
                                {{{{ verification_link }}}}
                            </p>
                            
                            <p><strong>⏰ Este link expira em {{{{ expiry_time }}}} horas.</strong></p>
                            
                            <div class="alert">
                                <strong>🚀 Após a verificação, você terá acesso a:</strong>
                                <ul>
                                    <li>🤖 Análise inteligente de contratos com IA</li>
                                    <li>📝 Editor jurídico avançado</li>
                                    <li>📊 Relatórios e estatísticas</li>
                                    <li>💼 Gestão completa de documentos</li>
                                </ul>
                            </div>
                        </div>
                        <div class="footer">
                            <p>© 2024 {Config.COMPANY_NAME} - Todos os direitos reservados</p>
                            <p>📧 Dúvidas? Entre em contato: <a href="mailto:{Config.SUPPORT_EMAIL}">{Config.SUPPORT_EMAIL}</a></p>
                        </div>
                    </div>
                </body>
                </html>
                """
            },
            
            'welcome': {
                'subject': f'🎉 Bem-vindo ao {Config.APP_NAME}!',
                'html': f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Bem-vindo - {Config.APP_NAME}</title>
                    {base_style}
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🎉 Bem-vindo!</h1>
                            <p>{Config.APP_NAME} - Plataforma Jurídica Inteligente</p>
                        </div>
                        <div class="content">
                            <p>Olá, <strong>{{{{ user_name }}}}</strong>!</p>
                            
                            <p>🎊 Parabéns! Sua conta foi verificada com sucesso. Agora você tem acesso completo ao {Config.APP_NAME}.</p>
                            
                            <p style="text-align: center;">
                                <a href="{{{{ dashboard_link }}}}" class="button">🚀 Acessar Plataforma</a>
                            </p>
                            
                            <div class="alert">
                                <strong>🛠️ Próximos passos recomendados:</strong>
                                <ol>
                                    <li>📄 Faça upload do seu primeiro contrato para análise</li>
                                    <li>🎯 Configure suas preferências no perfil</li>
                                    <li>📚 Explore nossos templates jurídicos</li>
                                    <li>🤖 Teste o analisador de contratos com IA</li>
                                </ol>
                            </div>
                            
                            <p>Precisa de ajuda? Nossa equipe está sempre disponível!</p>
                        </div>
                        <div class="footer">
                            <p>© 2024 {Config.COMPANY_NAME} - Todos os direitos reservados</p>
                            <p>📧 Suporte: <a href="mailto:{Config.SUPPORT_EMAIL}">{Config.SUPPORT_EMAIL}</a></p>
                        </div>
                    </div>
                </body>
                </html>
                """
            }
        }
    
    def _send_smtp_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Envia email via SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Adicionar versão texto se não fornecida
            if not text_content:
                # Criar versão texto simples removendo HTML
                import re
                text_content = re.sub('<[^<]+?>', '', html_content)
                text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            # Adicionar conteúdo
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # Conectar e enviar
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
            
            self.logger.info(f"Email SMTP enviado com sucesso para {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email SMTP para {to_email}: {str(e)}")
            return False
    
    def send_email(self, to_email: str, template_name: str, template_vars: Dict[str, Any]) -> bool:
        """Envia email usando template especificado"""
        try:
            templates = self._get_email_templates()
            
            if template_name not in templates:
                self.logger.error(f"Template '{template_name}' não encontrado")
                return False
            
            template = templates[template_name]
            
            # Processar template
            subject = template['subject']
            html_content = template['html']
            
            # Substituir variáveis no template
            for var, value in template_vars.items():
                placeholder = f'{{{{{{{ var }}}}}}}'
                subject = subject.replace(placeholder, str(value))
                html_content = html_content.replace(placeholder, str(value))
            
            # Tentar enviar
            return self._send_smtp_email(to_email, subject, html_content)
            
        except Exception as e:
            self.logger.error(f"Erro geral ao enviar email para {to_email}: {str(e)}")
            return False
    
    def send_password_reset(self, user_email: str, user_name: str, reset_token: str, 
                          ip_address: str = "", user_agent: str = "") -> bool:
        """Envia email de reset de senha"""
        reset_link = f"{Config.FRONTEND_URL}/reset-password?token={reset_token}"
        
        template_vars = {
            'user_name': user_name,
            'reset_link': reset_link,
            'expiry_time': str(Config.PASSWORD_RESET_EXPIRY // 60),  # Em minutos
            'request_time': datetime.now().strftime('%d/%m/%Y às %H:%M'),
            'ip_address': ip_address or 'Não disponível',
            'user_agent': user_agent[:100] + '...' if len(user_agent) > 100 else user_agent or 'Não disponível'
        }
        
        return self.send_email(user_email, 'password_reset', template_vars)
    
    def send_email_verification(self, user_email: str, user_name: str, verification_token: str) -> bool:
        """Envia email de verificação"""
        verification_link = f"{Config.FRONTEND_URL}/verify-email?token={verification_token}"
        
        template_vars = {
            'user_name': user_name,
            'verification_link': verification_link,
            'expiry_time': str(Config.EMAIL_VERIFICATION_EXPIRY // 3600)  # Em horas
        }
        
        return self.send_email(user_email, 'email_verification', template_vars)
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Envia email de boas-vindas após verificação"""
        dashboard_link = Config.FRONTEND_URL
        
        template_vars = {
            'user_name': user_name,
            'dashboard_link': dashboard_link
        }
        
        return self.send_email(user_email, 'welcome', template_vars)
    
    def is_configured(self) -> bool:
        """Verifica se o serviço de email está configurado"""
        return Config.is_email_configured()

# Instância global do serviço
email_service = EmailService() 