# Restaurante-Nordeste
Backend em Python e FastAPI que simula sistema de restaurante


##REPRODUÇÃO:

1. Fazer o clone do código (Download)

2. Criar ambiente virtual Python 3.10.2:
   - python -m venv venv
   - .\venv\Scripts\Activate
   
3. Instalar requisitos:
   - python -m pip install --upgrade pip setuptools wheel
   - pip install -r requirements.txt
   
4. Rodar Aplicação:
   - uvicorn main:app --reload
   
5. Acessar Documentação/Swagger:
   - http://127.0.0.1:8000/docs

6. Para popular o banco de dados rode:
   - python seed.py

7. O banco de dados pode ser visualizado no DB Browser for SQLite:
   - https://sqlitebrowser.org/

