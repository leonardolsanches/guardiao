```python
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
import json
import os
import csv
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'guarda_theo_secret_2025'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure directories exist
os.makedirs('data', exist_ok=True)
os.makedirs('export', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)

def load_json_file(filename, default_data=None):
    """Load JSON file with error handling"""
    if default_data is None:
        default_data = {}
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            logger.debug(f"Loaded JSON file: {filename}")
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading JSON file {filename}: {e}")
        return default_data

def save_json_file(filename, data):
    """Save data to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved JSON file: {filename}")
    except Exception as e:
        logger.error(f"Error saving JSON file {filename}: {e}")

def import_excel_data():
    """Import historical expense data from Excel, replacing existing JSON data"""
    excel_file = 'Financial Records Excel (version 1).xlsx'
    logger.debug(f"Checking for Excel file: {excel_file}")
    
    if not os.path.exists(excel_file):
        logger.error(f"Excel file not found: {excel_file}")
        return
    
    try:
        # Read Excel data
        logger.debug("Reading Excel file")
        df = pd.read_excel(excel_file, sheet_name=0, skiprows=65)
        logger.debug(f"Excel rows read: {len(df)}")
        
        # Initialize new expenses list (zero out existing data)
        despesas = []
        current_id = 0
        
        # Category mapping based on description
        category_map = {
            'escolaridade': 'educacao',
            'material escolar': 'educacao',
            'apostilas': 'educacao',
            'livro': 'educacao',
            'mensalidade': 'educacao',
            'transporte escolar': 'transporte',
            'alimentação': 'alimentacao',
            'alimentos': 'alimentacao',
            'almoço': 'alimentacao',
            'celular': 'comunicacao',
            'internet': 'comunicacao',
            'recarga': 'comunicacao',
            'plano de saude': 'saude',
            'terapia': 'saude',
            'dentista': 'saude',
            'remedios': 'saude',
            'roupas': 'vestuario',
            'uniformes': 'vestuario',
            'tênis': 'vestuario',
            'bermudas': 'vestuario'
        }
        
        # Process Excel data
        for index, row in df.iterrows():
            try:
                # Skip rows with invalid data
                if pd.isna(row['day']) or pd.isna(row['month']) or pd.isna(row['year']) or pd.isna(row['expense']):
                    logger.debug(f"Skipping row {index}: missing required fields")
                    continue
                
                # Format date as YYYY-MM-DD
                date_str = f"{int(row['year']):04d}-{int(row['month']):02d}-{int(row['day']):02d}"
                
                # Skip payment rows
                if str(row['expense']).lower() == 'pagamento':
                    logger.debug(f"Skipping row {index}: payment row")
                    continue
                
                # Determine category
                descricao = str(row['expense']).lower()
                categoria = 'outros'
                for key, value in category_map.items():
                    if key in descricao:
                        categoria = value
                        break
                
                # Determine tipo (recorrente, parcelada, or normal)
                tipo = 'recorrente' if any(key in descricao for key in ['escolaridade', 'transporte escolar', 'alimentação', 'alimentos', 'celular', 'internet', 'recarga', 'plano de saude']) else 'normal'
                
                # Handle parcelas for Material Escolar
                parcelas_total = None
                parcela_atual = None
                if 'material escolar' in descricao and '/' in descricao:
                    try:
                        parcela_info = descricao.split('/')[-1].strip()
                        parcela_atual = int(parcela_info)
                        parcelas_total = 10  # Assuming 10 parcels as per existing data
                        tipo = 'parcelada'
                    except ValueError:
                        logger.warning(f"Invalid parcel info in row {index}: {descricao}")
                
                nova_despesa = {
                    'id': current_id + 1,
                    'data': date_str,
                    'descricao': str(row['expense']),
                    'valor': float(row['amount_paid']),
                    'pagador': str(row['who_paid']).lower(),
                    'categoria': categoria,
                    'tipo': tipo,
                    'parcelas_total': parcelas_total,
                    'parcela_atual': parcela_atual,
                    'recorrente_ate': '2025-12-31' if tipo == 'recorrente' else None,
                    'status': 'validado',
                    'anexo': None,
                    'validado_por': str(row['who_paid']).lower()
                }
                
                despesas.append(nova_despesa)
                current_id += 1
                logger.debug(f"Added expense from row {index}: {nova_despesa['descricao']}")
            
            except Exception as e:
                logger.error(f"Error processing row {index}: {e}")
                continue
        
        # Save new expenses, overwriting existing file
        save_json_file('data/despesas.json', despesas)
        logger.info(f"Imported {len(despesas)} expenses to despesas.json")
        
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")

# Initialize data files
def init_data_files():
    """Initialize default data files if they don't exist"""
    logger.debug("Initializing data files")
    
    # Users data
    usuarios_default = {
        "leonardo": {"tipo": "pai", "senha": "leo123"},
        "taciana": {"tipo": "mae", "senha": "taci123"},
        "theo": {"tipo": "menor", "senha": "theo2025"}
    }
    
    usuarios = load_json_file('data/usuarios.json', usuarios_default)
    save_json_file('data/usuarios.json', usuarios)
    
    # Calendar data
    calendario = load_json_file('data/calendario.json', {})
    save_json_file('data/calendario.json', calendario)
    
    # Expenses data (reset and import from Excel)
    save_json_file('data/despesas.json', [])  # Zero out despesas.json
    import_excel_data()

init_data_files()

# ... (restante do app.py permanece igual ao fornecido anteriormente, incluindo rotas para login, calendario, conta, APIs, upload, e exportação)
```

