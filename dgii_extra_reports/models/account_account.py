from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_dividend = fields.Boolean(string="Cuenta de dividendos")
    ret_others_rent2 = fields.Boolean(string="Cuenta Otras retenciones 2%")
