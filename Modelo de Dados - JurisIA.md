# Modelo de Dados - JurisSaaS

Este documento detalha o modelo de dados relacional da plataforma JurisSaaS, incluindo entidades, relacionamentos, campos e restrições.

## Entidades Principais

### 1. Usuário (User)

Armazena informações dos usuários da plataforma.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| nome | VARCHAR(100) | Nome completo | NOT NULL |
| email | VARCHAR(100) | E-mail para login | UNIQUE, NOT NULL |
| senha_hash | VARCHAR(255) | Hash da senha | NOT NULL |
| papel | ENUM | Papel do usuário (Admin, Gestor, Advogado, Colaborador) | NOT NULL, DEFAULT 'Colaborador' |
| foto_url | VARCHAR(255) | URL da foto de perfil | NULL |
| preferencias_notificacao | JSON | Configurações de notificação | NULL |
| data_criacao | DATETIME | Data de criação do registro | DEFAULT CURRENT_TIMESTAMP |
| ultimo_acesso | DATETIME | Data do último acesso | NULL |
| status | ENUM | Status do usuário (Ativo, Inativo, Bloqueado) | DEFAULT 'Ativo' |
| token_refresh | VARCHAR(255) | Token para renovação de sessão | NULL |
| mfa_ativo | BOOLEAN | Se autenticação multifator está ativa | DEFAULT FALSE |
| mfa_secret | VARCHAR(255) | Segredo para autenticação multifator | NULL |

### 2. Cliente (Client)

Armazena informações dos clientes do escritório.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| nome | VARCHAR(100) | Nome do cliente | NOT NULL |
| tipo | ENUM | Tipo (PF, PJ) | NOT NULL |
| documento | VARCHAR(20) | CPF ou CNPJ | UNIQUE, NOT NULL |
| email | VARCHAR(100) | E-mail principal | NULL |
| telefone | VARCHAR(20) | Telefone principal | NULL |
| endereco | VARCHAR(255) | Endereço completo | NULL |
| data_cadastro | DATETIME | Data de cadastro | DEFAULT CURRENT_TIMESTAMP |
| status | ENUM | Status (Ativo, Inativo) | DEFAULT 'Ativo' |
| observacoes | TEXT | Observações gerais | NULL |

### 3. Processo (Process)

Armazena informações dos processos jurídicos.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| numero | VARCHAR(25) | Número do processo | UNIQUE, NOT NULL |
| cliente_id | INT | Cliente relacionado | FK (Client.id) |
| tribunal | VARCHAR(50) | Tribunal onde tramita | NOT NULL |
| vara | VARCHAR(100) | Vara ou seção | NULL |
| comarca | VARCHAR(100) | Comarca | NULL |
| area | VARCHAR(50) | Área do direito | NOT NULL |
| valor_causa | DECIMAL(15,2) | Valor da causa | NULL |
| data_distribuicao | DATE | Data de distribuição | NULL |
| status | ENUM | Status do processo | DEFAULT 'Ativo' |
| parte_contraria | VARCHAR(100) | Nome da parte contrária | NULL |
| descricao | TEXT | Descrição do processo | NULL |

### 4. Quadro Kanban (KanbanBoard)

Armazena informações dos quadros Kanban.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| nome | VARCHAR(100) | Nome do quadro | NOT NULL |
| cliente_id | INT | Cliente relacionado | FK (Client.id), NULL |
| processo_id | INT | Processo relacionado | FK (Process.id), NULL |
| area | VARCHAR(50) | Área do direito | NULL |
| data_criacao | DATETIME | Data de criação | DEFAULT CURRENT_TIMESTAMP |
| criado_por | INT | Usuário que criou | FK (User.id) |
| status | ENUM | Status (Ativo, Arquivado) | DEFAULT 'Ativo' |

### 5. Lista Kanban (KanbanList)

Armazena informações das listas dentro dos quadros Kanban.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| quadro_id | INT | Quadro relacionado | FK (KanbanBoard.id) |
| nome | VARCHAR(50) | Nome da lista | NOT NULL |
| ordem | INT | Ordem de exibição | NOT NULL |
| cor | VARCHAR(7) | Cor da lista (hex) | DEFAULT '#FFFFFF' |

### 6. Cartão/Tarefa (KanbanCard)

