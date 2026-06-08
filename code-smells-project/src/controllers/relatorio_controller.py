"""Controller de Relatório — regra de desconto com constantes nomeadas (cura AP-17)."""
from src.models import pedido_model

# Faixas de desconto (limiar de faturamento -> percentual). Cura magic numbers.
FAIXAS_DESCONTO = [
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
]


def _desconto(faturamento):
    for limiar, pct in FAIXAS_DESCONTO:
        if faturamento > limiar:
            return faturamento * pct
    return 0


def vendas():
    c = pedido_model.contadores_vendas()
    faturamento = c["faturamento"]
    desconto = _desconto(faturamento)
    total_pedidos = c["total_pedidos"]
    relatorio = {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": c["pendentes"],
        "pedidos_aprovados": c["aprovados"],
        "pedidos_cancelados": c["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
    return {"dados": relatorio, "sucesso": True}, 200
