import asyncio

from mcp.server.mcpserver import MCPServer, Context
from datetime import datetime,timezone
from pydantic import Field
from typing import Literal

mcp = MCPServer("meu-server")

@mcp.tool()
def ping() -> str:
    
    """Devolve 'pong' quando chamado."""
    
    return f"pong @ {datetime.now(timezone.utc).isoformat()}"


@mcp.tool()
def get_weather(
    city: str = Field(..., min_length=1, description="Nome da cidade."),
    unit: Literal["C", "F"] = "C"
) -> dict:
    
    """Devolve a previsão do tempo para uma cidade específica."""
    
    # Aqui você pode adicionar a lógica para buscar a previsão do tempo.
    # Por enquanto, vamos apenas retornar uma mensagem de exemplo.
    
    return f"Previsão do tempo para {city}: Ensolarado com 25°C."

@mcp.resource("pedidos://lista")
def listar_pedidos() -> str:
    """Devolve uma lista de pedidos."""
    # Aqui você pode adicionar a lógica para buscar os pedidos.
    # Por enquanto, vamos apenas retornar uma lista de exemplo.
    return [
        {"id": 1, "item": "Pizza", "quantidade": 2},
        {"id": 2, "item": "Hambúrguer", "quantidade": 1},
        {"id": 3, "item": "Salada", "quantidade": 3},
    ]
    
@mcp.resource("pedido://{pedido_id}")
def ler_pedido(pedido_id: str) -> str:
    """Devolve os detalhes de um pedido específico."""
    # Aqui você pode adicionar a lógica para buscar os detalhes do pedido.
    # Por enquanto, vamos apenas retornar uma mensagem de exemplo.
    class _PEDIDOS:
        ...
    _PEDIDOS[1] = {"id": 1, "item": "Pizza", "quantidade": 2, "status": "Em preparo"}
    _PEDIDOS[2] = {"id": 2, "item": "Hambúrguer", "quantidade": 1, "status": "Pronto"}
    _PEDIDOS[3] = {"id": 3, "item": "Salada", "quantidade": 3, "status": "Em preparo"}

    return {_PEDIDOS.get(int(pedido_id))}
    

@mcp.tool()
async def processar_lote(ids: list[str], ctx: Context) -> dict:
    total = len(ids)
    for i, item_id in enumerate(ids, start=1):
        
        await ctx.info(f"processando {item_id} ({i}/{total})")
        await asyncio.sleep(1)  # Simula algum processamento
        await ctx.report_progress(progress=i, total=total)
  
    return {"total": total, "sucesso": total}


@mcp.prompt()
def diagnostico_pedido(pedido_id: str, profundidade: Literal["básico", "detalhado"] = "básico") -> str:
    """Devolve um diagnóstico do pedido."""
    # Aqui você pode adicionar a lógica para gerar um diagnóstico do pedido.
    # Por enquanto, vamos apenas retornar uma mensagem de exemplo.
    return (f"Investigue o pedido {pedido_id}. \n"
            f"Nível: {profundidade}.\n"
            f"Use as tools disponíveis para buscar dados.")