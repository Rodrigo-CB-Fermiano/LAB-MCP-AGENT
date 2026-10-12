import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer, Context
from pydantic import Field
from typing import Literal

load_dotenv()

mcp = MCPServer("shipping-tool")

DB_DSN = os.getenv("DB_DSN", "postgres://postgres:postgres@localhost:5432/pedidos_db")


def get_db():
    return psycopg2.connect(DB_DSN, cursor_factory=RealDictCursor)


@mcp.resource("pedidos://lista")
def listar_pedidos() -> list[dict]:
    """Lista todos os pedidos cadastrados."""
    with get_db() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, item, quantidade, status FROM pedidos ORDER BY id")
        return [dict(row) for row in cur.fetchall()]


@mcp.resource("pedido://{pedido_id}")
def buscar_pedido(pedido_id: str) -> dict:
    """Retorna os detalhes de um pedido específico pelo ID."""
    with get_db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, item, quantidade, status, criado_em FROM pedidos WHERE id = %s",
            (int(pedido_id),),
        )
        row = cur.fetchone()
    if row is None:
        raise ValueError(f"Pedido {pedido_id} não encontrado.")
    return dict(row)


@mcp.tool()
def criar_pedido(
    item: str = Field(..., min_length=1, description="Nome do item pedido."),
    quantidade: int = Field(..., gt=0, description="Quantidade do item."),
) -> dict:
    """Cria um novo pedido com status 'Em preparo'."""
    with get_db() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO pedidos (item, quantidade) VALUES (%s, %s) RETURNING id, item, quantidade, status",
            (item, quantidade),
        )
        row = cur.fetchone()
        conn.commit()
    return dict(row)


@mcp.tool()
def atualizar_status(
    pedido_id: int = Field(..., gt=0, description="ID do pedido."),
    status: Literal["Em preparo", "Pronto", "Entregue", "Cancelado"] = Field(
        ..., description="Novo status do pedido."
    ),
) -> dict:
    """Atualiza o status de um pedido existente."""
    with get_db() as conn, conn.cursor() as cur:
        cur.execute(
            """UPDATE pedidos
               SET status = %s, updated_em = NOW()
               WHERE id = %s
               RETURNING id, item, quantidade, status""",
            (status, pedido_id),
        )
        row = cur.fetchone()
        conn.commit()
    if row is None:
        raise ValueError(f"Pedido {pedido_id} não encontrado.")
    return dict(row)


@mcp.tool()
def deletar_pedido(
    pedido_id: int = Field(..., gt=0, description="ID do pedido a ser removido.")
) -> dict:
    """Remove um pedido pelo ID."""
    with get_db() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM pedidos WHERE id = %s RETURNING id, item",
            (pedido_id,),
        )
        row = cur.fetchone()
        conn.commit()
    if row is None:
        raise ValueError(f"Pedido {pedido_id} não encontrado.")
    return {"deletado": True, **dict(row)}


if __name__ == "__main__":
    mcp.run()
