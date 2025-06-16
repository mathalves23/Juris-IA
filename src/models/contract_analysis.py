from src.extensions import db
from datetime import datetime
import json

class ContractAnalysis(db.Model):
    __tablename__ = 'contract_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    tipo_contrato = db.Column(db.String(100))
    conteudo_original = db.Column(db.Text, nullable=False)
    
    # Análise da IA
    score_risco = db.Column(db.Integer)  # 0-100 (0 = baixo risco, 100 = alto risco)
    nivel_complexidade = db.Column(db.String(20))  # 'Baixa', 'Média', 'Alta'
    
    # Resultados estruturados (JSON)
    clausulas_extraidas = db.Column(db.Text)  # JSON das cláusulas
    riscos_identificados = db.Column(db.Text)  # JSON dos riscos
    sugestoes_melhoria = db.Column(db.Text)  # JSON das sugestões
    pontos_atencao = db.Column(db.Text)  # JSON dos pontos críticos
    
    # Metadados
    tempo_analise = db.Column(db.Float)  # em segundos
    tokens_utilizados = db.Column(db.Integer)
    versao_ia = db.Column(db.String(50), default='gpt-4')
    
    # Relacionamentos
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_clausulas(self):
        """Retorna cláusulas como dict"""
        return json.loads(self.clausulas_extraidas) if self.clausulas_extraidas else {}
    
    def set_clausulas(self, clausulas_dict):
        """Define cláusulas a partir de dict"""
        self.clausulas_extraidas = json.dumps(clausulas_dict, ensure_ascii=False)
    
    def get_riscos(self):
        """Retorna riscos como dict"""
        return json.loads(self.riscos_identificados) if self.riscos_identificados else {}
    
    def set_riscos(self, riscos_dict):
        """Define riscos a partir de dict"""
        self.riscos_identificados = json.dumps(riscos_dict, ensure_ascii=False)
    
    def get_sugestoes(self):
        """Retorna sugestões como dict"""
        return json.loads(self.sugestoes_melhoria) if self.sugestoes_melhoria else {}
    
    def set_sugestoes(self, sugestoes_dict):
        """Define sugestões a partir de dict"""
        self.sugestoes_melhoria = json.dumps(sugestoes_dict, ensure_ascii=False)
    
    def get_pontos_atencao(self):
        """Retorna pontos de atenção como dict"""
        return json.loads(self.pontos_atencao) if self.pontos_atencao else {}
    
    def set_pontos_atencao(self, pontos_dict):
        """Define pontos de atenção a partir de dict"""
        self.pontos_atencao = json.dumps(pontos_dict, ensure_ascii=False)
    
    def get_nivel_risco_texto(self):
        """Retorna nível de risco em texto"""
        if self.score_risco is None:
            return "Não analisado"
        elif self.score_risco <= 30:
            return "Baixo"
        elif self.score_risco <= 60:
            return "Médio"
        else:
            return "Alto"
    
    def get_cor_risco(self):
        """Retorna cor baseada no nível de risco"""
        if self.score_risco is None:
            return "#gray"
        elif self.score_risco <= 30:
            return "#10B981"  # Verde
        elif self.score_risco <= 60:
            return "#F59E0B"  # Amarelo
        else:
            return "#EF4444"  # Vermelho
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome_arquivo': self.nome_arquivo,
            'tipo_contrato': self.tipo_contrato,
            'score_risco': self.score_risco,
            'nivel_risco': self.get_nivel_risco_texto(),
            'cor_risco': self.get_cor_risco(),
            'nivel_complexidade': self.nivel_complexidade,
            'clausulas': self.get_clausulas(),
            'riscos': self.get_riscos(),
            'sugestoes': self.get_sugestoes(),
            'pontos_atencao': self.get_pontos_atencao(),
            'tempo_analise': self.tempo_analise,
            'tokens_utilizados': self.tokens_utilizados,
            'versao_ia': self.versao_ia,
            'user_id': self.user_id,
            'document_id': self.document_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_summary_dict(self):
        """Versão resumida para listagens"""
        return {
            'id': self.id,
            'nome_arquivo': self.nome_arquivo,
            'tipo_contrato': self.tipo_contrato,
            'score_risco': self.score_risco,
            'nivel_risco': self.get_nivel_risco_texto(),
            'cor_risco': self.get_cor_risco(),
            'nivel_complexidade': self.nivel_complexidade,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 