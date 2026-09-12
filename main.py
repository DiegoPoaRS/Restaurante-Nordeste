import random
import uuid
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
from models import Usuario, ItemCardapio, Pedido, CanalPedidoEnum, ItemPedido, Unidade, Estoque, StatusPedidoEnum, LogAuditoria
from schemas import UsuarioCreate, UsuarioResponse, ItemCardapioResponse, PedidoCreate, PedidoResponse, ItemCardapioCreate, ItemCardapioUpdate, PromoverUsuario, LogAuditoriaResponse, EstoqueResponse, EstoqueUpdate


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


def registrar_auditoria(db: Session, usuario_id: int, acao: str, detalhes: str):
    log = LogAuditoria(
        usuario_id=usuario_id,
        acao=acao,
        detalhes=detalhes
    )
    db.add(log)


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

@app.get("/auditoria", response_model=List[LogAuditoriaResponse])
def listar_logs_auditoria(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(verificar_tipo_usuario(["ADMIN"])) # APENAS ADMIN PODE LER
):
    """Retorna os últimos 100 registros de auditoria, ordenados do mais recente para o mais antigo."""
    return db.query(LogAuditoria).order_by(LogAuditoria.data_hora.desc()).limit(100).all()

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

    registrar_auditoria(db=db, usuario_id=db_user.id, acao="LOGIN_SISTEMA", detalhes=f"Usuário {db_user.email} efetuou login com sucesso."    )
    db.commit()

    access_token = create_access_token(data={"sub": db_user.email, "tipo": db_user.tipo})
    return {"access_token": access_token, "token_type": "bearer", "usuario_id": db_user.id, "tipo": db_user.tipo}


@app.get("/usuarios/me", response_model=UsuarioResponse)
def ler_usuario_atual(usuario_atual: Usuario = Depends(get_usuario_atual)):
    """Retorna os dados do usuário logado, incluindo perfil e unidade vinculada."""
    return usuario_atual


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
    

    if dados.novo_tipo == "CLIENTE":
        usuario_alvo.unidade_id = None
    else:
        if not dados.unidade_id:
            raise HTTPException(status_code=400, detail="É obrigatório selecionar uma loja para Gerentes e Funcionários.")
        usuario_alvo.unidade_id = dados.unidade_id
    
    registrar_auditoria(
        db=db,
        usuario_id=usuario_logado.id,
        acao="PROMOVER_USUARIO",
        detalhes=f"Alterou o acesso de {dados.email} para {dados.novo_tipo} (Loja: {dados.unidade_id})"
    )
    
    db.commit()
    
    return {"mensagem": f"O usuário {dados.email} foi atualizado para {dados.novo_tipo} com sucesso!"}


@app.get("/unidades")
def listar_unidades(db: Session = Depends(get_db)):
    return db.query(Unidade).all()

#==============================
# --- ROTAS DE CARDÁPIO ---
#==============================

@app.get("/cardapio", response_model=List[ItemCardapioResponse])
def listar_cardapio(db: Session = Depends(get_db)):

#============================================
# Cria a Unidade Matriz se não existir
#============================================

    unidade = db.query(Unidade).first()
    if not unidade:
        unidade = Unidade(nome="Matriz Raízes", endereco="Rua Principal, 100")
        db.add(unidade)
        db.commit()
        db.refresh(unidade)

