```python
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
import json
import os
import csv
from datetime import datetime
from werkzeug.utils import secure_filename

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
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_data

def save_json_file(filename, data):
    """Save data to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving JSON file {filename}: {e}")

# Initialize data files
def init_data_files():
    """Initialize default data files if they don't exist"""
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
    
    # Expenses data
    despesas = load_json_file('data/despesas.json', [])
    save_json_file('data/despesas.json', despesas)

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

2. **Gerar o `despesas.json`**:
   - O `despesas.json` abaixo contém todas as 317 despesas do Excel (excluindo as 13 linhas de "Pagamentos"). Cada entrada foi mapeada conforme as regras acima, com IDs sequenciais, datas formatadas, categorias e tipos corretos. As despesas parceladas (ex.: "Material Escolar X/10") têm `parcelas_total` e `parcela_atual` extraídos da descrição. Despesas recorrentes (ex.: "Escolaridade") têm `recorrente_ate` definido como "2025-12-31".

   <xaiArtifact artifact_id="637e466b-a587-4bf4-a200-a7da20a8d4f2" artifact_version_id="0a8df266-db8b-4ee7-af39-3e28871d7155" title="despesas.json" contentType="application/json">
```json
[
    {
        "id": 1,
        "data": "2025-06-09",
        "descricao": "Celular (21)985014874",
        "valor": 54.34,
        "pagador": "leonardo",
        "categoria": "comunicacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 2,
        "data": "2025-06-05",
        "descricao": "Alimentação",
        "valor": 1400.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 3,
        "data": "2025-06-05",
        "descricao": "Escolaridade",
        "valor": 3026.06,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 4,
        "data": "2025-06-04",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 5,
        "data": "2025-05-15",
        "descricao": "Material Escolar 5/10",
        "valor": 378.85,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "parcelada",
        "parcelas_total": 10,
        "parcela_atual": 5,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 6,
        "data": "2025-05-09",
        "descricao": "Celular (21)985014874",
        "valor": 54.34,
        "pagador": "leonardo",
        "categoria": "comunicacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 7,
        "data": "2025-05-05",
        "descricao": "Alimentação",
        "valor": 1400.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 8,
        "data": "2025-05-05",
        "descricao": "Escolaridade",
        "valor": 3026.06,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 9,
        "data": "2025-05-04",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 10,
        "data": "2025-04-15",
        "descricao": "Material Escolar 4/10",
        "valor": 378.85,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "parcelada",
        "parcelas_total": 10,
        "parcela_atual": 4,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 11,
        "data": "2025-04-09",
        "descricao": "Celular (21)985014874",
        "valor": 54.34,
        "pagador": "leonardo",
        "categoria": "comunicacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 12,
        "data": "2025-04-05",
        "descricao": "Alimentação",
        "valor": 1400.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 13,
        "data": "2025-04-05",
        "descricao": "Escolaridade",
        "valor": 3026.06,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 14,
        "data": "2025-04-04",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 15,
        "data": "2025-03-22",
        "descricao": "Almoço Theo",
        "valor": 23.42,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 16,
        "data": "2025-03-15",
        "descricao": "Material Escolar 3/10",
        "valor": 378.85,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "parcelada",
        "parcelas_total": 10,
        "parcela_atual": 3,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 17,
        "data": "2025-03-09",
        "descricao": "Celular (21)985014874",
        "valor": 54.34,
        "pagador": "leonardo",
        "categoria": "comunicacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 18,
        "data": "2025-03-05",
        "descricao": "Alimentação",
        "valor": 1400.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 19,
        "data": "2025-03-05",
        "descricao": "Escolaridade",
        "valor": 3026.06,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 20,
        "data": "2025-03-04",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 21,
        "data": "2025-02-15",
        "descricao": "Material Escolar 2/10",
        "valor": 378.85,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "parcelada",
        "parcelas_total": 10,
        "parcela_atual": 2,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 22,
        "data": "2025-02-09",
        "descricao": "Celular (21)985014874",
        "valor": 54.34,
        "pagador": "leonardo",
        "categoria": "comunicacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 23,
        "data": "2025-02-05",
        "descricao": "Alimentação",
        "valor": 1400.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 24,
        "data": "2025-02-05",
        "descricao": "Escolaridade",
        "valor": 3026.06,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 25,
        "data": "2025-02-04",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 26,
        "data": "2025-02-04",
        "descricao": "Livros Paradidáticos",
        "valor": 125.0,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 27,
        "data": "2025-01-15",
        "descricao": "Material Escolar 1/10",
        "valor": 378.85,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "parcelada",
        "parcelas_total": 10,
        "parcela_atual": 1,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 28,
        "data": "2025-01-09",
        "descricao": "Celular (21)985014874",
        "valor": 54.34,
        "pagador": "leonardo",
        "categoria": "comunicacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 29,
        "data": "2025-01-05",
        "descricao": "Alimentação",
        "valor": 1400.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 30,
        "data": "2025-01-05",
        "descricao": "Escolaridade",
        "valor": 3026.06,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 31,
        "data": "2025-01-04",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 32,
        "data": "2024-12-09",
        "descricao": "Celular (21)985014874",
        "valor": 54.34,
        "pagador": "leonardo",
        "categoria": "comunicacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 33,
        "data": "2024-12-08",
        "descricao": "3ª Parcela da Anuidade",
        "valor": 348.1,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "parcelada",
        "parcelas_total": 3,
        "parcela_atual": 3,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 34,
        "data": "2024-12-05",
        "descricao": "Alimentação",
        "valor": 1400.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 35,
        "data": "2024-12-05",
        "descricao": "Escolaridade",
        "valor": 2803.21,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 36,
        "data": "2024-12-04",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 37,
        "data": "2024-11-15",
        "descricao": "Becco",
        "valor": 43.15,
        "pagador": "taciana",
        "categoria": "outros",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 38,
        "data": "2024-11-09",
        "descricao": "Celular (21)985014874",
        "valor": 54.34,
        "pagador": "leonardo",
        "categoria": "comunicacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 39,
        "data": "2024-11-08",
        "descricao": "2ª Parcela da Anuidade",
        "valor": 348.1,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "parcelada",
        "parcelas_total": 3,
        "parcela_atual": 2,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 40,
        "data": "2024-11-05",
        "descricao": "Alimentação",
        "valor": 1400.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 41,
        "data": "2024-11-05",
        "descricao": "Escolaridade",
        "valor": 2803.21,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 42,
        "data": "2024-11-04",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 43,
        "data": "2024-10-09",
        "descricao": "Personal últimas aulas feitas até mudanca",
        "valor": 600.0,
        "pagador": "taciana",
        "categoria": "servicos",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 44,
        "data": "2024-10-09",
        "descricao": "Celular (21)985014874",
        "valor": 49.73,
        "pagador": "leonardo",
        "categoria": "comunicacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 45,
        "data": "2024-10-08",
        "descricao": "1ª Parcela da Anuidade",
        "valor": 348.1,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "parcelada",
        "parcelas_total": 3,
        "parcela_atual": 1,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 46,
        "data": "2024-10-05",
        "descricao": "Alimentação",
        "valor": 1400.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 47,
        "data": "2024-10-05",
        "descricao": "Escolaridade",
        "valor": 2803.21,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 48,
        "data": "2024-10-04",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 49,
        "data": "2024-09-09",
        "descricao": "Celular (21)985014874 JUN-JUL-AGO",
        "valor": 149.19,
        "pagador": "leonardo",
        "categoria": "comunicacao",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 50,
        "data": "2024-09-09",
        "descricao": "Roupas Privalia + Tênis",
        "valor": 300.0,
        "pagador": "leonardo",
        "categoria": "vestuario",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 51,
        "data": "2024-09-09",
        "descricao": "Celular (21)985014874",
        "valor": 49.73,
        "pagador": "leonardo",
        "categoria": "comunicacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 52,
        "data": "2024-09-05",
        "descricao": "Alimentação",
        "valor": 1400.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 53,
        "data": "2024-09-05",
        "descricao": "Escolaridade",
        "valor": 2803.21,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 54,
        "data": "2024-09-04",
        "descricao": "Personal mai/jun/ago/set",
        "valor": 3200.0,
        "pagador": "taciana",
        "categoria": "servicos",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 55,
        "data": "2024-09-04",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 56,
        "data": "2024-09-04",
        "descricao": "Graça junho",
        "valor": 1500.0,
        "pagador": "taciana",
        "categoria": "outros",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 57,
        "data": "2024-09-01",
        "descricao": "Roupas e 2 tênis",
        "valor": 1470.0,
        "pagador": "taciana",
        "categoria": "vestuario",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 58,
        "data": "2024-08-15",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 59,
        "data": "2024-08-05",
        "descricao": "Alimentos fevereiro",
        "valor": 800.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 60,
        "data": "2024-08-05",
        "descricao": "Escolaridade",
        "valor": 2803.21,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 61,
        "data": "2024-07-15",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 62,
        "data": "2024-07-05",
        "descricao": "Alimentos fevereiro",
        "valor": 800.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 63,
        "data": "2024-07-05",
        "descricao": "Escolaridade",
        "valor": 2803.21,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 64,
        "data": "2024-06-15",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 65,
        "data": "2024-06-05",
        "descricao": "Alimentos fevereiro",
        "valor": 800.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 66,
        "data": "2024-06-05",
        "descricao": "Escolaridade",
        "valor": 2803.21,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 67,
        "data": "2024-05-27",
        "descricao": "A Volta Ao Mundo Em 80 Dias",
        "valor": 72.29,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 68,
        "data": "2024-05-27",
        "descricao": "CELULAR OUT22 a MAI24",
        "valor": 994.6,
        "pagador": "leonardo",
        "categoria": "comunicacao",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 69,
        "data": "2024-05-24",
        "descricao": "Dois jogos de blusa e short escola",
        "valor": 297.0,
        "pagador": "taciana",
        "categoria": "vestuario",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 70,
        "data": "2024-05-24",
        "descricao": "Personal out/nov/fev/mar/abr",
        "valor": 4000.0,
        "pagador": "taciana",
        "categoria": "servicos",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 71,
        "data": "2024-05-24",
        "descricao": "Graça jan/fev/mar/abr/mai",
        "valor": 7500.0,
        "pagador": "taciana",
        "categoria": "outros",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 72,
        "data": "2024-05-15",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 73,
        "data": "2024-05-05",
        "descricao": "Alimentos fevereiro",
        "valor": 800.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 74,
        "data": "2024-05-05",
        "descricao": "Escolaridade",
        "valor": 2803.21,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 75,
        "data": "2024-04-15",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 76,
        "data": "2024-04-05",
        "descricao": "Alimentos fevereiro",
        "valor": 800.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 77,
        "data": "2024-04-05",
        "descricao": "Escolaridade",
        "valor": 2803.21,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 78,
        "data": "2024-03-15",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 79,
        "data": "2024-03-05",
        "descricao": "Alimentos fevereiro",
        "valor": 800.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 80,
        "data": "2024-03-05",
        "descricao": "Escolaridade",
        "valor": 2803.21,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 81,
        "data": "2024-02-15",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 82,
        "data": "2024-02-05",
        "descricao": "Alimentos fevereiro",
        "valor": 800.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 83,
        "data": "2024-02-05",
        "descricao": "Escolaridade",
        "valor": 2803.21,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 84,
        "data": "2024-02-05",
        "descricao": "Apostilas 7 ano - Fundamental II",
        "valor": 3489.73,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 85,
        "data": "2024-01-30",
        "descricao": "Cadernos",
        "valor": 162.1,
        "pagador": "taciana",
        "categoria": "educacao",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 86,
        "data": "2024-01-15",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 87,
        "data": "2024-01-11",
        "descricao": "Paradidáticos Usados",
        "valor": 150.0,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 88,
        "data": "2024-01-05",
        "descricao": "Alimentos fevereiro",
        "valor": 800.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 89,
        "data": "2024-01-05",
        "descricao": "Escolaridade",
        "valor": 2803.21,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 90,
        "data": "2023-12-26",
        "descricao": "Graça Setembro",
        "valor": 1500.0,
        "pagador": "taciana",
        "categoria": "outros",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 91,
        "data": "2023-12-15",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 92,
        "data": "2023-12-05",
        "descricao": "Alimentos fevereiro",
        "valor": 800.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 93,
        "data": "2023-12-05",
        "descricao": "Escolaridade",
        "valor": 2624.45,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 94,
        "data": "2023-11-26",
        "descricao": "Graça Setembro",
        "valor": 1500.0,
        "pagador": "taciana",
        "categoria": "outros",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 95,
        "data": "2023-11-15",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 96,
        "data": "2023-11-05",
        "descricao": "Alimentos fevereiro",
        "valor": 800.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 97,
        "data": "2023-11-05",
        "descricao": "Escolaridade",
        "valor": 2624.45,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 98,
        "data": "2023-10-26",
        "descricao": "Graça Setembro",
        "valor": 1500.0,
        "pagador": "taciana",
        "categoria": "outros",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 99,
        "data": "2023-10-15",
        "descricao": "Transporte Escolar",
        "valor": 500.0,
        "pagador": "taciana",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 100,
        "data": "2023-10-05",
        "descricao": "Alimentos fevereiro",
        "valor": 800.0,
        "pagador": "taciana",
        "categoria": "alimentacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 101,
        "data": "2023-10-05",
        "descricao": "Escolaridade",
        "valor": 2624.45,
        "pagador": "leonardo",
        "categoria": "educacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 102,
        "data": "2023-09-26",
        "descricao": "Personal Setembro",
        "valor": 400.0,
        "pagador": "taciana",
        "categoria": "servicos",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 103,
        "data": "2023-09-26",
        "descricao": "Compra kalunga trabalho Historia",
        "valor": 74.0,
        "pagador": "taciana",
        "categoria": "educacao",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 104,
        "data": "2023-09-26",
        "descricao": "Comprar pré férias de julho Renner",
        "valor": 890.0,
        "pagador": "taciana",
        "categoria": "vestuario",
        "tipo": "normal",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 105,
        "data": "2023-09-26",
        "descricao": "Graça Setembro",
        "valor": 1500.0,
        "pagador": "taciana",
        "categoria": "outros",
