from src.extensions import db
from datetime import datetime

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    documento = db.Column(db.String(20), unique=True, nullable=False)  # CPF ou CNPJ
    tipo_pessoa = db.Column(db.Enum('PF', 'PJ', name='tipo_pessoa'), default='PF')
    email = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    endereco = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'documento': self.documento,
            'tipo_pessoa': self.tipo_pessoa,
            'email': self.email,
            'telefone': self.telefone,
            'endereco': self.endereco,
            'observacoes': self.observacoes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'usuario_id': self.usuario_id,
            'ativo': self.ativo
        } 