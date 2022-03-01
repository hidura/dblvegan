# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    preload_employee = fields.Boolean(default=True, string='Preload of Employee')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    preload_employee = fields.Boolean(string='Preload of Employee',
                                      related='company_id.preload_employee',
                                      readonly=0)
