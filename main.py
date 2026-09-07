import random
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from pydantic import BaseModel
from database import engine, get_db, Base
from security import SECRET_KEY, ALGORITHM, get_password_hash, verify_password, create_access_token, verificar_admin
from models import Usuario, ItemCardapio, Pedido, CanalPedidoEnum, ItemPedido, Unidade, Estoque, StatusPedidoEnum
from schemas import (
    UsuarioCreate, UsuarioResponse, ItemCardapioResponse, PedidoCreate, 
    PedidoResponse, ItemCardapioCreate, ItemCardapioUpdate
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Raízes do Nordeste", version="1.1.0")

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):

    error_name = "ERRO_DE_REQUISICAO"
    if exc.status_code == 401: error_name = "CREDENCIAIS_INVALIDAS"
    elif exc.status_code == 403: error_name = "ACESSO_NEGADO"
    elif exc.status_code == 404: error_name = "NAO_ENCONTRADO"
    elif exc.status_code == 409: error_name = "CONFLITO_REGRA_NEGOCIO"
    elif exc.status_code == 402: error_name = "PAGAMENTO_RECUSADO"

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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

def get_usuario_atual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    credenciais_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais. Token inválido ou ausente."
    )
    if not token: raise credenciais_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise credenciais_exception
    except JWTError:
        raise credenciais_exception

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None: raise credenciais_exception
    return usuario

