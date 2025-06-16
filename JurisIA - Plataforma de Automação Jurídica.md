# JurisIA - Plataforma de Automação Jurídica

Plataforma SaaS web jurídica voltada para escritórios de advocacia e profissionais do direito, com foco em automação da rotina jurídica, gestão visual de tarefas e geração de documentos com IA.

## Visão Geral

A plataforma JurisIA automatiza a rotina jurídica através de:

- Captação automática de publicações processuais
- Sistema visual de gestão de tarefas (Kanban)
- Editor de petições com IA que aprende o estilo do usuário
- Memória operacional (Wiki interna) para registro de teses e modelos
- Dashboard com relatórios de produtividade
- Sistema completo de gestão de assinaturas e pagamentos

## Arquitetura

O projeto utiliza uma arquitetura moderna e escalável:

- **Backend**: Flask (Python) com API RESTful
- **Frontend**: React com Typescript
- **Banco de Dados**: MySQL (relacional)
- **Autenticação**: JWT com refresh tokens
- **Segurança**: Conformidade com LGPD, logs de auditoria
- **Infraestrutura**: CI/CD, versionamento, deploy controlado

## Estrutura do Projeto

```
juris-saas/
├── backend/               # API Flask
│   ├── venv/              # Ambiente virtual Python
│   ├── src/               # Código-fonte
│   │   ├── main.py        # Ponto de entrada
│   │   ├── models/        # Modelos de dados
│   │   ├── routes/        # Rotas da API
│   │   ├── services/      # Serviços de negócio
│   │   ├── utils/         # Utilitários
│   │   └── ai/            # Módulos de IA
│   └── requirements.txt   # Dependências
│
├── frontend/              # Aplicação React
│   ├── public/            # Arquivos estáticos
│   ├── src/               # Código-fonte
│   │   ├── components/    # Componentes React
│   │   ├── pages/         # Páginas da aplicação
│   │   ├── services/      # Serviços de API
│   │   ├── hooks/         # React hooks
│   │   ├── context/       # Contextos React
│   │   └── styles/        # Estilos (Tailwind)
│   └── package.json       # Dependências
│
├── docs/                  # Documentação
│   ├── architecture/      # Documentação de arquitetura
│   ├── api/               # Documentação da API
│   └── user/              # Documentação de usuário
│
└── scripts/               # Scripts de automação
    ├── setup.sh           # Configuração inicial
    ├── deploy.sh          # Script de deploy
    └── seed.py            # Geração de dados de teste
```

## Módulos Principais

1. **Autenticação e Permissões**
   - Login/registro seguro
   - Controle de papéis (Admin, Gestor, Advogado, Colaborador)
   - Permissões granulares por recurso

2. **Kanban Jurídico**
   - Quadros personalizáveis
   - Listas customizáveis
   - Cartões/tarefas com drag-and-drop

3. **Automação de Publicações**
   - Scraping de portais jurídicos
   - Parser de texto com NLP
   - Geração automática de tarefas

4. **Memória Operacional (Wiki)**
   - Cadastro de teses e modelos
   - Busca avançada
   - Versionamento de conteúdo

5. **Editor de Petições com IA**
   - Aprendizado do estilo do usuário
   - Geração de rascunhos automáticos
   - Editor WYSIWYG

6. **Notificações e Alertas**
   - Notificações push, e-mail
   - Personalização de alertas
   - Log de envio e leitura

7. **Dashboard e Relatórios**
   - Visão geral de prazos e tarefas
   - Relatórios de produtividade
   - Exportação em diversos formatos

8. **Checkout e Pagamento**
   - Planos e assinaturas
   - Processamento de pagamentos recorrentes
   - Gestão de assinaturas

## Planos de Assinatura

1. **Editor IA (Plano de Entrada)**
   - Acesso apenas ao editor de petições com IA
   - Limite de 15 documentos/mês
   - Preço reduzido

2. **Plataforma Total**
   - Acesso a todos os módulos
   - Uso ilimitado
   - Suporte prioritário

## Conformidade e Segurança

- Conformidade com LGPD
- Logs de auditoria
- Monitoramento de segurança
- Backup automático

## Desenvolvimento

Este projeto segue as melhores práticas de desenvolvimento de software, incluindo:

- Versionamento com Git
- CI/CD para integração e deploy contínuos
- Testes automatizados
- Documentação abrangente
