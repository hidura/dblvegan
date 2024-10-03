from odoo import models, fields


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    # Add your custom fields or methods here
    scrap_reason = fields.Selection(
        [
            ("Daño por Equipo defectuoso", "Daño por Equipo defectuoso"),
            ("Daño por Plagas", "Daño por Plagas"),
            ("Devolucion Cliente", "Devolucion Cliente"),
            ("Mala Practica Personal", "Mala Practica Personal"),
            ("Mala Preparacion", "Mala Preparacion"),
            ("Problemas de batido o Mezcla", "Problemas de batido o Mezcla"),
            ("Problemas de horneado", "Problemas de horneado"),
            ("Producto Contaminado", "Producto Contaminado"),
            ("Producto Descongelado", "Producto Descongelado"),
            ("Producto Pegado a la bandeja", "Producto Pegado a la bandeja"),
            ("Rotura", "Rotura"),
            ("Vencimiento", "Vencimiento"),
            ("Producto mal estado", "Producto mal estado"),
        ], string="Causa de desecho"
    )