def get_usuario_opcional(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Identifica o usuário se houver token, mas permite continuar como Visitante se não houver."""
    if not token: return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email: return db.query(Usuario).filter(Usuario.email == email).first()
    except JWTError:
        pass
    return None

def verificar_tipo_usuario(tipos_permitidos: list[str]):
    def dependencia(usuario_atual: Usuario = Depends(get_usuario_atual)):
        if usuario_atual.tipo not in tipos_permitidos:
            raise HTTPException(status_code=403, detail="Acesso negado para o seu perfil.")
        return usuario_atual
    return dependencia

@app.post("/auth/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    if not usuario.aceite_lgpd:
        raise HTTPException(status_code=400, detail="O aceite da LGPD é obrigatório para cadastro.")
        
    db_user = db.query(Usuario).filter((Usuario.email == usuario.email) | (Usuario.cpf == usuario.cpf)).first()
    if db_user:
        raise HTTPException(status_code=409, detail="E-mail ou CPF já cadastrado no sistema.")
    
    novo_usuario = Usuario(
        nome_completo=usuario.nome_completo,
        email=usuario.email,
        senha_hash=get_password_hash(usuario.senha),
        endereco_entrega=usuario.endereco_entrega,
        telefone=usuario.telefone,
        cpf=usuario.cpf,
        data_nascimento=usuario.data_nascimento,
        aceite_lgpd=usuario.aceite_lgpd,
        tipo=usuario.tipo
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
        
    access_token = create_access_token(data={"sub": db_user.email, "tipo": db_user.tipo})
    return {"access_token": access_token, "token_type": "bearer", "usuario_id": db_user.id, "tipo": db_user.tipo}

@app.get("/unidades")
def listar_unidades(db: Session = Depends(get_db)):
    return db.query(Unidade).all()

@app.get("/cardapio", response_model=List[ItemCardapioResponse])
def listar_cardapio(db: Session = Depends(get_db)):
    ### Automação para não quebrar a aplicação ao criar banco novo:
    ### Se não existir nenhuma unidade (loja), o sistema cria a "Matriz" e um estoque de segurança automaticamente.
    unidade = db.query(Unidade).first()
    if not unidade:
        unidade = Unidade(nome="Matriz Raízes", endereco="Rua Principal, 100")
        db.add(unidade)
        db.commit()

    itens = db.query(ItemCardapio).filter(ItemCardapio.disponivel == 1).all()
    if not itens:
        item_exemplo = ItemCardapio(nome="Cuscuz Completo", descricao="Ovo, queijo e carne de sol", preco=15.90, disponivel=1)
        db.add(item_exemplo)
        db.commit()
        db.refresh(item_exemplo)
        
        estoque_exemplo = Estoque(unidade_id=unidade.id, item_cardapio_id=item_exemplo.id, quantidade=50)
        db.add(estoque_exemplo)
        db.commit()
        itens = [item_exemplo]
        
    return itens

@app.post("/cardapio", response_model=ItemCardapioResponse, status_code=status.HTTP_201_CREATED)
def criar_item_cardapio(item: ItemCardapioCreate, db: Session = Depends(get_db), admin: dict = Depends(verificar_admin)):
    novo_item = ItemCardapio(**item.model_dump(exclude_unset=True))
    db.add(novo_item)
    db.commit()
    db.refresh(novo_item)
    return novo_item

# --- ROTAS DE PEDIDO ---

@app.post("/pedidos", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def criar_pedido(
    pedido_in: PedidoCreate, 
    db: Session = Depends(get_db),
    usuario_atual: Optional[Usuario] = Depends(get_usuario_opcional) # Aceita visitante
):
    unidade = db.query(Unidade).filter(Unidade.id == pedido_in.unidade_id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="A Unidade informada não existe.")

    valor_total_pedido = 0
    itens_db = []
    
    for item in pedido_in.itens:
        produto = db.query(ItemCardapio).filter(ItemCardapio.id == item.item_id).first()
        if not produto or produto.disponivel == 0:
            raise HTTPException(status_code=404, detail=f"Produto ID {item.item_id} não encontrado ou indisponível.")
        
        # CHECAGEM DO ESTOQUE
        estoque = db.query(Estoque).filter(Estoque.unidade_id == unidade.id, Estoque.item_cardapio_id == produto.id).first()
        if not estoque or estoque.quantidade < item.quantidade:
            raise HTTPException(status_code=409, detail=f"Estoque insuficiente para {produto.nome} na {unidade.nome}.")
            
        valor_total_pedido += produto.preco * item.quantidade
        itens_db.append(ItemPedido(item_cardapio_id=produto.id, quantidade=item.quantidade, preco_unitario=produto.preco))
        
    novo_pedido = Pedido(
        cliente_id=usuario_atual.id if usuario_atual else None,
        unidade_id=unidade.id,
        canal_pedido=pedido_in.canal_pedido,
        valor_total=valor_total_pedido,
        status=StatusPedidoEnum.CRIADO
    )
    novo_pedido.itens = itens_db
    db.add(novo_pedido)
    db.commit()
    db.refresh(novo_pedido)
    return novo_pedido


@app.post("/pedidos/{pedido_id}/pagamento")
def processar_pagamento_mock(pedido_id: int, db: Session = Depends(get_db)):
    """Mock: Aprova aleatoriamente muda para COZINHA reduz o estoque e dá pontos."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido: raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    if pedido.status != StatusPedidoEnum.CRIADO:
        raise HTTPException(status_code=400, detail=f"Pedido em status inválido para pagamento: {pedido.status}")

    pagamento_aprovado = random.random() < 0.80

    if pagamento_aprovado:
        pedido.status = StatusPedidoEnum.COZINHA
        
        for item in pedido.itens:
            estoque = db.query(Estoque).filter(
                Estoque.unidade_id == pedido.unidade_id, 
                Estoque.item_cardapio_id == item.item_cardapio_id
            ).first()
            if estoque: estoque.quantidade -= item.quantidade
        
        pontos = 0
        if pedido.cliente_id:
            cliente = db.query(Usuario).filter(Usuario.id == pedido.cliente_id).first()
            if cliente:
                pontos = int(pedido.valor_total * 100)
                cliente.pontos_fidelidade += pontos

        db.commit()
        db.refresh(pedido)
        return {
            "mensagem": "Pagamento aprovado! Pedido enviado para a cozinha.", 
            "status": pedido.status,
            "pontos_ganhos": pontos
        }
    else:
        pedido.status = StatusPedidoEnum.CANCELADO
        db.commit()
        raise HTTPException(status_code=402, detail="Pagamento recusado pela operadora do cartão. Seu pedido foi cancelado.")

@app.get("/pedidos", response_model=List[PedidoResponse])
def listar_pedidos(
    canal_pedido: Optional[CanalPedidoEnum] = None,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual) 
):
    query = db.query(Pedido)
    if usuario_atual.tipo == "CLIENTE":
        query = query.filter(Pedido.cliente_id == usuario_atual.id)
    if canal_pedido:
        query = query.filter(Pedido.canal_pedido == canal_pedido)
    return query.all()

class StatusUpdate(BaseModel):
    novo_status: StatusPedidoEnum

@app.patch("/pedidos/{pedido_id}/status", response_model=PedidoResponse)
def atualizar_status_pedido(
    pedido_id: int,
    status_data: StatusUpdate,
    db: Session = Depends(get_db),
    usuario_func: Usuario = Depends(verificar_tipo_usuario(["FUNCIONARIO", "ADMIN", "GERENTE"]))
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    
    pedido.status = status_data.novo_status
    db.commit()
    db.refresh(pedido)
    
    return pedido