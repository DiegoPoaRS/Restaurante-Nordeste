from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, Boolean, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base



class CategoriaEnum(str, enum.Enum):
    BEBIDAS = "BEBIDAS"
    SOBREMESAS = "SOBREMESAS"
    LANCHES = "LANCHES"
    ACOMPANHAMENTOS = "ACOMPANHAMENTOS"
    COMBOS = "COMBOS"
    BRINDES = "BRINDES"

class TipoAplicacaoEnum(str, enum.Enum):
    CATEGORIA = "CATEGORIA"
    ITEM = "ITEM"


class CanalPedidoEnum(str, enum.Enum):
    APP = "APP"
    TOTEM = "TOTEM"
    BALCAO = "BALCAO"
    PICKUP = "PICKUP"
    WEB = "WEB"

class StatusPedidoEnum(str, enum.Enum):
    CRIADO = "CRIADO"
    PAGO = "PAGO"
    COZINHA = "COZINHA"
    PRONTO = "PRONTO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    endereco_entrega = Column(String, nullable=False)
    telefone = Column(String, unique=True, nullable=False)
    cpf = Column(String, unique=True, nullable=False)
    data_nascimento = Column(Date, nullable=False)
    aceite_lgpd = Column(Boolean, default=False)
    tipo = Column(String, default="CLIENTE") 
    pontos_fidelidade = Column(Integer, default=0)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=True) # Vínculo com loja só para funcionarios e gerentes 
    unidade = relationship("Unidade", back_populates="funcionarios")

class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"
    id = Column(Integer, primary_key=True, index=True)
    data_hora = Column(DateTime(timezone=True), server_default=func.now())
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    acao = Column(String, nullable=False)
    detalhes = Column(String, nullable=True)

class Unidade(Base):
    __tablename__ = "unidades"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    endereco = Column(String, nullable=False)
    estoques = relationship("Estoque", back_populates="unidade")
    funcionarios = relationship("Usuario", back_populates="unidade")

class ItemCardapio(Base):
    __tablename__ = "itens_cardapio"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    preco = Column(Float, nullable=False)
    categoria = Column(Enum(CategoriaEnum), default=CategoriaEnum.LANCHES) # NOVO
    disponivel = Column(Integer, default=1) 
    estoques = relationship("Estoque", back_populates="item_cardapio")

class Campanha(Base):
    __tablename__ = "campanhas"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=False) # Ex: NORDESTE10
    desconto_percentual = Column(Float, nullable=False) 
    tipo_aplicacao = Column(Enum(TipoAplicacaoEnum), nullable=False)
    categoria_alvo = Column(Enum(CategoriaEnum), nullable=True)
    item_alvo_id = Column(Integer, ForeignKey("itens_cardapio.id"), nullable=True)
    ativo = Column(Boolean, default=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=True) # Se NULL, vale na rede toda

class Estoque(Base):
    __tablename__ = "estoque"
    id = Column(Integer, primary_key=True, index=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    item_cardapio_id = Column(Integer, ForeignKey("itens_cardapio.id"), nullable=False)
    quantidade = Column(Integer, nullable=False, default=0)
    unidade = relationship("Unidade", back_populates="estoques")
    item_cardapio = relationship("ItemCardapio", back_populates="estoques")

class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    atendente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    canal_pedido = Column(Enum(CanalPedidoEnum), nullable=False)
    status = Column(Enum(StatusPedidoEnum), default=StatusPedidoEnum.CRIADO)
    
    # Valores Financeiros
    subtotal = Column(Float, nullable=False, default=0.0) 
    valor_desconto = Column(Float, nullable=False, default=0.0) 
    valor_total = Column(Float, nullable=False) 
    pontos_resgatados = Column(Integer, default=0) 
    cupom_aplicado = Column(String, nullable=True) 
    
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())
    data_atualizacao = Column(DateTime(timezone=True), onupdate=func.now())
    
    itens = relationship("ItemPedido", back_populates="pedido")

class ItemPedido(Base):
    __tablename__ = "itens_pedido"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    item_cardapio_id = Column(Integer, ForeignKey("itens_cardapio.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    pedido = relationship("Pedido", back_populates="itens")
    item_cardapio = relationship("ItemCardapio")