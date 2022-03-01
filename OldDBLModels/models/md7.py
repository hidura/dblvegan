# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HrEmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'

    tipo_nomina_id = fields.Many2one('tss.tipo_nomina', string='Nomina TSS')
    nss = fields.Char(string='NSS')

    nombres = fields.Char(string="Nombres")
    apellido_paterno = fields.Char(string="Apellido Paterno")
    apellido_materno = fields.Char(string="Apellido Materno")
