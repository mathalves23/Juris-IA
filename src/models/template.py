from src.extensions import db
from datetime import datetime
from enum import Enum

class TemplateCategory(Enum):
    CONTRATOS = "contratos"
    PETICOES = "peticoes"
    PARECERES = "pareceres"
    PROCURACOES = "procuracoes"
    CARTAS = "cartas"
    ATAS = "atas"
    RECURSOS = "recursos"
    ESTATUTOS = "estatutos"
    OUTROS = "outros"

class TemplateVisibility(Enum):
    PRIVATE = "private"          # Apenas o criador
    TEAM = "team"               # Equipe do usuário
    PUBLIC = "public"           # Todos os usuários
    MARKETPLACE = "marketplace"  # Marketplace público

class Template(db.Model):
    __tablename__ = 'templates'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    conteudo = db.Column(db.Text, nullable=False)
    
    # Categorização e tags
    categoria = db.Column(db.Enum(TemplateCategory), nullable=False, default=TemplateCategory.OUTROS)
    tags = db.Column(db.JSON)  # Lista de tags para busca
    
    # Compartilhamento e visibilidade
    visibilidade = db.Column(db.Enum(TemplateVisibility), default=TemplateVisibility.PRIVATE)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Métricas de uso
    uso_count = db.Column(db.Integer, default=0)
    favoritos_count = db.Column(db.Integer, default=0)
    
    # Metadata adicional
    variaveis = db.Column(db.JSON)  # Variáveis do template para substituição
    preview_image = db.Column(db.String(500))  # URL da imagem de preview
    
    # Versionamento
    versao = db.Column(db.String(10), default="1.0")
    template_parent_id = db.Column(db.Integer, db.ForeignKey('templates.id'))  # Para versões
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    aprovado = db.Column(db.Boolean, default=True)  # Para marketplace
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', backref='templates')
    favoritos = db.relationship('TemplateFavorito', back_populates='template', cascade='all, delete-orphan')
    compartilhamentos = db.relationship('TemplateCompartilhamento', back_populates='template', cascade='all, delete-orphan')
    
    def __init__(self, titulo, conteudo, user_id, categoria=TemplateCategory.OUTROS, **kwargs):
        self.titulo = titulo
        self.conteudo = conteudo
        self.user_id = user_id
        self.categoria = categoria
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def incrementar_uso(self):
        """Incrementa contador de uso"""
        self.uso_count += 1
        db.session.commit()
    
    def pode_acessar(self, user_id):
        """Verifica se usuário pode acessar o template"""
        if self.user_id == user_id:
            return True
        
        if self.visibilidade == TemplateVisibility.PUBLIC:
            return True
        
        if self.visibilidade == TemplateVisibility.MARKETPLACE and self.aprovado:
            return True
        
        # Verificar compartilhamentos específicos
        compartilhamento = TemplateCompartilhamento.query.filter_by(
            template_id=self.id, 
            user_id=user_id
        ).first()
        
        return compartilhamento is not None
    
    def esta_favoritado_por(self, user_id):
        """Verifica se template está favoritado pelo usuário"""
        return TemplateFavorito.query.filter_by(
            template_id=self.id, 
            user_id=user_id
        ).first() is not None
    
    def to_dict(self, user_id=None):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'conteudo': self.conteudo,
            'categoria': self.categoria.value if self.categoria else None,
            'tags': self.tags or [],
            'visibilidade': self.visibilidade.value if self.visibilidade else None,
            'user_id': self.user_id,
            'uso_count': self.uso_count,
            'favoritos_count': self.favoritos_count,
            'variaveis': self.variaveis or [],
            'preview_image': self.preview_image,
            'versao': self.versao,
            'template_parent_id': self.template_parent_id,
            'ativo': self.ativo,
            'aprovado': self.aprovado,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'favoritado': self.esta_favoritado_por(user_id) if user_id else False,
            'pode_editar': self.user_id == user_id if user_id else False
        }

class TemplateFavorito(db.Model):
    __tablename__ = 'template_favoritos'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    template = db.relationship('Template', back_populates='favoritos')
    user = db.relationship('User')
    
    __table_args__ = (db.UniqueConstraint('template_id', 'user_id'),)

class TemplateCompartilhamento(db.Model):
    __tablename__ = 'template_compartilhamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    compartilhado_por = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permissao = db.Column(db.String(10), default='leitura')  # leitura, edicao
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    template = db.relationship('Template', back_populates='compartilhamentos')
    usuario = db.relationship('User', foreign_keys=[user_id])
    compartilhador = db.relationship('User', foreign_keys=[compartilhado_por])
    
    __table_args__ = (db.UniqueConstraint('template_id', 'user_id'),)

class TemplateCategoria(db.Model):
    __tablename__ = 'template_categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    icone = db.Column(db.String(50))  # Nome do ícone
    cor = db.Column(db.String(7), default='#6366f1')  # Cor hex
    ativo = db.Column(db.Boolean, default=True)
    ordem = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'icone': self.icone,
            'cor': self.cor,
            'ativo': self.ativo,
            'ordem': self.ordem
        }
