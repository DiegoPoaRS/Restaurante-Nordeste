import bcrypt
from jose import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Header

SECRET_KEY = "sua_chave_secreta_super_segura_aqui" # Em produção
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def get_password_hash(password: str) -> str:

    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:

    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_bytes)

def create_access_token(data: dict):

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_token_payload(authorization: str = Header(default=None)):

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou formato inválido. Use 'Bearer <token>'.")
    
    token = authorization.split(" ")[1]
    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

def verificar_admin(payload: dict = Depends(get_token_payload)):
    if payload.get("tipo") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas usuários ADMIN podem realizar esta ação.")
    return payload