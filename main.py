#!/usr/bin/env python3
"""
Arquivo principal para executar a aplicação LegalAI
Este arquivo importa e executa o main.py da pasta src
"""

import os
import sys

# Adicionar o diretório atual ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar e executar o main da pasta src
if __name__ == '__main__':
    from src.main import app
    
    print("🚀 Iniciando LegalAI API...")
    app.run(
        host='0.0.0.0',
        port=5005,
        debug=True,
        use_reloader=True
    ) 