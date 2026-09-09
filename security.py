# security.py
import bcrypt
from jose import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Header

# Configurações do JWT
SECRET_KEY = "sua_chave_secreta_super_segura_aqui" # Em produção, use variáveis de ambiente (.env)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def get_password_hash(password: str) -> str:
    """Recebe uma senha em texto puro e retorna o hash criptografado."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto puro corresponde ao hash salvo no banco."""
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_bytes)

def create_access_token(data: dict):
    """Gera o token JWT para autenticação."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_token_payload(authorization: str = Header(default=None)):
    """Lê o token do cabeçalho da requisição e decodifica."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou formato inválido. Use 'Bearer <token>'.")
    
    token = authorization.split(" ")[1]
    try:
        # SECRET_KEY e ALGORITHM já foram definidos neste arquivo
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

def verificar_admin(payload: dict = Depends(get_token_payload)):
    """Bloqueia a requisição (Erro 403) se o usuário não for ADMIN."""
    if payload.get("tipo") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas usuários ADMIN podem realizar esta ação.")
    return payload