Armazena informações dos cartões/tarefas dentro das listas Kanban.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| lista_id | INT | Lista relacionada | FK (KanbanList.id) |
| titulo | VARCHAR(100) | Título do cartão | NOT NULL |
| descricao | TEXT | Descrição detalhada | NULL |
| processo_id | INT | Processo relacionado | FK (Process.id), NULL |
| responsavel_id | INT | Usuário responsável | FK (User.id), NULL |
| data_limite | DATETIME | Prazo final | NULL |
| prioridade | ENUM | Prioridade (Baixa, Média, Alta, Urgente) | DEFAULT 'Média' |
| status | ENUM | Status (Pendente, Em Andamento, Concluído) | DEFAULT 'Pendente' |
| ordem | INT | Ordem na lista | NOT NULL |
| criado_por | INT | Usuário que criou | FK (User.id) |
| criado_em | DATETIME | Data de criação | DEFAULT CURRENT_TIMESTAMP |
| atualizado_em | DATETIME | Data de atualização | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP |
| origem | ENUM | Origem (Manual, Publicação, Automático) | DEFAULT 'Manual' |

### 7. Checklist (ChecklistItem)

Armazena itens de checklist dos cartões.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| cartao_id | INT | Cartão relacionado | FK (KanbanCard.id) |
| descricao | VARCHAR(255) | Descrição do item | NOT NULL |
| concluido | BOOLEAN | Se está concluído | DEFAULT FALSE |
| ordem | INT | Ordem de exibição | NOT NULL |

### 8. Etiqueta (Tag)

Armazena etiquetas para categorização.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| nome | VARCHAR(50) | Nome da etiqueta | NOT NULL |
| cor | VARCHAR(7) | Cor da etiqueta (hex) | DEFAULT '#CCCCCC' |

### 9. Etiquetas do Cartão (CardTag)

Tabela de relacionamento entre cartões e etiquetas.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| cartao_id | INT | Cartão relacionado | PK, FK (KanbanCard.id) |
| etiqueta_id | INT | Etiqueta relacionada | PK, FK (Tag.id) |

### 10. Publicação (Publication)

Armazena publicações capturadas dos tribunais.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| processo_id | INT | Processo relacionado | FK (Process.id) |
| tribunal | VARCHAR(50) | Tribunal de origem | NOT NULL |
| data_publicacao | DATE | Data da publicação | NOT NULL |
| texto | TEXT | Texto da publicação | NOT NULL |
| texto_ocr | TEXT | Texto extraído por OCR | NULL |
| status_leitura | ENUM | Status (Não Lida, Lida, Processada) | DEFAULT 'Não Lida' |
| data_captura | DATETIME | Data de captura | DEFAULT CURRENT_TIMESTAMP |
| tipo_andamento | VARCHAR(100) | Tipo de andamento identificado | NULL |
| prazo_identificado | INT | Prazo em dias identificado | NULL |
| termo_inicial | DATE | Data inicial do prazo | NULL |

### 11. Memória Operacional (Wiki)

Armazena itens da wiki interna.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| titulo | VARCHAR(100) | Título do item | NOT NULL |
| categoria | VARCHAR(50) | Categoria | NOT NULL |
| texto | TEXT | Conteúdo | NOT NULL |
| autor_id | INT | Usuário autor | FK (User.id) |
| data_criacao | DATETIME | Data de criação | DEFAULT CURRENT_TIMESTAMP |
| data_atualizacao | DATETIME | Data de atualização | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP |
| versao | INT | Versão do documento | DEFAULT 1 |
| status | ENUM | Status (Rascunho, Publicado, Obsoleto) | DEFAULT 'Rascunho' |

### 12. Tags da Wiki (WikiTag)

Tabela de relacionamento entre itens wiki e tags.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| wiki_id | INT | Item wiki relacionado | PK, FK (Wiki.id) |
| tag | VARCHAR(50) | Tag | PK |

### 13. Processos da Wiki (WikiProcess)

Tabela de relacionamento entre itens wiki e processos.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| wiki_id | INT | Item wiki relacionado | PK, FK (Wiki.id) |
| processo_id | INT | Processo relacionado | PK, FK (Process.id) |

### 14. Comentário (Comment)

Armazena comentários em cartões e itens wiki.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| tipo_entidade | ENUM | Tipo (Cartão, Wiki) | NOT NULL |
| entidade_id | INT | ID da entidade | NOT NULL |
| usuario_id | INT | Usuário autor | FK (User.id) |
| texto | TEXT | Texto do comentário | NOT NULL |
| data_criacao | DATETIME | Data de criação | DEFAULT CURRENT_TIMESTAMP |

### 15. Anexo (Attachment)

