# Restaurante-Nordeste
Backend em Python e FastAPI que simula sistema de restaurante


##REPRODUÇÃO:

1. Fazer o clone do código (Download)

2. Instalar Python 3.10.2 para windows:
   - https://www.python.org/ftp/python/3.10.2/python-3.10.2-amd64.exe

4. Criar ambiente virtual (opcional)
   - python -m venv venv
   - .\venv\Scripts\Activate
   
5. Instalar requisitos:
   - python -m pip install --upgrade pip setuptools wheel
   - pip install -r requirements.txt
   
6. Rodar Aplicação (na pasta da aplicação):
   - uvicorn main:app --reload
   
7. Acessar Documentação/Swagger:
   - http://127.0.0.1:8000/docs

8. Para popular o banco de dados rode:
   - python seed.py

9. O banco de dados pode ser visualizado no DB Browser for SQLite (necessita instalação):
   - https://sqlitebrowser.org/