### Passos para Resolver
1. **Atualize o `app.py`**:
   - Substitua o `app.py` no projeto Render pelo código acima, que inclui logs detalhados.
   - Os logs ajudarão a identificar se o Excel está sendo encontrado, lido corretamente, e quais linhas estão sendo processadas ou ignoradas.

2. **Confirme o `requirements.txt`**:
   - Certifique-se de que contém:
     ```
     flask>=3.1.1
     werkzeug>=3.1.3
     pandas>=2.2.2
     openpyxl>=3.1.2
     gunicorn>=20.1.0
     ```
   - No Render, após atualizar o `requirements.txt`, force um redeploy para reinstalar as dependências.

3. **Verifique o Excel**:
   - Confirme que o arquivo está na raiz do projeto (ex.: `/Financial Records Excel (version 1).xlsx`).
   - Abra o Excel localmente e verifique:
     - As primeiras 65 linhas podem ser cabeçalhos ou metadados (o código pula essas linhas com `skiprows=65`).
     - As colunas `day`, `month`, `year`, `expense`, `amount_paid`, `who_paid` existem após a linha 65.
     - Se possível, compartilhe as primeiras linhas de dados (após a linha 65) ou a estrutura das colunas para confirmar se o `skiprows=65` é adequado.

4. **Deploy no Render**:
   - Faça upload do `app.py` atualizado, do Excel, e de outros arquivos necessários (`templates/`, `static/`, `data/` com `calendario.json` e `usuarios.json`).
   - Configure o comando de inicialização: `gunicorn app:app`.
   - Deploy o projeto.

5. **Consulte os Logs no Render**:
   - Após o deploy, acesse o painel do Render e vá para a seção de **Logs**.
   - Procure por mensagens de depuração como:
     - `Checking for Excel file: Financial Records Excel (version 1).xlsx`
     - `Excel file not found: ...`
     - `Excel rows read: <número>`
     - `Added expense from row <índice>: <descrição>`
     - `Imported <número> expenses to despesas.json`
     - Ou erros como `Error reading Excel file: ...` ou `Error processing row <índice>: ...`.
   - Compartilhe os logs relevantes para identificar o problema exato.

6. **Teste a Tela "Conta Corrente"**:
   - Acesse o aplicativo, faça login (ex.: `leonardo`, senha `leo123`), e vá para `/conta`.
   - Verifique se a tabela de despesas está vazia ou contém dados inesperados. Se vazia, os logs indicarão por que a importação falhou.

### Se o Problema Persistir
- **Estrutura do Excel**: Se o `skiprows=65` for incorreto ou as colunas não corresponderem, a leitura falhará. Compartilhe a estrutura do Excel (ex.: nomes das colunas após a linha 65) para ajustar o código.
- **Permissões no Render**: Confirme que a pasta `data` tem permissões de escrita (o Render geralmente gerencia isso automaticamente, mas vale verificar).
- **Teste Local**: Execute o aplicativo localmente (`python app.py`) com o Excel na raiz e verifique os logs no terminal. Isso pode revelar erros que não aparecem no Render.

### Alternativa: Carga Manual via Tela
Se a carga automática continuar falhando, você pode preferir a carga manual via uma tela, conforme sugerido anteriormente. Posso fornecer o código completo para adicionar um formulário de upload em `conta.html` e uma rota `/upload_excel`. Indique se deseja essa solução.

### Próximos Passos
- Atualize o `app.py` com os logs e redeploy.
- Compartilhe:
  - Os logs do Render após o deploy.
  - A estrutura do Excel (colunas e algumas linhas após a linha 65).
  - Qualquer mensagem de erro observada.
- Com essas informações, posso ajustar o código ou sugerir uma correção específica.

Desculpe pelo inconveniente! Vamos resolver isso rapidamente.
