
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
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
