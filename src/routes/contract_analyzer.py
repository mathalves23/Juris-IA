"""
Rotas para Análise Inteligente de Contratos
"""

import os
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
import json
from datetime import datetime

from src.services.contract_analyzer import ContractAnalyzer
from src.models.contract_analysis import ContractAnalysis

# Configuração
bp = Blueprint('contract_analyzer', __name__)
logger = logging.getLogger(__name__)

# Configurações de upload
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Mock data para demonstração
MOCK_ANALYSES = [
    {
        "id": 1,
        "title": "Contrato de Prestação de Serviços",
        "status": "completed",
        "score_risco": 3,
        "nivel_complexidade": "medium",
        "created_at": "2024-12-13T10:00:00Z",
        "updated_at": "2024-12-13T10:30:00Z",
        "clausulas_extraidas": [
            "Cláusula de pagamento",
            "Cláusula de rescisão",
            "Cláusula de confidencialidade"
        ],
        "riscos_identificados": [
            "Ausência de cláusula de multa por atraso",
            "Prazo de pagamento muito extenso"
        ],
        "sugestoes_melhoria": [
            "Incluir cláusula de multa por atraso no pagamento",
            "Definir prazo máximo de 30 dias para pagamento"
        ]
    },
    {
        "id": 2,
        "title": "Contrato de Locação Comercial",
        "status": "analyzing",
        "score_risco": 2,
        "nivel_complexidade": "low",
        "created_at": "2024-12-13T11:00:00Z",
        "updated_at": "2024-12-13T11:15:00Z",
        "clausulas_extraidas": [
            "Cláusula de prazo",
            "Cláusula de valor do aluguel",
            "Cláusula de reajuste"
        ],
        "riscos_identificados": [
            "Índice de reajuste não especificado claramente"
        ],
        "sugestoes_melhoria": [
            "Especificar índice de reajuste (IGPM, IPCA, etc.)"
        ]
    }
]

MOCK_STATS = {
    "total_analyses": 15,
    "completed_analyses": 12,
    "pending_analyses": 3,
    "average_risk_score": 2.8,
    "risk_distribution": {
        "low": 8,
        "medium": 5,
        "high": 2
    },
    "complexity_distribution": {
        "low": 6,
        "medium": 7,
        "high": 2
    },
    "analyses_this_month": 8,
    "time_saved_hours": 45.5
}

