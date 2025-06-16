from src.extensions import db
from datetime import datetime
from enum import Enum
import json

class DocumentStatus(Enum):
    RASCUNHO = "rascunho"
    EM_REVISAO = "em_revisao"
    APROVADO = "aprovado"
    FINALIZADO = "finalizado"
    ARQUIVADO = "arquivado"

class DocumentType(Enum):
    TEXTO_SIMPLES = "texto_simples"
    RICH_TEXT = "rich_text"
    MARKDOWN = "markdown"
    JURIDICO = "juridico"

class PermissionType(Enum):
    LEITURA = "leitura"
    COMENTARIO = "comentario"
    EDICAO = "edicao"
    ADMIN = "admin"

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    conteudo = db.Column(db.Text, nullable=False)
    conteudo_delta = db.Column(db.JSON)  # Para Quill.js Delta format
    
    # Tipo e status
    tipo = db.Column(db.Enum(DocumentType), default=DocumentType.RICH_TEXT)
    status = db.Column(db.Enum(DocumentStatus), default=DocumentStatus.RASCUNHO)
    
    # Relacionamentos básicos
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=True)
    
    # Versionamento
    versao = db.Column(db.Integer, default=1)
    versao_principal = db.Column(db.Boolean, default=True)  # Se é a versão principal
    documento_pai_id = db.Column(db.Integer, db.ForeignKey('documents.id'))  # Para versões
    
    # Colaboração e permissões
    colaborativo = db.Column(db.Boolean, default=False)
    publico = db.Column(db.Boolean, default=False)
    
    # Metadados
    tags = db.Column(db.JSON)  # Lista de tags
    palavras_chave = db.Column(db.JSON)  # Palavras-chave extraídas
    tamanho_estimado = db.Column(db.Integer)  # Tamanho em caracteres
    tempo_leitura = db.Column(db.Integer)  # Tempo estimado de leitura em minutos
    
    # Auditoria e rastreamento
    ultima_edicao_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    bloqueado_para_edicao = db.Column(db.Boolean, default=False)
    bloqueado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    bloqueado_em = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', foreign_keys=[user_id], backref='documentos')
    template = db.relationship('Template')
    ultima_edicao_user = db.relationship('User', foreign_keys=[ultima_edicao_user_id])
    bloqueado_por_user = db.relationship('User', foreign_keys=[bloqueado_por_user_id])
    
    # Relacionamentos para colaboração
    colaboradores = db.relationship('DocumentColaborador', back_populates='document', cascade='all, delete-orphan')
    comentarios = db.relationship('DocumentComentario', back_populates='document', cascade='all, delete-orphan')
    historico = db.relationship('DocumentHistorico', back_populates='document', cascade='all, delete-orphan')
    
    def __init__(self, titulo, conteudo, user_id, **kwargs):
        self.titulo = titulo
        self.conteudo = conteudo
        self.user_id = user_id
        self.ultima_edicao_user_id = user_id
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Calcular metadados automaticamente
        self._calcular_metadados()
    
    def _calcular_metadados(self):
        """Calcula metadados do documento"""
        if self.conteudo:
            self.tamanho_estimado = len(self.conteudo)
            # Estima tempo de leitura (200 palavras por minuto)
            palavras = len(self.conteudo.split())
            self.tempo_leitura = max(1, palavras // 200)
    
    def pode_acessar(self, user_id):
        """Verifica se usuário pode acessar o documento"""
        if self.user_id == user_id:
            return True
        
        if self.publico:
            return True
        
        # Verificar colaboradores
        colaborador = DocumentColaborador.query.filter_by(
            document_id=self.id,
            user_id=user_id
        ).first()
        
        return colaborador is not None
    
    def pode_editar(self, user_id):
        """Verifica se usuário pode editar o documento"""
        if self.user_id == user_id:
            return True
        
        if self.bloqueado_para_edicao and self.bloqueado_por_user_id != user_id:
            return False
        
        colaborador = DocumentColaborador.query.filter_by(
            document_id=self.id,
            user_id=user_id
        ).first()
        
        if colaborador:
            return colaborador.permissao in [PermissionType.EDICAO, PermissionType.ADMIN]
        
        return False
    
    def bloquear_para_edicao(self, user_id):
        """Bloqueia documento para edição por usuário específico"""
        if self.pode_editar(user_id):
            self.bloqueado_para_edicao = True
            self.bloqueado_por_user_id = user_id
            self.bloqueado_em = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def desbloquear_edicao(self, user_id):
        """Desbloqueia documento para edição"""
        if self.bloqueado_por_user_id == user_id or self.user_id == user_id:
            self.bloqueado_para_edicao = False
            self.bloqueado_por_user_id = None
            self.bloqueado_em = None
            db.session.commit()
            return True
        return False
    
    def criar_nova_versao(self, user_id, conteudo_novo, comentario=""):
        """Cria nova versão do documento"""
        # Registrar no histórico
        historico = DocumentHistorico(
            document_id=self.id,
            user_id=user_id,
            conteudo_anterior=self.conteudo,
            conteudo_novo=conteudo_novo,
            versao_anterior=self.versao,
            comentario=comentario
        )
        
        # Atualizar documento
        self.conteudo = conteudo_novo
        self.versao += 1
        self.ultima_edicao_user_id = user_id
        self.updated_at = datetime.utcnow()
        self._calcular_metadados()
        
        db.session.add(historico)
        db.session.commit()
        
        return historico
    
    def to_dict(self, user_id=None, incluir_conteudo=True):
        base_dict = {
            'id': self.id,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'tipo': self.tipo.value if self.tipo else None,
            'status': self.status.value if self.status else None,
            'user_id': self.user_id,
            'template_id': self.template_id,
            'versao': self.versao,
            'versao_principal': self.versao_principal,
            'documento_pai_id': self.documento_pai_id,
            'colaborativo': self.colaborativo,
            'publico': self.publico,
            'tags': self.tags or [],
            'palavras_chave': self.palavras_chave or [],
            'tamanho_estimado': self.tamanho_estimado,
            'tempo_leitura': self.tempo_leitura,
            'bloqueado_para_edicao': self.bloqueado_para_edicao,
            'bloqueado_por_user_id': self.bloqueado_por_user_id,
            'bloqueado_em': self.bloqueado_em.isoformat() if self.bloqueado_em else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if incluir_conteudo:
            base_dict['conteudo'] = self.conteudo
            base_dict['conteudo_delta'] = self.conteudo_delta
        
        if user_id:
            base_dict['pode_acessar'] = self.pode_acessar(user_id)
            base_dict['pode_editar'] = self.pode_editar(user_id)
        
        return base_dict

class DocumentColaborador(db.Model):
    __tablename__ = 'document_colaboradores'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permissao = db.Column(db.Enum(PermissionType), default=PermissionType.LEITURA)
    convidado_por = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    document = db.relationship('Document', back_populates='colaboradores')
    user = db.relationship('User', foreign_keys=[user_id])
    convidado_por_user = db.relationship('User', foreign_keys=[convidado_por])
    
    __table_args__ = (db.UniqueConstraint('document_id', 'user_id'),)

class DocumentComentario(db.Model):
    __tablename__ = 'document_comentarios'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comentario = db.Column(db.Text, nullable=False)
    posicao_inicio = db.Column(db.Integer)  # Posição no texto onde inicia o comentário
    posicao_fim = db.Column(db.Integer)     # Posição no texto onde termina o comentário
    resolvido = db.Column(db.Boolean, default=False)
    comentario_pai_id = db.Column(db.Integer, db.ForeignKey('document_comentarios.id'))  # Para respostas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    document = db.relationship('Document', back_populates='comentarios')
    user = db.relationship('User')
    respostas = db.relationship('DocumentComentario', backref=db.backref('comentario_pai', remote_side=[id]))

class DocumentHistorico(db.Model):
    __tablename__ = 'document_historico'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Conteúdo das versões
    conteudo_anterior = db.Column(db.Text)
    conteudo_novo = db.Column(db.Text)
    
    # Metadados da mudança
    versao_anterior = db.Column(db.Integer)
    comentario = db.Column(db.Text)  # Comentário da mudança
    tipo_mudanca = db.Column(db.String(50), default='edicao')  # edicao, revisao, aprovacao
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    document = db.relationship('Document', back_populates='historico')
    user = db.relationship('User')

class DocumentTemplate(db.Model):
    """Associação entre documentos e templates"""
    __tablename__ = 'document_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)
    variaveis_utilizadas = db.Column(db.JSON)  # Valores das variáveis usadas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
