# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    tss_force_month = fields.Boolean(default=True, string='Force the same month for TSS')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tss_force_month = fields.Boolean(related='company_id.tss_force_month', readonly=0)
