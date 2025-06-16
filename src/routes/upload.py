from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import docx
import PyPDF2
from src.extensions import db
from src.models.template import Template

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx'}
UPLOAD_FOLDER = 'uploads'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extrai texto de arquivo PDF"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise Exception(f"Erro ao processar PDF: {str(e)}")

def extract_text_from_docx(file_path):
    """Extrai texto de arquivo DOCX"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        raise Exception(f"Erro ao processar DOCX: {str(e)}")

@upload_bp.route('/document', methods=['POST'])
@jwt_required()
def upload_document():
    """Upload de documento para criar template"""
    usuario_id = get_jwt_identity()
    
    # Verificar se o arquivo foi enviado
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Tipo de arquivo não permitido. Use .pdf ou .docx"}), 400
    
    try:
        # Criar diretório de upload se não existir
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        
        # Salvar arquivo temporariamente
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Extrair texto baseado no tipo de arquivo
        file_extension = filename.rsplit('.', 1)[1].lower()
        
        if file_extension == 'pdf':
            extracted_text = extract_text_from_pdf(file_path)
        elif file_extension == 'docx':
            extracted_text = extract_text_from_docx(file_path)
        else:
            return jsonify({"error": "Tipo de arquivo não suportado"}), 400
        
        # Obter dados adicionais do formulário
        titulo = request.form.get('titulo', filename.rsplit('.', 1)[0])
        categoria = request.form.get('categoria', 'Geral')
        
        # Detectar e destacar possíveis variáveis no texto
        import re
        # Padrões comuns para variáveis
        patterns = [
            r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})*\b',  # PALAVRAS EM MAIÚSCULO
            r'_+',  # Linhas sublinhadas
            r'\[.*?\]',  # Texto entre colchetes
            r'\{.*?\}',  # Texto entre chaves
        ]
        
        processed_text = extracted_text
        variable_suggestions = []
        
        for pattern in patterns:
            matches = re.findall(pattern, extracted_text)
            for match in matches:
                if len(match.strip()) > 2 and match not in variable_suggestions:
                    variable_suggestions.append(match.strip())
                    # Substituir por variável no formato {VARIAVEL}
                    variable_name = match.strip().upper().replace(' ', '_')
                    processed_text = processed_text.replace(match, f"{{{variable_name}}}")
        
        # Criar template no banco de dados
        template = Template(
            titulo=titulo,
            categoria=categoria,
            conteudo=processed_text,
            usuario_id=usuario_id,
            publico=False
        )
        
        db.session.add(template)
        db.session.commit()
        
        # Remover arquivo temporário
        os.remove(file_path)
        
        return jsonify({
            "message": "Documento processado com sucesso",
            "template": template.to_dict(),
            "original_text": extracted_text,
            "processed_text": processed_text,
            "variable_suggestions": variable_suggestions
        }), 201
        
    except Exception as e:
        # Remover arquivo em caso de erro
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": f"Erro ao processar arquivo: {str(e)}"}), 500

@upload_bp.route('/analyze', methods=['POST'])
@jwt_required()
def analyze_document():
    """Analisa documento sem salvar, apenas para prévia"""
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Tipo de arquivo não permitido. Use .pdf ou .docx"}), 400
    
    try:
        # Criar diretório de upload se não existir
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        
        # Salvar arquivo temporariamente
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Extrair texto
        file_extension = filename.rsplit('.', 1)[1].lower()
        
        if file_extension == 'pdf':
            extracted_text = extract_text_from_pdf(file_path)
        elif file_extension == 'docx':
            extracted_text = extract_text_from_docx(file_path)
        
        # Analisar possíveis variáveis
        import re
        patterns = [
            r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})*\b',
            r'_+',
            r'\[.*?\]',
            r'\{.*?\}',
        ]
        
        variable_suggestions = []
        for pattern in patterns:
            matches = re.findall(pattern, extracted_text)
            for match in matches:
                if len(match.strip()) > 2 and match not in variable_suggestions:
                    variable_suggestions.append(match.strip())
        
        # Estatísticas do documento
        word_count = len(extracted_text.split())
        char_count = len(extracted_text)
        paragraph_count = len([p for p in extracted_text.split('\n') if p.strip()])
        
        # Remover arquivo temporário
        os.remove(file_path)
        
        return jsonify({
            "filename": filename,
            "text": extracted_text,
            "variable_suggestions": variable_suggestions,
            "stats": {
                "words": word_count,
                "characters": char_count,
                "paragraphs": paragraph_count
            }
        }), 200
        
    except Exception as e:
        # Remover arquivo em caso de erro
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": f"Erro ao analisar arquivo: {str(e)}"}), 500 