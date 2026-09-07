from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
import enum
from database import Base

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
    # Campos de Cadastro e LGPD
    nome_completo = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    endereco_entrega = Column(String, nullable=True)
    telefone = Column(String, nullable=True)
    cpf = Column(String, unique=True, nullable=True)
    data_nascimento = Column(Date, nullable=True)
    aceite_lgpd = Column(Boolean, default=False)
    
    tipo = Column(String, default="CLIENTE") 
    pontos_fidelidade = Column(Integer, default=0)

class Unidade(Base):
    __tablename__ = "unidades"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    endereco = Column(String, nullable=False)
    
    # Relacionamentos
    estoques = relationship("Estoque", back_populates="unidade")

class ItemCardapio(Base):
    __tablename__ = "itens_cardapio"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    preco = Column(Float, nullable=False)
    disponivel = Column(Integer, default=1) 
    
    # Relacionamentos
    estoques = relationship("Estoque", back_populates="item_cardapio")

class Estoque(Base):
    __tablename__ = "estoque"

    id = Column(Integer, primary_key=True, index=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    item_cardapio_id = Column(Integer, ForeignKey("itens_cardapio.id"), nullable=False)
    quantidade = Column(Integer, nullable=False, default=0)

    # Relacionamentos
    unidade = relationship("Unidade", back_populates="estoques")
    item_cardapio = relationship("ItemCardapio", back_populates="estoques")

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    
    cliente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    
    canal_pedido = Column(Enum(CanalPedidoEnum), nullable=False)
    status = Column(Enum(StatusPedidoEnum), default=StatusPedidoEnum.CRIADO)
    valor_total = Column(Float, nullable=False)
    
    # Relacionamentos
    itens = relationship("ItemPedido", back_populates="pedido")

class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    item_cardapio_id = Column(Integer, ForeignKey("itens_cardapio.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)

    # Relacionamentos
    pedido = relationship("Pedido", back_populates="itens")
    item_cardapio = relationship("ItemCardapio")