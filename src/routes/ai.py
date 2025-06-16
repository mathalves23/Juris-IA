from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
import asyncio
import random
import time
from datetime import datetime
from src.extensions import db
from src.models.document import Document
from src.config import Config
from src.services.ai_service import LegalAIService, AIRequest, AITask, DocumentType
from src.middleware.subscription_middleware import check_usage_limit

ai_bp = Blueprint('ai', __name__)
ai_service = LegalAIService()

@ai_bp.route('/test', methods=['GET'])
@jwt_required()
def test_ai():
    """Teste simples da IA."""
    return jsonify({
        "success": True,
        "message": "IA funcionando!",
        "user_id": get_jwt_identity()
    }), 200

@ai_bp.route('/generate', methods=['POST', 'OPTIONS'])
def generate_text():
    """Gerar texto jurídico usando IA (modo demonstração)."""
    # Headers CORS para OPTIONS
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        return response
        
    try:
        data = request.get_json() or {}
        prompt = data.get('prompt', 'Gerar documento jurídico')
        
        # Simular processamento IA
        time.sleep(0.5)  # Simular delay de processamento
        
        mock_responses = [
            f"Com base no prompt '{prompt}', elaborei o seguinte texto jurídico: Este documento estabelece as condições e termos necessários para o cumprimento das obrigações legais pertinentes ao caso em questão, considerando as normativas vigentes e os precedentes jurisprudenciais aplicáveis.",
            f"Considerando sua solicitação sobre '{prompt}', sugiro o seguinte conteúdo: As partes envolvidas neste instrumento legal comprometem-se a cumprir integralmente as disposições aqui estabelecidas, sob pena das sanções previstas em lei.",
            f"De acordo com a análise do tema '{prompt}', o documento deve conter: Cláusulas específicas que garantam a segurança jurídica das partes, estabelecendo direitos e deveres de forma clara e inequívoca."
        ]
        
        response_text = random.choice(mock_responses)
        
        response_data = {
            "success": True,
            "generated_text": response_text,
            "suggestions": [
                "Revisar cláusulas específicas conforme legislação",
                "Adicionar referências legais pertinentes",
                "Verificar formatação e estrutura do documento",
                "Considerar jurisprudência recente sobre o tema"
            ],
            "metadata": {
                "model": "JurisIA-GPT-4",
                "tokens_used": random.randint(150, 600),
                "response_time": round(random.uniform(0.5, 2.0), 2),
                "legal_accuracy": "95%",
                "confidence_score": round(random.uniform(0.85, 0.98), 2)
            },
            "confidence": round(random.uniform(0.8, 0.95), 2),
            "processing_time": "0.5s",
            "legal_references": [
                "Código Civil Brasileiro",
                "Lei 13.105/2015 (CPC)",
                "Constituição Federal/1988"
            ]
        }
        
        response = jsonify(response_data)
        
        # Adicionar headers CORS
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        
        return response, 200
        
    except Exception as e:
        response = jsonify({
            "success": False,
            "error": f"Erro ao processar solicitação de IA: {str(e)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@ai_bp.route('/review', methods=['POST'])
@jwt_required()
@check_usage_limit('ai_requests')
def review_content():
    """Revisar conteúdo jurídico."""
    usuario_id = get_jwt_identity()
    data = request.get_json()
    
    if 'content' not in data:
        return jsonify({"error": "Conteúdo não fornecido"}), 400
    
    try:
        ai_request = AIRequest(
            task=AITask.REVIEW,
            content=data['content'],
            user_id=usuario_id
        )
        
        response = asyncio.run(ai_service.process_request(ai_request))
        
        return jsonify({
            "success": response.success,
            "review": response.content,
            "suggestions": response.suggestions,
            "metadata": response.metadata,
            "confidence": response.confidence
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erro na revisão: {str(e)}"
        }), 500


@ai_bp.route('/summarize', methods=['POST'])
@jwt_required()
@check_usage_limit('ai_requests')
def summarize_content():
    """Resumir conteúdo jurídico."""
    usuario_id = get_jwt_identity()
    data = request.get_json()
    
    if 'content' not in data:
        return jsonify({"error": "Conteúdo não fornecido"}), 400
    
    try:
        ai_request = AIRequest(
            task=AITask.SUMMARIZE,
            content=data['content'],
            user_id=usuario_id
        )
        
        response = asyncio.run(ai_service.process_request(ai_request))
        
        return jsonify({
            "success": response.success,
            "summary": response.content,
            "metadata": response.metadata,
            "confidence": response.confidence
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erro no resumo: {str(e)}"
        }), 500

# === ROTAS MOCK PARA DEMONSTRAÇÃO (SEM AUTENTICAÇÃO) ===

@ai_bp.route('/generate-demo', methods=['POST', 'OPTIONS'])
def generate_text_demo():
    """Gerar texto jurídico usando IA (versão demo sem autenticação)."""
    # Headers CORS
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        return response
        
    try:
        data = request.get_json() or {}
        prompt = data.get('prompt', 'Gerar documento jurídico')
        
        # Simular processamento IA
        time.sleep(0.5)  # Simular delay
        
        mock_responses = [
            "Com base na sua solicitação, elaborei o seguinte documento jurídico: Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
            "Considerando os aspectos legais mencionados, sugiro o seguinte texto: Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
            "De acordo com a legislação vigente, o documento deve conter: Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."
        ]
        
        response_text = random.choice(mock_responses)
        
        response = jsonify({
            "success": True,
            "generated_text": response_text,
            "suggestions": [
                "Revisar cláusulas específicas",
                "Adicionar referências legais",
                "Verificar formatação"
            ],
            "metadata": {
                "model": "gpt-4-turbo",
                "tokens_used": random.randint(100, 500),
                "response_time": round(random.uniform(0.5, 2.0), 2)
            },
            "confidence": round(random.uniform(0.8, 0.95), 2),
            "processing_time": "0.5s"
        })
        
        # Adicionar headers CORS
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        
        return response, 200
        
    except Exception as e:
        response = jsonify({
            "success": False,
            "error": f"Erro ao processar solicitação: {str(e)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

# Criar rota mock para a rota original também
@ai_bp.route('/generate-mock', methods=['POST', 'OPTIONS'])
def generate_text_mock():
    """Versão mock da rota generate sem autenticação."""
    return generate_text_demo()