def allowed_file(filename):
    """Verifica se o arquivo é permitido"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_size(file_content):
    """Valida tamanho do arquivo"""
    return len(file_content) <= MAX_FILE_SIZE

@bp.route('/upload-contract', methods=['POST'])
@jwt_required()
def upload_and_analyze_contract():
    """Upload e análise de contrato"""
    try:
        user_id = get_jwt_identity()
        
        # Verifica se arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo foi enviado'
            }), 400
        
        file = request.files['file']
        
        # Verifica se arquivo tem nome
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo selecionado'
            }), 400
        
        # Valida extensão
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': f'Formato não suportado. Use: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Lê conteúdo do arquivo
        file_content = file.read()
        
        # Valida tamanho
        if not validate_file_size(file_content):
            return jsonify({
                'success': False,
                'message': f'Arquivo muito grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB'
            }), 413
        
        # Inicializa analisador
        analyzer = ContractAnalyzer()
        
        # Extrai texto do arquivo
        try:
            text_content = analyzer.extract_text_from_file(file_content, file.filename)
        except Exception as e:
            logger.error(f"Erro ao extrair texto: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Erro ao processar arquivo: {str(e)}'
            }), 400
        
        # Valida se texto foi extraído
        if not text_content.strip():
            return jsonify({
                'success': False,
                'message': 'Não foi possível extrair texto do arquivo'
            }), 400
        
        # Realiza análise
        try:
            analysis_result = analyzer.analyze_contract(text_content, file.filename)
        except Exception as e:
            logger.error(f"Erro na análise: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Erro na análise: {str(e)}'
            }), 500
        
        # Salva análise no banco
        try:
            analysis = analyzer.save_analysis(
                analysis_result=analysis_result,
                filename=secure_filename(file.filename),
                text=text_content,
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Erro ao salvar análise: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Erro ao salvar análise: {str(e)}'
            }), 500
        
        # Retorna resultado
        return jsonify({
            'success': True,
            'data': {
                'analysis_id': analysis.id,
                'nome_arquivo': analysis.nome_arquivo,
                'tipo_contrato': analysis.tipo_contrato,
                'score_risco': analysis.score_risco,
                'nivel_risco': analysis.get_nivel_risco_texto(),
                'cor_risco': analysis.get_cor_risco(),
                'nivel_complexidade': analysis.nivel_complexidade,
                'tempo_analise': analysis.tempo_analise,
                'tokens_utilizados': analysis.tokens_utilizados,
                'created_at': analysis.created_at.isoformat()
            },
            'message': 'Análise realizada com sucesso!'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no upload e análise: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@bp.route('/analysis/<int:analysis_id>', methods=['GET'])
@jwt_required()
def get_analysis_details(analysis_id):
    """Obter detalhes completos da análise"""
    try:
        user_id = get_jwt_identity()
        analyzer = ContractAnalyzer()
        
        # Busca análise
        analysis = analyzer.get_analysis_by_id(analysis_id, user_id)
        
        if not analysis:
            return jsonify({
                'success': False,
                'message': 'Análise não encontrada'
            }), 404
        
        return jsonify({
            'success': True,
            'data': analysis.to_dict(),
            'message': 'Análise encontrada'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar análise: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@bp.route('/analyses', methods=['GET'])
@jwt_required()
def list_user_analyses():
    """Listar análises do usuário"""
    try:
        user_id = get_jwt_identity()
        limit = request.args.get('limit', 20, type=int)
        
        analyzer = ContractAnalyzer()
        analyses = analyzer.get_user_analyses(user_id, limit)
        
        return jsonify({
            'success': True,
            'data': [analysis.to_summary_dict() for analysis in analyses],
            'total': len(analyses),
            'message': f'{len(analyses)} análises encontradas'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar análises: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@bp.route('/analysis/<int:analysis_id>', methods=['DELETE'])
@jwt_required()
def delete_analysis(analysis_id):
    """Deletar análise"""
    try:
        user_id = get_jwt_identity()
        analyzer = ContractAnalyzer()
        
        if analyzer.delete_analysis(analysis_id, user_id):
            return jsonify({
                'success': True,
                'message': 'Análise deletada com sucesso'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Análise não encontrada'
            }), 404
            
    except Exception as e:
        logger.error(f"Erro ao deletar análise: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@bp.route('/stats', methods=['GET'])
@jwt_required()
def get_analysis_stats():
    """Estatísticas das análises do usuário"""
    try:
        user_id = get_jwt_identity()
        
        # Busca todas as análises do usuário
        analyses = ContractAnalysis.query.filter_by(user_id=user_id).all()
        
        if not analyses:
            return jsonify({
                'success': True,
                'data': {
                    'total_analyses': 0,
                    'risk_distribution': {},
                    'complexity_distribution': {},
                    'contract_types': {},
                    'avg_risk_score': 0
                },
                'message': 'Nenhuma análise encontrada'
            }), 200
        
        # Calcula estatísticas
        total_analyses = len(analyses)
        risk_scores = [a.score_risco for a in analyses if a.score_risco is not None]
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        # Distribuição de riscos
        risk_distribution = {'Baixo': 0, 'Médio': 0, 'Alto': 0}
        for analysis in analyses:
            risk_level = analysis.get_nivel_risco_texto()
            if risk_level in risk_distribution:
                risk_distribution[risk_level] += 1
        
        # Distribuição de complexidade
        complexity_distribution = {'Baixa': 0, 'Média': 0, 'Alta': 0}
        for analysis in analyses:
            if analysis.nivel_complexidade:
                complexity_distribution[analysis.nivel_complexidade] += 1
        
        # Tipos de contratos
        contract_types = {}
        for analysis in analyses:
            if analysis.tipo_contrato:
                contract_types[analysis.tipo_contrato] = contract_types.get(analysis.tipo_contrato, 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'total_analyses': total_analyses,
                'risk_distribution': risk_distribution,
                'complexity_distribution': complexity_distribution,  
                'contract_types': contract_types,
                'avg_risk_score': round(avg_risk_score, 1)
            },
            'message': 'Estatísticas calculadas com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@bp.route('/compare', methods=['POST'])
@jwt_required()
def compare_analyses():
    """Comparar duas análises"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'analysis_id_1' not in data or 'analysis_id_2' not in data:
            return jsonify({
                'success': False,
                'message': 'IDs das análises são obrigatórios'
            }), 400
        
        analyzer = ContractAnalyzer()
        
        # Busca as duas análises
        analysis_1 = analyzer.get_analysis_by_id(data['analysis_id_1'], user_id)
        analysis_2 = analyzer.get_analysis_by_id(data['analysis_id_2'], user_id)
        
        if not analysis_1 or not analysis_2:
            return jsonify({
                'success': False,
                'message': 'Uma ou mais análises não foram encontradas'
            }), 404
        
        # Prepara comparação
        comparison = {
            'analysis_1': {
                'id': analysis_1.id,
                'nome_arquivo': analysis_1.nome_arquivo,
                'tipo_contrato': analysis_1.tipo_contrato,
                'score_risco': analysis_1.score_risco,
                'nivel_complexidade': analysis_1.nivel_complexidade
            },
            'analysis_2': {
                'id': analysis_2.id,
                'nome_arquivo': analysis_2.nome_arquivo,
                'tipo_contrato': analysis_2.tipo_contrato,
                'score_risco': analysis_2.score_risco,
                'nivel_complexidade': analysis_2.nivel_complexidade
            },
            'differences': {
                'risk_difference': abs((analysis_1.score_risco or 0) - (analysis_2.score_risco or 0)),
                'same_type': analysis_1.tipo_contrato == analysis_2.tipo_contrato,
                'same_complexity': analysis_1.nivel_complexidade == analysis_2.nivel_complexidade
            }
        }
        
        return jsonify({
            'success': True,
            'data': comparison,
            'message': 'Comparação realizada com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na comparação: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@bp.route('/analyses', methods=['GET'])
@cross_origin()
def get_analyses():
    """Retorna lista de análises de contratos"""
    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Simular paginação
        analyses = MOCK_ANALYSES[offset:offset+limit]
        
        return jsonify({
            'success': True,
            'data': analyses,
            'total': len(MOCK_ANALYSES),
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/stats', methods=['GET'])
@cross_origin()
def get_stats():
    """Retorna estatísticas das análises"""
    try:
        return jsonify({
            'success': True,
            'data': MOCK_STATS
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/analyze', methods=['POST'])
@cross_origin()
def analyze_contract():
    """Analisa um novo contrato"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados não fornecidos'
            }), 400
        
        # Simular análise
        analysis = {
            "id": len(MOCK_ANALYSES) + 1,
            "title": data.get('title', 'Contrato sem título'),
            "status": "analyzing",
            "score_risco": 2,
            "nivel_complexidade": "medium",
            "created_at": datetime.now().isoformat() + 'Z',
            "updated_at": datetime.now().isoformat() + 'Z',
            "clausulas_extraidas": [
                "Analisando cláusulas...",
                "Processamento em andamento..."
            ],
            "riscos_identificados": [
                "Análise em processamento..."
            ],
            "sugestoes_melhoria": [
                "Aguarde a conclusão da análise..."
            ]
        }
        
        return jsonify({
            'success': True,
            'data': analysis,
            'message': 'Análise iniciada com sucesso'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/analyses/<int:analysis_id>', methods=['GET'])
@cross_origin()
def get_analysis(analysis_id):
    """Retorna uma análise específica"""
    try:
        # Procurar análise no mock
        analysis = next((a for a in MOCK_ANALYSES if a['id'] == analysis_id), None)
        
        if not analysis:
            return jsonify({
                'success': False,
                'error': 'Análise não encontrada'
            }), 404
        
        return jsonify({
            'success': True,
            'data': analysis
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/analyses/<int:analysis_id>', methods=['DELETE'])
@cross_origin()
def delete_analysis(analysis_id):
    """Deleta uma análise"""
    try:
        # Simular deleção
        return jsonify({
            'success': True,
            'message': 'Análise deletada com sucesso'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Rota para health check específica do módulo
@bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check do módulo de análise de contratos"""
    return jsonify({
        'module': 'contract_analyzer',
        'status': 'healthy',
        'version': '1.0.0',
        'features': [
            'contract_analysis',
            'risk_assessment',
            'clause_extraction',
            'statistics'
        ]
    }), 200 