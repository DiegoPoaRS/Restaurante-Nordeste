from jose import JWTError, jwt
from security import SECRET_KEY, ALGORITHM, get_password_hash, verify_password, create_access_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from database import engine, get_db, Base
from models import Usuario, ItemCardapio, Pedido, CanalPedidoEnum, ItemPedido
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from schemas import (
    UsuarioCreate, UsuarioResponse, LoginRequest,
    ItemCardapioResponse, PedidoCreate, PedidoResponse
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Restaurante - Projeto Extensionista II", version="1.0.0")

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):

    error_name = "ERRO_DE_REQUISICAO"
    if exc.status_code == 401:
        error_name = "CREDENCIAIS_INVALIDAS"
    elif exc.status_code == 403:
        error_name = "ACESSO_NEGADO"
    elif exc.status_code == 404:
        error_name = "NAO_ENCONTRADO"
    elif exc.status_code == 409:
        error_name = "CONFLITO_REGRA_NEGOCIO"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": error_name,
            "message": str(exc.detail),
            "details": [],
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "path": request.url.path
        }
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_usuario_atual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    credenciais_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais. Token inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credenciais_exception
    except JWTError:
        raise credenciais_exception

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None:
        raise credenciais_exception
        
    return usuario

@app.post("/auth/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    db_user = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    
    senha_criptografada = get_password_hash(usuario.senha)
    
    novo_usuario = Usuario(email=usuario.email, senha_hash=senha_criptografada, tipo=usuario.tipo)
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario


@app.post("/auth/login")

def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.senha_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")
        
    access_token = create_access_token(data={"sub": db_user.email, "tipo": db_user.tipo})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "usuario_id": db_user.id, 
        "tipo": db_user.tipo
    }
    
@app.get("/cardapio", response_model=List[ItemCardapioResponse])
def listar_cardapio(db: Session = Depends(get_db)):
    itens = db.query(ItemCardapio).filter(ItemCardapio.disponivel == 1).all()
    
    # Se o cardapio tiver vazio insere itens de exemplo
    if not itens:
        item_exemplo = ItemCardapio(nome="X-Burger Especial", descricao="Pão, carne artesanal e queijo", preco=29.90, disponivel=1)
        db.add(item_exemplo)
        db.commit()
        itens = [item_exemplo]
        
    return itens

class PagamentoMockRequest(BaseModel):
    sucesso: bool = True


@app.post("/pedidos", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def criar_pedido(
    pedido_in: PedidoCreate, 
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual) # ROTA PROTEGIDA
):
    valor_total_pedido = 0
    itens_db = []
    
    for item in pedido_in.itens:
        produto = db.query(ItemCardapio).filter(ItemCardapio.id == item.item_id).first()
        if not produto:
            raise HTTPException(status_code=404, detail=f"Produto {item.item_id} não encontrado.")
        if produto.disponivel == 0:
            raise HTTPException(status_code=409, detail=f"Produto {produto.nome} indisponível/sem estoque.")
            
        valor_total_pedido += produto.preco * item.quantidade
        
        novo_item_pedido = ItemPedido(
            item_cardapio_id=produto.id,
            quantidade=item.quantidade,
            preco_unitario=produto.preco
        )
        itens_db.append(novo_item_pedido)
        
    novo_pedido = Pedido(
        cliente_id=usuario_atual.id,
        canal_pedido=pedido_in.canal_pedido,
        valor_total=valor_total_pedido,
        status="CRIADO"
    )
    novo_pedido.itens = itens_db
    
    db.add(novo_pedido)
    db.commit()
    db.refresh(novo_pedido)
    
    return novo_pedido


@app.post("/pedidos/{pedido_id}/pagamento")
def processar_pagamento_mock(pedido_id: int, request: PagamentoMockRequest, db: Session = Depends(get_db)):

    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    
    if pedido.status != "CRIADO":
        raise HTTPException(status_code=400, detail=f"O pedido já está com status: {pedido.status}")

    if request.sucesso:
        pedido.status = "PAGO"
        db.commit()
        db.refresh(pedido)
        return {"mensagem": "Pagamento aprovado via gateway mock.", "status_pedido": pedido.status}
    else:
        pedido.status = "CANCELADO"
        db.commit()
        db.refresh(pedido)
        raise HTTPException(status_code=402, detail="Pagamento recusado pelo gateway externo. Pedido cancelado.")


@app.get("/pedidos", response_model=List[PedidoResponse])
def listar_pedidos(
    canal_pedido: Optional[CanalPedidoEnum] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual) # ROTA PROTEGIDA
):
    query = db.query(Pedido)

    if usuario_atual.tipo == "CLIENTE":
        query = query.filter(Pedido.cliente_id == usuario_atual.id)
    
    if canal_pedido:
        query = query.filter(Pedido.canal_pedido == canal_pedido)
    if status:
        query = query.filter(Pedido.status == status)
        
    return query.all()
