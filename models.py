from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from database import Base

class CanalPedidoEnum(str, enum.Enum):
    APP = "APP"
    TOTEM = "TOTEM"
    BALCAO = "BALCAO"
    PICKUP = "PICKUP"
    WEB = "WEB"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    tipo = Column(String, default="CLIENTE")

class ItemCardapio(Base):
    __tablename__ = "itens_cardapio"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    preco = Column(Float, nullable=False)
    disponivel = Column(Integer, default=1) 

class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    item_cardapio_id = Column(Integer, ForeignKey("itens_cardapio.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)

    pedido = relationship("Pedido", back_populates="itens")
    item_cardapio = relationship("ItemCardapio")

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    canal_pedido = Column(Enum(CanalPedidoEnum), nullable=False)
    status = Column(String, default="CRIADO")
    valor_total = Column(Float, nullable=False)
    itens = relationship("ItemPedido", back_populates="pedido")