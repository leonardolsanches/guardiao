
#!/usr/bin/env python3
import zipfile
import os
from datetime import datetime

def create_deploy_package():
    """Cria um pacote ZIP com todos os arquivos necessários para deploy"""
    
    # Nome do arquivo ZIP com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f'guarda_theo_deploy_{timestamp}.zip'
    
    # Arquivos e diretórios para incluir no ZIP
    files_to_include = [
        'app.py',
        'main.py',
        'pyproject.toml',
        'static/style.css',
        'static/script.js',
        'static/uploads/theo_logo.png',
        'templates/index.html',
        'templates/calendario.html',
        'templates/conta.html',
        'data/usuarios.json',
        'data/calendario.json',
        'data/despesas.json'
    ]
    
    # Criar diretórios necessários no ZIP
    directories_to_create = [
        'data/',
        'static/',
        'static/uploads/',
        'templates/',
        'export/'
    ]
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Adicionar diretórios vazios
        for directory in directories_to_create:
            zipf.writestr(directory, '')
        
        # Adicionar arquivos
        for file_path in files_to_include:
            if os.path.exists(file_path):
                zipf.write(file_path, file_path)
                print(f"Adicionado: {file_path}")
            else:
                print(f"Arquivo não encontrado: {file_path}")
        
        # Criar requirements.txt para o Render
        requirements_content = """flask>=3.1.1
werkzeug>=3.1.3
"""
        zipf.writestr('requirements.txt', requirements_content)
        print("Adicionado: requirements.txt")
        
        # Criar Procfile para o Render (opcional)
        procfile_content = "web: python main.py"
        zipf.writestr('Procfile', procfile_content)
        print("Adicionado: Procfile")
        
        # Criar .gitignore
        gitignore_content = """__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
"""
        zipf.writestr('.gitignore', gitignore_content)
        print("Adicionado: .gitignore")
    
    print(f"\nPacote criado com sucesso: {zip_filename}")
    print(f"Tamanho do arquivo: {os.path.getsize(zip_filename)} bytes")
    
    # Instruções para deploy no Render
    print("\n" + "="*50)
    print("INSTRUÇÕES PARA DEPLOY NO RENDER:")
    print("="*50)
    print("1. Faça upload do arquivo ZIP para um repositório GitHub")
    print("2. No Render, conecte seu repositório GitHub")
    print("3. Configure as seguintes variáveis:")
    print("   - Build Command: pip install -r requirements.txt")
    print("   - Start Command: python main.py")
    print("   - Environment: Python 3")
    print("4. Deploy automático será feito!")
    print("\nMas recomendo usar o Replit Deploy que é mais simples!")

if __name__ == '__main__':
    create_deploy_package()
