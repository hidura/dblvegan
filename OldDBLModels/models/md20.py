# -*- coding: utf-8 -*-

from odoo import models, fields,api


class ResCompany(models.Model):
    _inherit = 'res.company'

    preload_employee = fields.Boolean(default=True, string='Preload of Employee')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    preload_employee = fields.Boolean(string='Preload of Employee',
                                      related='company_id.preload_employee',
                                      readonly=0)


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def _get_available_contracts_domain(self):
        company_id = self.env.company
        domain = [('contract_ids.state', 'in', ('open', 'close')), ('company_id', '=', company_id.id)]

        if not company_id.preload_employee:
            domain = [(False, '=', True)]

        return domain