Armazena anexos de cartões e processos.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| tipo_entidade | ENUM | Tipo (Cartão, Processo) | NOT NULL |
| entidade_id | INT | ID da entidade | NOT NULL |
| nome | VARCHAR(100) | Nome do arquivo | NOT NULL |
| tipo_arquivo | VARCHAR(50) | Tipo MIME | NOT NULL |
| url | VARCHAR(255) | URL do arquivo | NOT NULL |
| tamanho | INT | Tamanho em bytes | NOT NULL |
| usuario_id | INT | Usuário que anexou | FK (User.id) |
| data_upload | DATETIME | Data de upload | DEFAULT CURRENT_TIMESTAMP |

### 16. Notificação (Notification)

Armazena notificações para usuários.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| usuario_id | INT | Usuário destinatário | FK (User.id) |
| tipo | ENUM | Tipo de notificação | NOT NULL |
| titulo | VARCHAR(100) | Título da notificação | NOT NULL |
| mensagem | TEXT | Mensagem detalhada | NOT NULL |
| link | VARCHAR(255) | Link relacionado | NULL |
| lida | BOOLEAN | Se foi lida | DEFAULT FALSE |
| data_criacao | DATETIME | Data de criação | DEFAULT CURRENT_TIMESTAMP |
| data_leitura | DATETIME | Data de leitura | NULL |

### 17. Histórico de Cartão (CardHistory)

Armazena histórico de alterações em cartões.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| cartao_id | INT | Cartão relacionado | FK (KanbanCard.id) |
| usuario_id | INT | Usuário que alterou | FK (User.id) |
| tipo_alteracao | ENUM | Tipo de alteração | NOT NULL |
| valor_anterior | TEXT | Valor antes da alteração | NULL |
| valor_novo | TEXT | Valor após alteração | NULL |
| data_alteracao | DATETIME | Data da alteração | DEFAULT CURRENT_TIMESTAMP |

### 18. Modelo de Petição (PetitionTemplate)

Armazena modelos de petições para o editor IA.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| nome | VARCHAR(100) | Nome do modelo | NOT NULL |
| categoria | VARCHAR(50) | Categoria | NOT NULL |
| conteudo | TEXT | Conteúdo do modelo | NOT NULL |
| variaveis | JSON | Variáveis dinâmicas | NULL |
| usuario_id | INT | Usuário que criou | FK (User.id) |
| data_criacao | DATETIME | Data de criação | DEFAULT CURRENT_TIMESTAMP |
| data_atualizacao | DATETIME | Data de atualização | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP |
| status | ENUM | Status (Ativo, Inativo) | DEFAULT 'Ativo' |

### 19. Petição (Petition)

Armazena petições geradas pelo editor IA.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| titulo | VARCHAR(100) | Título da petição | NOT NULL |
| conteudo | TEXT | Conteúdo da petição | NOT NULL |
| modelo_id | INT | Modelo utilizado | FK (PetitionTemplate.id), NULL |
| processo_id | INT | Processo relacionado | FK (Process.id), NULL |
| cartao_id | INT | Cartão relacionado | FK (KanbanCard.id), NULL |
| usuario_id | INT | Usuário que criou | FK (User.id) |
| data_criacao | DATETIME | Data de criação | DEFAULT CURRENT_TIMESTAMP |
| data_atualizacao | DATETIME | Data de atualização | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP |
| versao | INT | Versão do documento | DEFAULT 1 |
| status | ENUM | Status (Rascunho, Finalizada) | DEFAULT 'Rascunho' |

### 20. Assinatura (Subscription)

Armazena informações de assinaturas e pagamentos.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| usuario_id | INT | Usuário assinante | FK (User.id) |
| plano | ENUM | Plano (Editor IA, Plataforma Total) | NOT NULL |
| valor | DECIMAL(10,2) | Valor da assinatura | NOT NULL |
| periodicidade | ENUM | Periodicidade (Mensal, Anual) | DEFAULT 'Mensal' |
| data_inicio | DATE | Data de início | NOT NULL |
| data_proximo_pagamento | DATE | Data do próximo pagamento | NOT NULL |
| status | ENUM | Status (Ativa, Inadimplente, Cancelada) | DEFAULT 'Ativa' |
| metodo_pagamento | VARCHAR(50) | Método de pagamento | NOT NULL |
| info_pagamento | JSON | Informações de pagamento | NULL |
| limite_documentos | INT | Limite de documentos (plano Editor IA) | NULL |
| documentos_utilizados | INT | Documentos utilizados no ciclo atual | DEFAULT 0 |
| data_atualizacao | DATETIME | Data de atualização | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP |

