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
from schemas import (     UsuarioCreate, UsuarioResponse, ItemCardapioResponse, PedidoCreate, 
    PedidoResponse, ItemCardapioCreate, ItemCardapioUpdate, PromoverUsuario    )

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Raízes do Nordeste", version="1.10.0")

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):

    """Intercepta e padroniza erros no formato JSON exigido pelo Roteiro."""
    
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
    """Exige que o usuário esteja logado (Retorna 401 se não estiver)."""
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

@app.get("/usuarios/me", response_model=UsuarioResponse)
def ler_usuario_atual(usuario_atual: Usuario = Depends(get_usuario_atual)):
    """Retorna os dados do usuário logado, incluindo perfil e unidade vinculada."""
    return usuario_atual

# --- ROTAS DE AUTENTICAÇÃO E USUÁRIOS ---

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
    """Retorna todas as lojas cadastradas para o cliente escolher."""
    return db.query(Unidade).all()


# --- ROTAS DE CARDÁPIO ---

@app.get("/cardapio", response_model=List[ItemCardapioResponse])
def listar_cardapio(db: Session = Depends(get_db)):
    # 1. Cria a Unidade Matriz se não existir
    unidade = db.query(Unidade).first()
    if not unidade:
        unidade = Unidade(nome="Matriz Raízes", endereco="Rua Principal, 100")
        db.add(unidade)
        db.commit()
        db.refresh(unidade)

    # 2. Cria o Admin automaticamente e já vinculado à Loja
    admin_existe = db.query(Usuario).filter(Usuario.email == "admin@raizes.com.br").first()
    if not admin_existe:
        admin = Usuario(
            nome_completo="Admin", 
            email="admin@raizes.com.br", 
            senha_hash=get_password_hash("admin123"), 
            tipo="ADMIN", 
            unidade_id=unidade.id
        )
        db.add(admin)
        db.commit()
        
    return db.query(ItemCardapio).filter(ItemCardapio.disponivel == 1).all()

    
@app.post("/cardapio", response_model=ItemCardapioResponse, status_code=status.HTTP_201_CREATED)
def criar_item_cardapio(item: ItemCardapioCreate, db: Session = Depends(get_db), admin: dict = Depends(verificar_admin)):
    novo_item = ItemCardapio(**item.model_dump(exclude_unset=True))
    db.add(novo_item)
    db.commit()
    db.refresh(novo_item)
    return novo_item


@app.patch("/usuarios/promover")
def promover_usuario(
    dados: PromoverUsuario,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(verificar_tipo_usuario(["ADMIN", "GERENTE"]))
):
    usuario_alvo = db.query(Usuario).filter(Usuario.email == dados.email).first()
    
    if not usuario_alvo:
        raise HTTPException(status_code=404, detail="Usuário não encontrado com este e-mail.")
    
    # === BLOQUEIO DE SEGURANÇA EXCLUSIVO PARA O GERENTE ===
    if usuario_logado.tipo == "GERENTE":
        if dados.novo_tipo not in ["CLIENTE", "FUNCIONARIO"]:
            raise HTTPException(status_code=403, detail="Gerentes só podem promover para Funcionário ou rebaixar para Cliente.")
        
        if usuario_alvo.tipo in ["ADMIN", "GERENTE"]:
            raise HTTPException(status_code=403, detail="Acesso negado: Você não pode alterar o cargo de Administradores ou de outros Gerentes.")
            
        # Garante que o gerente só contrate para a própria loja onde trabalha
        if dados.novo_tipo == "FUNCIONARIO" and dados.unidade_id != usuario_logado.unidade_id:
            raise HTTPException(status_code=403, detail="Você só pode contratar funcionários para a sua própria unidade.")


    if dados.novo_tipo not in ["CLIENTE", "FUNCIONARIO", "GERENTE", "ADMIN"]:
        raise HTTPException(status_code=400, detail="Tipo de usuário inválido.")
    
    usuario_alvo.tipo = dados.novo_tipo
    
    # Gerencia o vínculo com a loja
    if dados.novo_tipo == "CLIENTE":
        usuario_alvo.unidade_id = None # Clientes não têm vínculo empregatício
    else:
        if not dados.unidade_id:
            raise HTTPException(status_code=400, detail="É obrigatório selecionar uma loja para Gerentes e Funcionários.")
        usuario_alvo.unidade_id = dados.unidade_id
        
    db.commit()
    
    return {"mensagem": f"O usuário {dados.email} foi atualizado para {dados.novo_tipo} com sucesso!"}


