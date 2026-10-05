import random
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from pydantic import BaseModel
from database import engine, get_db, Base
from security import SECRET_KEY, ALGORITHM, get_password_hash, verify_password, create_access_token, verificar_admin
from models import Usuario, ItemCardapio, Pedido, CanalPedidoEnum, ItemPedido, Unidade, Estoque, StatusPedidoEnum, LogAuditoria
from schemas import UsuarioCreate, UsuarioResponse, ItemCardapioResponse, PedidoCreate, PedidoResponse, ItemCardapioCreate, ItemCardapioUpdate, CampanhaCreate, PromoverUsuario, LogAuditoriaResponse, EstoqueResponse, EstoqueUpdate, UsuarioComPedidosResponse


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


@app.get("/usuarios/me", response_model=UsuarioComPedidosResponse)
def ler_usuario_atual(
    usuario_atual: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db)):

    pedidos_do_usuario = db.query(Pedido).filter(
        Pedido.cliente_id == usuario_atual.id).order_by(Pedido.data_criacao.desc()).all()

    return {
        "id": usuario_atual.id,
        "nome_completo": usuario_atual.nome_completo,
        "email": usuario_atual.email,
        "tipo": usuario_atual.tipo,
        "pontos_fidelidade": usuario_atual.pontos_fidelidade,
        "unidade_id": usuario_atual.unidade_id,
        "cpf": usuario_atual.cpf,
        "pedidos": pedidos_do_usuario
    }


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
        raise HTTPException(status_code=404, detail="Unidade não existe.")

    cliente_final = None
    atendente_final_id = None

    if usuario_atual and usuario_atual.tipo in ["ADMIN", "GERENTE", "FUNCIONARIO"]:
        atendente_final_id = usuario_atual.id
        if pedido_in.cpf_cliente:
            cliente_final = db.query(Usuario).filter(Usuario.cpf == pedido_in.cpf_cliente).first()
    else:
        cliente_final = usuario_atual

    # 1. VALIDAÇÃO DE ESTOQUE E SUBTOTAL
    subtotal_pedido = 0.0
    itens_db = []
    
    for item in pedido_in.itens:
        produto = db.query(ItemCardapio).filter(ItemCardapio.id == item.item_id).first()
        if not produto or produto.disponivel == 0:
            raise HTTPException(status_code=404, detail=f"Produto ID {item.item_id} indisponível.")
        
        estoque = db.query(Estoque).filter(Estoque.unidade_id == unidade.id, Estoque.item_cardapio_id == produto.id).first()
        if not estoque or estoque.quantidade < item.quantidade:
            raise HTTPException(status_code=409, detail=f"Estoque insuficiente para {produto.nome}.")
            
        subtotal_pedido += produto.preco * item.quantidade
        itens_db.append(ItemPedido(item_cardapio_id=produto.id, quantidade=item.quantidade, preco_unitario=produto.preco))

    # 2. CÁLCULO DE DESCONTOS (PONTOS OU CUPOM)
    valor_desconto = 0.0
    pontos_utilizados = 0
    cupom_aplicado_nome = None
    
    if pedido_in.usar_pontos_fidelidade:
        if not cliente_final:
            raise HTTPException(status_code=400, detail="Identificação necessária para usar pontos.")
        
        # 100 pontos = R$ 1.00
        valor_em_pontos = cliente_final.pontos_fidelidade / 100.0
        if valor_em_pontos > 0:
            # Não deixa o desconto ser maior que o subtotal do pedido
            valor_desconto = min(subtotal_pedido, valor_em_pontos)
            pontos_utilizados = int(valor_desconto * 100)
            cliente_final.pontos_fidelidade -= pontos_utilizados # Deduz os pontos do cliente real

    elif pedido_in.codigo_cupom:
        from models import Campanha # Importe se necessário
        cupom = db.query(Campanha).filter(
            Campanha.codigo == pedido_in.codigo_cupom,
            Campanha.ativo == True
        ).first()
        
        if not cupom:
            raise HTTPException(status_code=404, detail="Cupom inválido ou expirado.")
            
        if cupom.unidade_id and cupom.unidade_id != unidade.id:
            raise HTTPException(status_code=400, detail="Este cupom não é válido para esta loja.")
            
        cupom_aplicado_nome = cupom.codigo
        
        # Aplica o desconto item a item dependendo da regra
        for item_pedido in itens_db:
            produto_vinculado = db.query(ItemCardapio).filter(ItemCardapio.id == item_pedido.item_cardapio_id).first()
            aplica_desconto = False
            
            if cupom.tipo_aplicacao == "CATEGORIA" and produto_vinculado.categoria == cupom.categoria_alvo:
                aplica_desconto = True
            elif cupom.tipo_aplicacao == "ITEM" and produto_vinculado.id == cupom.item_alvo_id:
                aplica_desconto = True
                
            if aplica_desconto:
                valor_item_cheio = item_pedido.preco_unitario * item_pedido.quantidade
                desconto_neste_item = valor_item_cheio * (cupom.desconto_percentual / 100.0)
                valor_desconto += desconto_neste_item

    valor_total_final = subtotal_pedido - valor_desconto
    if valor_total_final < 0: valor_total_final = 0.0

    # 3. PERSISTÊNCIA DO PEDIDO
    novo_pedido = Pedido(
        cliente_id=cliente_final.id if cliente_final else None,
        atendente_id=atendente_final_id,
        unidade_id=unidade.id,
        canal_pedido=pedido_in.canal_pedido,
        subtotal=subtotal_pedido,
        valor_desconto=valor_desconto,
        valor_total=valor_total_final,
        pontos_resgatados=pontos_utilizados,
        cupom_aplicado=cupom_aplicado_nome,
        status=StatusPedidoEnum.CRIADO
    )
    novo_pedido.itens = itens_db
    db.add(novo_pedido)
    db.flush() 

    # LOG GERENCIAL
    qtd_itens = sum([i.quantidade for i in pedido_in.itens])
    detalhes_venda = f"NOVA_VENDA | Pedido: #{novo_pedido.id} | Subtotal: R$ {subtotal_pedido:.2f} | Desconto: R$ {valor_desconto:.2f} | Final: R$ {valor_total_final:.2f} | Atendente: {atendente_final_id}"
    registrar_auditoria(db=db, usuario_id=usuario_atual.id if usuario_atual else None, acao="PEDIDO_CRIADO", detalhes=detalhes_venda)

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


