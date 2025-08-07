
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
    
    # New data files
    cadastro = load_json_file('data/cadastro.json', {})
    save_json_file('data/cadastro.json', cadastro)
    
    documentos = load_json_file('data/documentos.json', [])
    save_json_file('data/documentos.json', documentos)
    
    boletim = load_json_file('data/boletim.json', [])
    save_json_file('data/boletim.json', boletim)
    
    vacinacao = load_json_file('data/vacinacao.json', [])
    save_json_file('data/vacinacao.json', vacinacao)
    
    consultas = load_json_file('data/consultas.json', [])
    save_json_file('data/consultas.json', consultas)
    
    mesada = load_json_file('data/mesada.json', [])
    save_json_file('data/mesada.json', mesada)
    
    seguros = load_json_file('data/seguros.json', [])
    save_json_file('data/seguros.json', seguros)
    
    crescimento = load_json_file('data/crescimento.json', [])
    save_json_file('data/crescimento.json', crescimento)
    
    notas = load_json_file('data/notas.json', [])
    save_json_file('data/notas.json', notas)
    
    marcos = load_json_file('data/marcos.json', [])
    save_json_file('data/marcos.json', marcos)

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

@app.route('/documentos')
def documentos():
    """Child documents page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('documentos.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/cadastro')
def cadastro():
    """Child registration/profile page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('cadastro.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/boletim')
def boletim():
    """School report card page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('boletim.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/vacinacao')
def vacinacao():
    """Vaccination record page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('vacinacao.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/consultas')
def consultas():
    """Medical appointments and prescriptions page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('consultas.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/mesada')
def mesada():
    """Allowance management page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('mesada.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/seguros')
def seguros():
    """Insurance management page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('seguros.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/localizacao')
def localizacao():
    """Location tracking page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('localizacao.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/crescimento')
def crescimento():
    """Height and weight tracking page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('crescimento.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/agenda')
def agenda():
    """Schedule/agenda page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('agenda.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/calendario_escolar')
def calendario_escolar():
    """School calendar page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('calendario_escolar.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/mapa_astral')
def mapa_astral():
    """Astrological chart page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('mapa_astral.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/notas')
def notas():
    """Shared notes page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('notas.html', usuario=session['usuario'], tipo=session['tipo'])

@app.route('/marcos')
def marcos():
    """Milestones/development tracking page"""
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    return render_template('marcos.html', usuario=session['usuario'], tipo=session['tipo'])

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
    print(f"API despesas: carregando {len(despesas)} despesas")
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

# API endpoints for new features
@app.route('/api/cadastro')
def api_cadastro():
    """API endpoint to get child profile data"""
    cadastro = load_json_file('data/cadastro.json', {})
    return jsonify(cadastro)

@app.route('/api/cadastro/salvar', methods=['POST'])
def api_cadastro_salvar():
    """API endpoint to save child profile data"""
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    data = request.json
    save_json_file('data/cadastro.json', data)
    return jsonify({'sucesso': True})

@app.route('/api/documentos')
def api_documentos():
    """API endpoint to get documents data"""
    documentos = load_json_file('data/documentos.json', [])
    return jsonify(documentos)

@app.route('/api/documentos/salvar', methods=['POST'])
def api_documentos_salvar():
    """API endpoint to save document data"""
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    data = request.json
    documentos = load_json_file('data/documentos.json', [])
    novo_id = max([d.get('id', 0) for d in documentos], default=0) + 1
    data['id'] = novo_id
    documentos.append(data)
    save_json_file('data/documentos.json', documentos)
    return jsonify({'sucesso': True, 'id': novo_id})

@app.route('/api/vacinacao')
def api_vacinacao():
    """API endpoint to get vaccination data"""
    vacinacao = load_json_file('data/vacinacao.json', [])
    return jsonify(vacinacao)

@app.route('/api/vacinacao/salvar', methods=['POST'])
def api_vacinacao_salvar():
    """API endpoint to save vaccination data"""
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    data = request.json
    vacinacao = load_json_file('data/vacinacao.json', [])
    novo_id = max([v.get('id', 0) for v in vacinacao], default=0) + 1
    data['id'] = novo_id
    vacinacao.append(data)
    save_json_file('data/vacinacao.json', vacinacao)
    return jsonify({'sucesso': True, 'id': novo_id})

@app.route('/api/consultas')
def api_consultas():
    """API endpoint to get medical consultations data"""
    consultas = load_json_file('data/consultas.json', [])
    return jsonify(consultas)

@app.route('/api/consultas/salvar', methods=['POST'])
def api_consultas_salvar():
    """API endpoint to save medical consultation data"""
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    data = request.json
    consultas = load_json_file('data/consultas.json', [])
    novo_id = max([c.get('id', 0) for c in consultas], default=0) + 1
    data['id'] = novo_id
    consultas.append(data)
    save_json_file('data/consultas.json', consultas)
    return jsonify({'sucesso': True, 'id': novo_id})

@app.route('/api/crescimento')
def api_crescimento():
    """API endpoint to get growth data"""
    crescimento = load_json_file('data/crescimento.json', [])
    return jsonify(crescimento)

@app.route('/api/crescimento/salvar', methods=['POST'])
def api_crescimento_salvar():
    """API endpoint to save growth data"""
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    data = request.json
    crescimento = load_json_file('data/crescimento.json', [])
    novo_id = max([c.get('id', 0) for c in crescimento], default=0) + 1
    data['id'] = novo_id
    crescimento.append(data)
    save_json_file('data/crescimento.json', crescimento)
    return jsonify({'sucesso': True, 'id': novo_id})

@app.route('/api/notas')
def api_notas():
    """API endpoint to get shared notes data"""
    notas = load_json_file('data/notas.json', [])
    return jsonify(notas)

@app.route('/api/notas/salvar', methods=['POST'])
def api_notas_salvar():
    """API endpoint to save shared note"""
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    data = request.json
    notas = load_json_file('data/notas.json', [])
    novo_id = max([n.get('id', 0) for n in notas], default=0) + 1
    data['id'] = novo_id
    data['autor'] = session['usuario']
    data['data_criacao'] = datetime.now().isoformat()
    notas.append(data)
    save_json_file('data/notas.json', notas)
    return jsonify({'sucesso': True, 'id': novo_id})

@app.route('/api/marcos')
def api_marcos():
    """API endpoint to get milestones data"""
    marcos = load_json_file('data/marcos.json', [])
    return jsonify(marcos)

@app.route('/api/marcos/salvar', methods=['POST'])
def api_marcos_salvar():
    """API endpoint to save milestone data"""
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    data = request.json
    marcos = load_json_file('data/marcos.json', [])
    novo_id = max([m.get('id', 0) for m in marcos], default=0) + 1
    data['id'] = novo_id
    data['registrado_por'] = session['usuario']
    marcos.append(data)
    save_json_file('data/marcos.json', marcos)
    return jsonify({'sucesso': True, 'id': novo_id})

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
    print("Iniciando servidor Flask na porta 5000...")
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Erro ao iniciar o servidor: {e}")