@app.get("/usuarios/equipe", response_model=List[UsuarioResponse])
def listar_equipe(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(verificar_tipo_usuario(["ADMIN", "GERENTE"]))
):
    """Retorna os funcionários e gerentes ordenados alfabeticamente por nome."""
    query = db.query(Usuario).filter(Usuario.tipo.in_(["FUNCIONARIO", "GERENTE", "ADMIN"]))
    if usuario_atual.tipo == "GERENTE":
        query = query.filter(Usuario.unidade_id == usuario_atual.unidade_id)
    return query.order_by(Usuario.nome_completo.asc()).all()


    
# =======================================================
# --- ROTAS DE PEDIDO ---
# =======================================================


@app.post("/pedidos", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def criar_pedido(
    pedido_in: PedidoCreate, 
    db: Session = Depends(get_db),
    usuario_atual: Optional[Usuario] = Depends(get_usuario_opcional)
):
    unidade = db.query(Unidade).filter(Unidade.id == pedido_in.unidade_id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="A Unidade informada não existe.")

    cliente_final_id = None
    atendente_final_id = None

    if usuario_atual and usuario_atual.tipo in ["ADMIN", "GERENTE", "FUNCIONARIO"]:
        atendente_final_id = usuario_atual.id
        
        # === TRAVA DE SEGURANÇA POR UNIDADE ===
        if usuario_atual.tipo in ["GERENTE", "FUNCIONARIO"]:
            if pedido_in.unidade_id != usuario_atual.unidade_id:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Acesso negado: Você só pode registrar pedidos para a sua própria unidade."
                )
        # ======================================

        if pedido_in.cpf_cliente:
            cliente_vinculado = db.query(Usuario).filter(Usuario.cpf == pedido_in.cpf_cliente).first()
            if cliente_vinculado:
                cliente_final_id = cliente_vinculado.id
    else:
        cliente_final_id = usuario_atual.id if usuario_atual else None

    valor_total_pedido = 0
    itens_db = []
    
    for item in pedido_in.itens:
        produto = db.query(ItemCardapio).filter(ItemCardapio.id == item.item_id).first()
        if not produto or produto.disponivel == 0:
            raise HTTPException(status_code=404, detail=f"Produto ID {item.item_id} indisponível.")
        
        estoque = db.query(Estoque).filter(Estoque.unidade_id == unidade.id, Estoque.item_cardapio_id == produto.id).first()
        if not estoque or estoque.quantidade < item.quantidade:
            raise HTTPException(status_code=409, detail=f"Estoque insuficiente para {produto.nome}.")
            
        valor_total_pedido += produto.preco * item.quantidade
        itens_db.append(ItemPedido(item_cardapio_id=produto.id, quantidade=item.quantidade, preco_unitario=produto.preco))
        
    novo_pedido = Pedido(
        cliente_id=cliente_final_id,
        atendente_id=atendente_final_id,
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


# ============================================================
# --- MOCK DE PAGAMENTO + PONTUAÇÃO + CONTROLE DE ESTOQUE ---
# ============================================================


@app.post("/pedidos/{pedido_id}/pagamento")
def processar_pagamento_mock(pedido_id: int, db: Session = Depends(get_db)):

    """Mock inteligente: Aprova aleatoriamente, muda para COZINHA, reduz o estoque e dá pontos."""
    
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido: raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    if pedido.status != StatusPedidoEnum.CRIADO:
        raise HTTPException(status_code=400, detail=f"Pedido em status inválido para pagamento: {pedido.status}")

    # Lógica Randômica (80% de chance de sucesso)
    pagamento_aprovado = random.random() < 0.80

    if pagamento_aprovado:
        # Pula PAGO e vai direto para COZINHA conforme a regra do projeto
        pedido.status = StatusPedidoEnum.COZINHA
        
        # Baixa de Estoque
        for item in pedido.itens:
            estoque = db.query(Estoque).filter(
                Estoque.unidade_id == pedido.unidade_id, 
                Estoque.item_cardapio_id == item.item_cardapio_id).first()
            if estoque: estoque.quantidade -= item.quantidade
        
        # Fidelidade: R$ 1,00 = 100 pontos (Apenas se o cliente estiver cadastrado)

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
    """Permite que o gerente/funcionário avance o status do pedido."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    
    pedido.status = status_data.novo_status
    db.commit()
    db.refresh(pedido)
    
    return pedido