#=================================
# CRIA ADMIN CASO NÃO EXISTA
#=================================

    admin_existe = db.query(Usuario).filter(Usuario.email == "admin@raizes.com.br").first()
    if not admin_existe:
        admin = Usuario(
            nome_completo="Admin", 
            email="admin@raizes.com.br", 
            senha_hash=get_password_hash("admin123"), 
            tipo="ADMIN", 
            unidade_id=""
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



@app.get("/estoque", response_model=List[EstoqueResponse])
def listar_estoque(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(verificar_tipo_usuario(["ADMIN", "GERENTE", "FUNCIONARIO"]))
):
    """Retorna o estoque. Admin vê todas as lojas com seus respectivos nomes."""
    query = db.query(Estoque).join(ItemCardapio).join(Unidade)
    
    if usuario_atual.tipo in ["GERENTE", "FUNCIONARIO"]:
        query = query.filter(Estoque.unidade_id == usuario_atual.unidade_id)
        
    registros = query.all()
    resultado = []
    for est in registros:
        resultado.append({
            "id": est.id,
            "unidade_id": est.unidade_id,
            "unidade_nome": est.unidade.nome if est.unidade else "Loja Desconhecida",
            "item_cardapio_id": est.item_cardapio_id,
            "quantidade": est.quantidade,
            "nome_item": est.item_cardapio.nome if est.item_cardapio else "Desconhecido"
        })
        
    return resultado

@app.put("/estoque", response_model=EstoqueResponse)
def atualizar_estoque(
    dados: EstoqueUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(verificar_tipo_usuario(["ADMIN", "GERENTE", "FUNCIONARIO"]))
):
    """Atualiza ou insere estoque. Admin pode definir a unidade_id; Gerentes usam a própria unidade."""
    if usuario_atual.tipo == "ADMIN" and dados.unidade_id:
        unidade_alvo = dados.unidade_id
    else:
        unidade_alvo = usuario_atual.unidade_id
    
    if not unidade_alvo:
        raise HTTPException(status_code=400, detail="Unidade não definida para atualização de estoque.")

    produto = db.query(ItemCardapio).filter(ItemCardapio.id == dados.item_cardapio_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado no cardápio.")

    estoque = db.query(Estoque).filter(
        Estoque.unidade_id == unidade_alvo,
        Estoque.item_cardapio_id == dados.item_cardapio_id
    ).first()

    if estoque:
        estoque.quantidade = dados.quantidade
    else:
        estoque = Estoque(
            unidade_id=unidade_alvo,
            item_cardapio_id=dados.item_cardapio_id,
            quantidade=dados.quantidade
        )
        db.add(estoque)

    db.commit()
    db.refresh(estoque)

    return {
        "id": estoque.id,
        "unidade_id": estoque.unidade_id,
        "unidade_nome": estoque.unidade.nome if estoque.unidade else "Loja",
        "item_cardapio_id": estoque.item_cardapio_id,
        "quantidade": estoque.quantidade,
        "nome_item": produto.nome
    }
    
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
def processar_pagamento_externo(pedido_id: int, db: Session = Depends(get_db)):

    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido: 
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    if pedido.status != StatusPedidoEnum.CRIADO:
        raise HTTPException(status_code=400, detail=f"Pedido em status inválido para pagamento: {pedido.status}")

    # 1. Simulação de Envio para o Serviço Externo (Gateway de Pagamento)
    transacao_id = str(uuid.uuid4())
    pagamento_aprovado = random.random() < 0.70
    
    status_gateway = "APROVADO" if pagamento_aprovado else "RECUSADO"
    
    payload_externo = {
        "gateway": "RaizesPayExternalService",
        "transaction_id": transacao_id,
        "pedido_id": pedido.id,
        "valor_processado": pedido.valor_total,
        "moeda": "BRL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mensagem_operadora": "Autorizado com sucesso" if pagamento_aprovado else "Transação recusada pelo banco emissor"
    }

    if pagamento_aprovado:
        pedido.status = StatusPedidoEnum.COZINHA
        
#===================================================
# Executa a baixa de estoque nas tabelas vinculadas
#===================================================

        for item in pedido.itens:
            estoque = db.query(Estoque).filter(
                Estoque.unidade_id == pedido.unidade_id, 
                Estoque.item_cardapio_id == item.item_cardapio_id).first()
            if estoque: 
                estoque.quantidade -= item.quantidade

#==================================================================
# Concede pontos de fidelidade se o cliente estiver identificado
#==================================================================

        pontos = 0
        if pedido.cliente_id:
            cliente = db.query(Usuario).filter(Usuario.id == pedido.cliente_id).first()
            if cliente:
                pontos = int(pedido.valor_total * 100)
                cliente.pontos_fidelidade += pontos
                payload_externo["pontos_fidelidade_atribuidos"] = pontos

        registrar_auditoria(
            db=db,
            usuario_id=pedido.cliente_id,
            acao="PAGAMENTO_EXTERNO_APROVADO",
            detalhes=f"Transação {transacao_id} aprovada para o pedido #{pedido.id} no valor de R$ {pedido.valor_total:.2f}"
        )

        db.commit()
        db.refresh(pedido)

        return {
            "status": status_gateway,
            "payload": payload_externo
        }
    else:
        pedido.status = StatusPedidoEnum.CANCELADO
        
        registrar_auditoria(
            db=db,
            usuario_id=pedido.cliente_id,
            acao="PAGAMENTO_EXTERNO_RECUSADO",
            detalhes=f"Transação {transacao_id} recusada para o pedido #{pedido.id}"
        )
        
        db.commit()
        
        raise HTTPException(
            status_code=402, 
            detail={
                "error": "PAGAMENTO_RECUSADO",
                "status": status_gateway,
                "payload": payload_externo
            }
        )


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

    registrar_auditoria(
        db=db,
        usuario_id=usuario_func.id,
        acao="MUDANCA_STATUS_PEDIDO",
        detalhes=f"Pedido #{pedido.id} movido para {status_data.novo_status}"
    )

    db.commit()
    db.refresh(pedido)
    
    return pedido