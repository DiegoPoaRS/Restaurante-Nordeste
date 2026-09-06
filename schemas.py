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

class PedidoResponse(BaseModel):
    id: int
    cliente_id: int
    canal_pedido: CanalPedidoEnum
    status: str
    valor_total: float

    class Config:
        from_attributes = True