# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrPayslipEmployees(models.Model):
    _inherit = 'hr.work.entry'

    def action_validate(self):
        # Retorna True para que la nomina no de error
        # con lsa entradas de trabajo.
        return True
