import hashlib
from werkzeug.security import check_password_hash, generate_password_hash

def verify_password_custom(password, hash_str):
    """Verifica senha usando hash personalizado"""
    try:
        # Primeiro tenta o hash personalizado (usado no init_db_simple)
        test_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 100000)
        if test_hash.hex() == hash_str:
            return True
        
        # Se não der certo, tenta o hash padrão do Werkzeug
        return check_password_hash(hash_str, password)
    except:
        return False

def generate_password_hash_custom(password):
    """Gera hash da senha usando método padrão do Werkzeug"""
    return generate_password_hash(password) 