@app.get("/relatorios/bi")
def gerar_relatorios_bi(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(verificar_tipo_usuario(["ADMIN", "GERENTE"]))
):
    """Gera indicadores gerenciais. Filtra automaticamente pela unidade se for Gerente."""
    
    # 1. Query Base (Ignora cancelados)
    query_base = db.query(Pedido).filter(Pedido.status != StatusPedidoEnum.CANCELADO)
    if usuario_atual.tipo == "GERENTE":
        query_base = query_base.filter(Pedido.unidade_id == usuario_atual.unidade_id)
        
    # Faturamento e Ticket Médio
    dados_gerais = query_base.with_entities(
        func.count(Pedido.id).label("total_pedidos"),
        func.sum(Pedido.valor_total).label("faturamento_total"),
        func.avg(Pedido.valor_total).label("ticket_medio")
    ).first()

    # 2. SLA de Pedidos (Tempo médio em minutos)
    query_sla = db.query(
        func.avg((func.julianday(Pedido.data_atualizacao) - func.julianday(Pedido.data_criacao)) * 1440)
    ).filter(Pedido.status.in_([StatusPedidoEnum.PRONTO, StatusPedidoEnum.ENTREGUE]))
    
    if usuario_atual.tipo == "GERENTE":
        query_sla = query_sla.filter(Pedido.unidade_id == usuario_atual.unidade_id)
        
    sla_medio = query_sla.scalar()

    # 3. Itens Mais Vendidos
    query_itens = db.query(
        ItemCardapio.nome,
        func.sum(ItemPedido.quantidade).label("total_vendido")
    ).join(ItemPedido, ItemCardapio.id == ItemPedido.item_cardapio_id)\
     .join(Pedido, ItemPedido.pedido_id == Pedido.id)\
     .filter(Pedido.status != StatusPedidoEnum.CANCELADO)
     
    if usuario_atual.tipo == "GERENTE":
        query_itens = query_itens.filter(Pedido.unidade_id == usuario_atual.unidade_id)
        
    itens_vendidos = query_itens.group_by(ItemCardapio.nome).order_by(desc("total_vendido")).limit(5).all()

    # 4. Venda por Funcionário (Ticket / Desempenho)
    query_func = db.query(
        Usuario.nome_completo,
        func.count(Pedido.id).label("total_pedidos"),
        func.sum(Pedido.valor_total).label("total_arrecadado")
    ).join(Pedido, Usuario.id == Pedido.atendente_id)\
     .filter(Pedido.status != StatusPedidoEnum.CANCELADO)
     
    if usuario_atual.tipo == "GERENTE":
        query_func = query_func.filter(Pedido.unidade_id == usuario_atual.unidade_id)
        
    vendas_funcionarios = query_func.group_by(Usuario.nome_completo).order_by(desc("total_arrecadado")).all()

    return {
        "faturamento_total": dados_gerais.faturamento_total or 0.0,
        "total_pedidos": dados_gerais.total_pedidos or 0,
        "ticket_medio": dados_gerais.ticket_medio or 0.0,
        "sla_medio_minutos": round(sla_medio, 2) if sla_medio else 0.0,
        "top_itens": [{"nome": i[0], "quantidade": i[1]} for i in itens_vendidos],
        "vendas_por_funcionario": [{"nome": f[0], "pedidos": f[1], "arrecadado": f[2]} for f in vendas_funcionarios]
    }



