# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = "pos.config"

    default_partner_id = fields.Many2one(
        comodel_name="res.partner",
        default=lambda self: self.env.ref('l10n_do_pos.default_partner_on_pos', raise_if_not_found=False),
        help="Este cliente se usará por defecto como cliente de consumo para las facturas de consumidor final",
    )
    print_pdf = fields.Boolean("Imprimir PDF", default=False)
    only_invoice = fields.Boolean(string="Solo Facturacion", default=False)

    @api.onchange("only_invoice")
    def onchange_only_invoice(self):
        default_partner = self.env.ref("l10n_do_pos.default_partner_on_pos", raise_if_not_found=False)
        if self.only_invoice and default_partner:
            self.default_partner_id = default_partner.id
        else:
            self.default_partner_id = False
