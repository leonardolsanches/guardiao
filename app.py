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

@app.route('/')
def index():
    """Login page"""
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    """Handle login authentication"""
    usuario = request.form.get('usuario', '').lower()
    senha = request.form.get('senha', '')
    
    usuarios = load_json_file('data/usuarios.json')
    
    if usuario in usuarios and usuarios[usuario]['senha'] == senha:
        session['usuario'] = usuario
        session['tipo'] = usuarios[usuario]['tipo']
        return redirect(url_for('calendario'))
    
    return render_template('index.html', erro='Usuário ou senha inválidos')

@app.route('/logout')
def logout():
    """Handle logout"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/calendario')
def calendario():
    """Calendar page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('calendario.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/conta')
def conta():
    """Financial account page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('conta.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/api/calendario/<int:ano>/<int:mes>')
def api_calendario(ano, mes):
    """API endpoint to get calendar data for specific month"""
    calendario = load_json_file('data/calendario.json')
    
    # Filter data for the requested month
    mes_data = {}
    for data, info in calendario.items():
        if data.startswith(f"{ano:04d}-{mes:02d}"):
            mes_data[data] = info
    
    return jsonify(mes_data)

@app.route('/api/calendario/salvar', methods=['POST'])
def api_calendario_salvar():
    """API endpoint to save calendar data"""
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    data = request.json
    calendario = load_json_file('data/calendario.json')
    
    data_str = data['data']
    calendario[data_str] = {
        'responsavel': data['responsavel'],
        'tipo': data.get('tipo', 'planejado'),
        'observacao': data.get('observacao', '')
    }
    
    save_json_file('data/calendario.json', calendario)
    return jsonify({'sucesso': True})

@app.route('/api/despesas')
def api_despesas():
    """API endpoint to get expenses data"""
    despesas = load_json_file('data/despesas.json', [])
    return jsonify(despesas)

@app.route('/api/despesas/salvar', methods=['POST'])
def api_despesas_salvar():
    """API endpoint to save expense data"""
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    data = request.json
    despesas = load_json_file('data/despesas.json', [])
    
    # Generate new ID
    novo_id = max([d.get('id', 0) for d in despesas], default=0) + 1
    
    # Auto-validar despesas recorrentes
    status = 'validado' if data.get('auto_validar') else 'pendente'
    validado_por = session['usuario'] if data.get('auto_validar') else None
    
    nova_despesa = {
        'id': novo_id,
        'data': data['data'],
        'descricao': data['descricao'],
        'valor': float(data['valor']),
        'pagador': data['pagador'],
        'categoria': data['categoria'],
        'tipo': data['tipo'],
        'parcelas_total': data.get('parcelas_total'),
        'parcela_atual': data.get('parcela_atual'),
        'recorrente_ate': data.get('recorrente_ate'),
        'status': status,
        'anexo': data.get('anexo'),
        'validado_por': validado_por
    }
    
    despesas.append(nova_despesa)
    save_json_file('data/despesas.json', despesas)
    
    return jsonify({'sucesso': True, 'id': novo_id})

@app.route('/api/despesas/validar/<int:despesa_id>', methods=['POST'])
def api_despesas_validar(despesa_id):
    """API endpoint to validate expense"""
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    despesas = load_json_file('data/despesas.json', [])
    
    for despesa in despesas:
        if despesa['id'] == despesa_id:
            despesa['status'] = 'validado'
            despesa['validado_por'] = session['usuario']
            break
    
    save_json_file('data/despesas.json', despesas)
    return jsonify({'sucesso': True})

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload for expense attachments"""
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    if 'arquivo' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo selecionado'})
    
    file = request.files['arquivo']
    if file.filename == '':
        return jsonify({'erro': 'Nenhum arquivo selecionado'})
    
    if file:
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'sucesso': True, 'filename': filename})