@app.post("/campanhas", status_code=status.HTTP_201_CREATED)
def criar_campanha(
    campanha_in: CampanhaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(verificar_tipo_usuario(["ADMIN", "GERENTE"]))
):
    from models import Campanha # Importação local para evitar dependência circular
    
    # === REGRA DE NEGÓCIO: HIERARQUIA ===
    if usuario_atual.tipo == "GERENTE":
        # Força o cupom a pertencer APENAS à loja do gerente, ignorando o que vier no payload
        campanha_in.unidade_id = usuario_atual.unidade_id
    
    # Validações estruturais do cupom
    if campanha_in.tipo_aplicacao == "CATEGORIA" and not campanha_in.categoria_alvo:
        raise HTTPException(status_code=400, detail="Especifique a categoria alvo para o desconto.")
    if campanha_in.tipo_aplicacao == "ITEM" and not campanha_in.item_alvo_id:
        raise HTTPException(status_code=400, detail="Especifique o item alvo para o desconto.")

    cupom_existente = db.query(Campanha).filter(Campanha.codigo == campanha_in.codigo.upper()).first()
    if cupom_existente:
        raise HTTPException(status_code=409, detail="Este código de cupom já existe.")

    nova_campanha = Campanha(
        codigo=campanha_in.codigo.upper(),
        desconto_percentual=campanha_in.desconto_percentual,
        tipo_aplicacao=campanha_in.tipo_aplicacao,
        categoria_alvo=campanha_in.categoria_alvo,
        item_alvo_id=campanha_in.item_alvo_id,
        unidade_id=campanha_in.unidade_id,
        ativo=True
    )
    db.add(nova_campanha)

    # Rastreabilidade gerencial
    escopo = f"Loja {nova_campanha.unidade_id}" if nova_campanha.unidade_id else "Rede Global"
    registrar_auditoria(
        db=db, 
        usuario_id=usuario_atual.id, 
        acao="CRIAR_CAMPANHA", 
        detalhes=f"Cupom {nova_campanha.codigo} ({nova_campanha.desconto_percentual}%) criado para {escopo}."
    )

    db.commit()
    db.refresh(nova_campanha)
    return nova_campanha


@app.get("/campanhas")
def listar_campanhas(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(verificar_tipo_usuario(["ADMIN", "GERENTE"]))
):
    from models import Campanha
    query = db.query(Campanha)
    
    if usuario_atual.tipo == "GERENTE":
        # Gerente enxerga todos os cupons (unidade null) e os cupons da sua propria loja
        query = query.filter((Campanha.unidade_id == usuario_atual.unidade_id) | (Campanha.unidade_id.is_(None)))
        
    return query.all()