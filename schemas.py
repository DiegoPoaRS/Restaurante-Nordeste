from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date, datetime
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

class PromoverUsuario(BaseModel):
    email: str
    novo_tipo: str
    unidade_id: Optional[int] = None

class UsuarioResponse(BaseModel):
    id: int
    nome_completo: str
    email: str
    tipo: str
    pontos_fidelidade: int = 0
    unidade_id: Optional[int] = None
    cpf: Optional[str] = None

    @field_validator('pontos_fidelidade', mode='before')
    @classmethod
    def parse_pontos(cls, v):
        if v == '' or v is None:
            return 0
        return int(v)

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
    unidade_id: int 
    canal_pedido: CanalPedidoEnum
    cpf_cliente: Optional[str] = None
    itens: List[ItemPedidoCreate]

class ItemPedidoResponse(BaseModel):
    id: int
    item_cardapio_id: int
    quantidade: int
    preco_unitario: float

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


class PedidoResponse(BaseModel):
    id: int
    cliente_id: Optional[int] = None 
    unidade_id: int
    canal_pedido: CanalPedidoEnum
    status: str
    valor_total: float
    itens: List[ItemPedidoResponse] = []

    class Config:
        from_attributes = True

class EstoqueResponse(BaseModel):
    id: int
    unidade_id: int
    unidade_nome: Optional[str] = None
    item_cardapio_id: int
    quantidade: int
    nome_item: Optional[str] = None

    class Config:
        from_attributes = True

class EstoqueUpdate(BaseModel):
    item_cardapio_id: int
    quantidade: int
    unidade_id: Optional[int] = None


class LogAuditoriaResponse(BaseModel):
    id: int
    data_hora: datetime
    usuario_id: Optional[int]
    acao: str
    detalhes: Optional[str]

    class Config:
        from_attributes = True