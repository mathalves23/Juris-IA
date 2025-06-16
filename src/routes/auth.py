from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from src.extensions import db
from src.models.user import User
from src.models.subscription import Subscription
from src.models.config import Config
from src.auth import verify_password_custom, generate_password_hash_custom

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Verificar se todos os campos necessários estão presentes
    if not all(k in data for k in ('nome', 'email', 'senha')):
        return jsonify({"error": "Dados incompletos"}), 400
    
    # Verificar se o email já está em uso
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email já cadastrado"}), 400
    
    # Criar novo usuário
    novo_usuario = User(
        nome=data['nome'],
        email=data['email'],
        senha_hash=generate_password_hash(data['senha']),
        papel=data.get('papel', 'usuario')
    )
    
    # Adicionar usuário ao banco de dados
    db.session.add(novo_usuario)
    db.session.commit()
    
    # Gerar tokens
    access_token = create_access_token(identity=novo_usuario.id)
    refresh_token = create_refresh_token(identity=novo_usuario.id)
    
    return jsonify({
        "message": "Usuário registrado com sucesso",
        "user": novo_usuario.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Verificar se todos os campos necessários estão presentes
    if not all(k in data for k in ('email', 'senha')):
        return jsonify({"error": "Dados incompletos"}), 400
    
    # Buscar usuário pelo email
    usuario = User.query.filter_by(email=data['email']).first()
    
    # Verificar se o usuário existe e a senha está correta
    if not usuario or not usuario.verify_password(data['senha']):
        return jsonify({"error": "Credenciais inválidas"}), 401
    
    # Verificar se o usuário está ativo
    if not usuario.ativo:
        return jsonify({"error": "Usuário inativo ou bloqueado"}), 403
    
    # Gerar tokens
    access_token = create_access_token(identity=usuario.id)
    refresh_token = create_refresh_token(identity=usuario.id)
    
    return jsonify({
        "message": "Login realizado com sucesso",
        "user": usuario.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    # Obter identidade do usuário a partir do token de refresh
    identity = get_jwt_identity()
    
    # Gerar novo token de acesso
    access_token = create_access_token(identity=identity)
    
    return jsonify({
        "access_token": access_token
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    # Obter identidade do usuário a partir do token
    identity = get_jwt_identity()
    
    # Buscar usuário pelo ID
    usuario = User.query.get(identity)
    
    if not usuario:
        return jsonify({"error": "Usuário não encontrado"}), 404
    
    return jsonify(usuario.to_dict()), 200

@auth_bp.route('/set-flags', methods=['POST'])
@jwt_required()
def set_flags():
    """
    Define configurações/flags baseadas em string para diferentes ambientes
    """
    data = request.get_json()
    
    if not all(k in data for k in ('flags', 'environment')):
        return jsonify({"error": "Dados incompletos"}), 400
    
    flags_string = data.get('flags', '')
    environment = data.get('environment', 'test')
    
    # Verificar se o ambiente é válido
    if environment not in ['test', 'prod']:
        return jsonify({"error": "Ambiente inválido. Use 'test' ou 'prod'"}), 400
    
    # Obter identidade do usuário
    identity = get_jwt_identity()
    usuario = User.query.get(identity)
    
    if not usuario:
        return jsonify({"error": "Usuário não encontrado"}), 404
    
    # Verificar se o usuário tem permissão para configurar flags
    if usuario.papel not in ['admin', 'superuser']:
        return jsonify({"error": "Permissão insuficiente"}), 403
    
    try:
        # Processar e armazenar as flags usando o modelo Config
        flags_dict = Config.set_flags_from_string(environment, flags_string, identity)
        
        return jsonify({
            "message": f"Flags configuradas com sucesso para o ambiente {environment}",
            "environment": environment,
            "flags": flags_dict
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro ao processar flags: {str(e)}"}), 400

@auth_bp.route('/flags', methods=['GET'])
@jwt_required()
def get_flags():
    """
    Obtém as configurações/flags atuais para um ambiente específico
    """
    environment = request.args.get('environment', 'test')
    
    # Verificar se o ambiente é válido
    if environment not in ['test', 'prod']:
        return jsonify({"error": "Ambiente inválido. Use 'test' ou 'prod'"}), 400
    
    # Obter identidade do usuário
    identity = get_jwt_identity()
    usuario = User.query.get(identity)
    
    if not usuario:
        return jsonify({"error": "Usuário não encontrado"}), 404
    
    # Buscar configurações do banco de dados
    flags = Config.get_environment_configs(environment)
    
    # Se não houver configurações, usar valores padrão
    if not flags:
        default_flags = {
            'test': {
                'debug_mode': True,
                'ai_enabled': True,
                'document_limit': 100,
                'export_pdf': True,
                'export_docx': True
            },
            'prod': {
                'debug_mode': False,
                'ai_enabled': True,
                'document_limit': 1000,
                'export_pdf': True,
                'export_docx': True
            }
        }
        flags = default_flags.get(environment, {})
    
    return jsonify({
        "environment": environment,
        "flags": flags
    }), 200