# Export routes for Power BI integration
@app.route('/export/despesas.csv')
def export_despesas_csv():
    """Export expenses to CSV for Power BI"""
    despesas = load_json_file('data/despesas.json', [])
    
    csv_filename = 'export/despesas.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        if despesas:
            fieldnames = despesas[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(despesas)
    
    return send_file(csv_filename, as_attachment=True, download_name='despesas.csv')

@app.route('/export/calendario.csv')
def export_calendario_csv():
    """Export calendar to CSV for Power BI"""
    calendario = load_json_file('data/calendario.json', {})
    
    csv_filename = 'export/calendario.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['data', 'responsavel', 'tipo', 'observacao']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for data, info in calendario.items():
            row = {
                'data': data,
                'responsavel': info.get('responsavel', ''),
                'tipo': info.get('tipo', ''),
                'observacao': info.get('observacao', '')
            }
            writer.writerow(row)
    
    return send_file(csv_filename, as_attachment=True, download_name='calendario.csv')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

2. **Atualize o Repositório GitHub**:
   - No repositório `leonardolsanches/guardiao`, substitua o `app.py` existente pelo código acima.
   - Certifique-se de que os outros arquivos estão corretos:
     - `/templates/index.html`, `/templates/calendario.html`, `/templates/conta.html` (use as versões corrigidas fornecidas anteriormente).
     - `/static/style.css`, `/static/script.js`.
     - `/data/calendario.json`, `/data/usuarios.json`.
     - `/Financial Records Excel (version 1).xlsx` na raiz.
     - `/requirements.txt` com:
       ```
       flask>=3.1.1
       werkzeug>=3.1.3
       pandas>=2.2.2
       openpyxl>=3.1.2
       gunicorn>=20.1.0
       ```
   - Commit e push as alterações:
     ```bash
     git add app.py requirements.txt
     git commit -m "Corrige app.py removendo marcações Markdown e mantém logs"
     git push origin main
     ```

3. **Confirme o Comando de Inicialização no Render**:
   - No painel do Render, verifique que o comando de inicialização está configurado como:
     ```
     gunicorn app:app
     ```
   - Se estiver diferente, atualize nas configurações do serviço.

4. **Redeploy no Render**:
   - No painel do Render, acione um redeploy manual para puxar as alterações do commit mais recente (`main` branch, commit `42060430296ebed7233adb74a280755a09d6a8b0` ou posterior).
   - Monitore os logs do deploy para confirmar que não há erros de sintaxe.

5. **Verifique a Carga do Excel**:
   - Após o deploy, acesse os logs do Render e procure por mensagens como:
     - `Checking for Excel file: Financial Records Excel (version 1).xlsx`
     - `Excel rows read: <número>`
     - `Imported <número> expenses to despesas.json`
     - Ou erros como `Excel file not found` ou `Error reading Excel file`.
   - Acesse o aplicativo, faça login (ex.: `leonardo`, senha `leo123`), e vá para a tela **"Conta Corrente"** (`/conta`) para verificar se as despesas do Excel foram carregadas.

### Resolvendo o Problema de Carga do Excel
Se, após corrigir o `app.py`, os dados do Excel ainda não carregarem:
- **Confirme o Excel**:
  - Verifique se `Financial Records Excel (version 1).xlsx` está na raiz do repositório GitHub e foi incluído no commit.
  - Confirme que o arquivo tem as colunas `day`, `month`, `year`, `expense`, `amount_paid`, `who_paid` após a linha 65 (devido a `skiprows=65`).
  - Se possível, compartilhe a estrutura do Excel (nomes das colunas e algumas linhas após a linha 65) para ajustar o `skiprows` ou o mapeamento de colunas.

- **Cheque os Logs**:
  - Os logs do Render mostrarão se o Excel foi encontrado e quantas linhas foram lidas. Compartilhe os logs relevantes para diagnosticar.

- **Teste Local**:
  - Clone o repositório localmente:
    ```bash
    git clone https://github.com/leonardolsanches/guardiao
    cd guardiao
    ```
  - Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
  - Coloque o Excel na raiz e execute:
    ```bash
    python app.py
    ```
  - Verifique os logs no terminal para mensagens de depuração.

### Se Precisar de Carga Manual
Se preferir evitar a carga automática e adicionar uma tela para upload manual do Excel, posso fornecer o código para um formulário em `conta.html` e uma rota `/upload_excel`. Indique se deseja essa funcionalidade.

### Próximos Passos
- Atualize o `app.py` no repositório GitHub e faça o push.
- Redeploy no Render e compartilhe os novos logs se houver erros ou se o Excel não carregar.
- Forneça a estrutura do Excel para confirmar o `skiprows=65` e o mapeamento de colunas.

Desculpe pela confusão com o Markdown! Com essas correções, o deploy deve funcionar, e podemos resolver a carga do Excel.
