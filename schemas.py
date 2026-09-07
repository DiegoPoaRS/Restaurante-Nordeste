from pydantic import BaseModel
from typing import List, Optional
from models import CanalPedidoEnum

class UsuarioCreate(BaseModel):
    email: str
    senha: str
    tipo: Optional[str] = "CLIENTE"

class UsuarioResponse(BaseModel):
    id: int
    email: str
    tipo: str

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    senha: str

class ItemCardapioResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    preco: float
    disponivel: int

    class Config:
        from_attributes = True

class ItemPedidoCreate(BaseModel):
    item_id: int
    quantidade: int

class PedidoCreate(BaseModel):
    canal_pedido: CanalPedidoEnum
    itens: List[ItemPedidoCreate]

class ItemCardapioCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float
    disponivel: Optional[int] = 1

class ItemCardapioUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[float] = None
    disponivel: Optional[int] = None

class ItemPedidoResponse(BaseModel):
    id: int
    item_cardapio_id: int
    quantidade: int
    preco_unitario: float

    class Config:
        from_attributes = True

# PedidoResponse definitivo contendo a lista de itens
class PedidoResponse(BaseModel):
    id: int
    cliente_id: int
    canal_pedido: CanalPedidoEnum
    status: str
    valor_total: float
    itens: List[ItemPedidoResponse] = []

    class Config:
        from_attributes = True

class ItemCardapioSimples(BaseModel):
    nome: str

    class Config:
        from_attributes = True

class ItemPedidoDetalhadoResponse(BaseModel):
    id: int
    quantidade: int
    preco_unitario: float
    item_cardapio: ItemCardapioSimples

    class Config:
        from_attributes = True