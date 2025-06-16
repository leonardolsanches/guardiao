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

#### 2. `despesas.json` (com dados simulados do Excel)
Como os dados exatos do `Financial Records Excel (version 1).xlsx` não foram fornecidos, gerei um `despesas.json` com exemplos baseados nas descrições anteriores (ex.: despesas de escolaridade, material escolar, alimentação) e no mapeamento de categorias/tipos definido no `app.py` original. O arquivo inclui:
- Despesas com IDs sequenciais.
- Formato de data `YYYY-MM-DD`.
- Categorias mapeadas (ex.: "escolaridade" → "educacao").
- Tipos (`recorrente`, `parcelada`, `normal`).
- Parcelas para "material escolar" (assumindo 10 parcelas).
- Status "validado" e campos `anexo` como `null`.

Se você fornecer linhas específicas do Excel, posso gerar um `despesas.json` mais preciso.

<xaiArtifact artifact_id="e7191fbc-194d-413a-840f-b19f982e8d9e" artifact_version_id="4fe84db6-d0fa-4962-88bb-dedda8439193" title="despesas.json" contentType="application/json">
```json
[
    {
        "id": 1,
        "data": "2025-01-10",
        "descricao": "Mensalidade Escolaridade",
        "valor": 1200.00,
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
        "id": 2,
        "data": "2025-01-15",
        "descricao": "Material Escolar 1/10",
        "valor": 150.00,
        "pagador": "taciana",
        "categoria": "educacao",
        "tipo": "parcelada",
        "parcelas_total": 10,
        "parcela_atual": 1,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 3,
        "data": "2025-02-15",
        "descricao": "Material Escolar 2/10",
        "valor": 150.00,
        "pagador": "taciana",
        "categoria": "educacao",
        "tipo": "parcelada",
        "parcelas_total": 10,
        "parcela_atual": 2,
        "recorrente_ate": null,
        "status": "validado",
        "anexo": null,
        "validado_por": "taciana"
    },
    {
        "id": 4,
        "data": "2025-01-20",
        "descricao": "Transporte Escolar",
        "valor": 300.00,
        "pagador": "leonardo",
        "categoria": "transporte",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    },
    {
        "id": 5,
        "data": "2025-01-25",
        "descricao": "Almoço Escolar",
        "valor": 50.00,
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
        "id": 6,
        "data": "2025-02-01",
        "descricao": "Plano de Saúde",
        "valor": 500.00,
        "pagador": "leonardo",
        "categoria": "saude",
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
        "data": "2025-02-05",
        "descricao": "Tênis Novo",
        "valor": 200.00,
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
        "id": 8,
        "data": "2025-02-10",
        "descricao": "Recarga Celular",
        "valor": 30.00,
        "pagador": "leonardo",
        "categoria": "comunicacao",
        "tipo": "recorrente",
        "parcelas_total": null,
        "parcela_atual": null,
        "recorrente_ate": "2025-12-31",
        "status": "validado",
        "anexo": null,
        "validado_por": "leonardo"
    }
]
```

### Instruções para Upload e Deploy
1. **Atualize o Repositório GitHub**:
   - No repositório `leonardolsanches/guardiao`, substitua o `app.py` pelo código acima.
   - Adicione o `despesas.json` na pasta `data` (`/data/despesas.json`).
   - Remova o `Financial Records Excel (version 1).xlsx` da raiz, já que não será mais usado.
   - Confirme que os outros arquivos estão corretos:
     - `/templates/index.html`, `/templates/calendario.html`, `/templates/conta.html`
     - `/static/style.css`, `/static/script.js`
     - `/data/calendario.json`, `/data/usuarios.json`
   - Atualize o `requirements.txt` para remover dependências desnecessárias:
     ```
     flask>=3.1.1
     werkzeug>=3.1.3
     gunicorn>=20.1.0
     ```
   - Commit e push as alterações:
     ```bash
     git add app.py data/despesas.json requirements.txt
     git rm "Financial Records Excel (version 1).xlsx"
     git commit -m "Remove Excel import, add despesas.json with preloaded data"
     git push origin main
     ```

2. **Confirme a Configuração no Render**:
   - No painel do Render, verifique que o comando de inicialização é:
     ```
     gunicorn app:app
     ```
   - Certifique-se de que o branch configurado é `main`.

3. **Redeploy no Render**:
   - Acione um redeploy manual no Render para puxar as alterações.
   - Monitore os logs do deploy para confirmar que não há erros de sintaxe e que o aplicativo inicia corretamente.

4. **Teste o Aplicativo**:
   - Acesse o aplicativo, faça login (ex.: `leonardo`, senha `leo123`), e vá para a tela **"Conta Corrente"** (`/conta`).
   - Verifique se as despesas do `despesas.json` aparecem na tabela, organizadas por mês.
   - Teste a adição de novas despesas via interface para confirmar que o `despesas.json` é atualizado corretamente.

### Observações sobre o `despesas.json`
- O `despesas.json` acima é baseado em exemplos genéricos, já que os dados exatos do Excel não foram fornecidos. Ele inclui 8 despesas variadas para teste.
- Se você compartilhar linhas específicas do Excel (ex.: `day`, `month`, `year`, `expense`, `amount_paid`, `who_paid`), posso gerar um `despesas.json` com os dados exatos.
- O arquivo respeita o mapeamento de categorias e tipos definido anteriormente (ex.: "material escolar" como `parcelada`, "escolaridade" como `recorrente`).

### Próximos Passos
- Faça upload do `app.py` e `despesas.json` no repositório e remova o Excel.
- Redeploy no Render e compartilhe os logs se houver erros.
- Se desejar um `despesas.json` com dados específicos do Excel, envie algumas linhas de exemplo.
- Caso queira adicionar uma funcionalidade para upload manual de Excel no futuro, posso fornecer o código.

Desculpe pelos problemas com a importação automática! Essa abordagem com o `despesas.json` pré-carregado deve simplificar o deploy e resolver o problema.
