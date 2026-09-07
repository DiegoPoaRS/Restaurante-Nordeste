from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from models import CanalPedidoEnum

class UsuarioCreate(BaseModel):
    nome_completo: str
    email: str
    senha: str
    endereco_entrega: str
    telefone: str
    cpf: str
    data_nascimento: date
    aceite_lgpd: bool = Field(..., description="Aceite explícito da política de proteção de dados (LGPD)")
    tipo: Optional[str] = "CLIENTE"

class UsuarioResponse(BaseModel):
    id: int
    nome_completo: str
    email: str
    tipo: str
    pontos_fidelidade: int

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

class ItemPedidoCreate(BaseModel):
    item_id: int
    quantidade: int

class PedidoCreate(BaseModel):
    unidade_id: int # de qual loja descontar o estoque
    canal_pedido: CanalPedidoEnum
    itens: List[ItemPedidoCreate]

class ItemPedidoResponse(BaseModel):
    id: int
    item_cardapio_id: int
    quantidade: int
    preco_unitario: float

    class Config:
        from_attributes = True

class PedidoResponse(BaseModel):
    id: int
    cliente_id: Optional[int] = None # Não identificado
    unidade_id: int
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