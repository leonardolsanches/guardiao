import os
import json
import re
from datetime import datetime

def import_json_data():
    """Import historical data from JSON file"""
    json_file = '../data/despesas_novo.json'

    if not os.path.exists(json_file):
        print(f"❌ Arquivo JSON não encontrado: {json_file}")
        return []

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix commas in decimal numbers (e.g., 200,00 -> 200.00)
        content = re.sub(r'(\d+),(\d{2})(?=[,\n\s])', r'\1.\2', content)

        data = json.loads(content)

        if not isinstance(data, list):
            print("❌ JSON não contém uma lista de despesas")
            return []

        despesas = []
        for item in data:
            try:
                formatted_date = item['data']
                valor = float(item['valor'])

                nova_despesa = {
                    'data': formatted_date,
                    'descricao': item['descricao'],
                    'categoria': item['categoria'],
                    'valor': valor,
                    'pagador': item['pagador'],
                    'status': item['status'],
                    'validado_por': item['validado_por']
                }
                despesas.append(nova_despesa)
            except KeyError as e:
                print(f"❌ Campo faltando no item: {e}")
            except ValueError as e:
                print(f"❌ Erro ao converter valor: {e}")

        os.makedirs('../data', exist_ok=True)
        save_json_file('../data/despesas.json', despesas)
        print(f"✅ {len(despesas)} despesas carregadas com sucesso!")
        return despesas

    except json.JSONDecodeError as e:
        print(f"❌ Erro no JSON na linha {e.lineno}, coluna {e.colno}: {e.msg}")
        return []
    except Exception as e:
        print(f"❌ Erro ao processar o arquivo JSON: {e}")
        return []

def save_json_file(filename, data):
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import_json_data()