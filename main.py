
from app import app

if __name__ == '__main__':
    print("Iniciando aplicação Flask...")
    app.run(host='0.0.0.0', port=5000, debug=True)