### 21. Pagamento (Payment)

Armazena histórico de pagamentos.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| assinatura_id | INT | Assinatura relacionada | FK (Subscription.id) |
| valor | DECIMAL(10,2) | Valor pago | NOT NULL |
| data_pagamento | DATETIME | Data do pagamento | NOT NULL |
| status | ENUM | Status (Pendente, Aprovado, Recusado, Estornado) | DEFAULT 'Pendente' |
| gateway | VARCHAR(50) | Gateway de pagamento | NOT NULL |
| transacao_id | VARCHAR(100) | ID da transação no gateway | NULL |
| comprovante_url | VARCHAR(255) | URL do comprovante | NULL |

### 22. Log de Auditoria (AuditLog)

Armazena logs de auditoria para conformidade com LGPD.

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| id | INT | Identificador único | PK, AUTO_INCREMENT |
| usuario_id | INT | Usuário que realizou a ação | FK (User.id), NULL |
| ip | VARCHAR(45) | Endereço IP | NOT NULL |
| acao | VARCHAR(50) | Ação realizada | NOT NULL |
| entidade | VARCHAR(50) | Entidade afetada | NOT NULL |
| entidade_id | INT | ID da entidade | NULL |
| detalhes | TEXT | Detalhes da ação | NULL |
| data | DATETIME | Data da ação | DEFAULT CURRENT_TIMESTAMP |

## Relacionamentos

1. Um **Usuário** pode ter muitas **Notificações**
2. Um **Cliente** pode ter muitos **Processos**
3. Um **Processo** pode ter muitas **Publicações**
4. Um **Processo** pode estar vinculado a muitos **Quadros Kanban**
5. Um **Quadro Kanban** contém muitas **Listas Kanban**
6. Uma **Lista Kanban** contém muitos **Cartões/Tarefas**
7. Um **Cartão/Tarefa** pode ter muitos **Itens de Checklist**
8. Um **Cartão/Tarefa** pode ter muitas **Etiquetas** (via CardTag)
9. Um **Cartão/Tarefa** pode ter muitos **Comentários**
10. Um **Cartão/Tarefa** pode ter muitos **Anexos**
11. Um **Cartão/Tarefa** pode ter muitos registros de **Histórico**
12. Um **Item Wiki** pode ter muitas **Tags** (via WikiTag)
13. Um **Item Wiki** pode estar vinculado a muitos **Processos** (via WikiProcess)
14. Um **Item Wiki** pode ter muitos **Comentários**
15. Um **Usuário** pode ter uma **Assinatura** ativa
16. Uma **Assinatura** pode ter muitos **Pagamentos**

## Índices

Para otimizar o desempenho, os seguintes índices serão criados:

1. Índice em `User.email` para buscas rápidas no login
2. Índice em `Process.numero` para buscas por número de processo
3. Índice em `Process.cliente_id` para listar processos por cliente
4. Índice em `KanbanCard.lista_id` para listar cartões por lista
5. Índice em `KanbanCard.responsavel_id` para listar tarefas por responsável
6. Índice em `KanbanCard.data_limite` para buscar tarefas por prazo
7. Índice em `Publication.processo_id` para listar publicações por processo
8. Índice em `Publication.data_publicacao` para buscar publicações por data
9. Índice em `Wiki.categoria` para buscar itens wiki por categoria
10. Índice em `Notification.usuario_id` para listar notificações por usuário
11. Índice em `Subscription.usuario_id` para buscar assinatura por usuário
12. Índice em `AuditLog.usuario_id` para buscar logs por usuário

## Constraints e Validações

1. Validação de formato de e-mail em `User.email`
2. Validação de formato de CPF/CNPJ em `Client.documento`
3. Validação de formato de número de processo em `Process.numero`
4. Constraint para garantir que `KanbanCard.ordem` seja único dentro de uma lista
5. Constraint para garantir que `KanbanList.ordem` seja único dentro de um quadro
6. Validação para garantir que `Subscription.limite_documentos` seja preenchido apenas para plano "Editor IA"
7. Validação para garantir que `Subscription.documentos_utilizados` não ultrapasse `limite_documentos`

## Considerações de Segurança

1. Senhas armazenadas apenas como hash (bcrypt)
2. Dados sensíveis criptografados no banco
3. Logs de auditoria para todas as operações críticas
4. Separação clara de dados por usuário/cliente para evitar acesso indevido
