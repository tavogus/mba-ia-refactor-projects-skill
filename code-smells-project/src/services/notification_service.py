"""Efeitos colaterais (notificações) isolados num service injetável (cura AP-09).

No projeto original isto eram `print()` espalhados pelo controller.
"""
import logging

logger = logging.getLogger("notifications")


class NotificationService:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("pedido_criado pedido=%s usuario=%s (email/sms/push)", pedido_id, usuario_id)

    def status_atualizado(self, pedido_id, status):
        if status == "aprovado":
            logger.info("pedido %s aprovado — preparar envio", pedido_id)
        elif status == "cancelado":
            logger.info("pedido %s cancelado — devolver estoque", pedido_id)
