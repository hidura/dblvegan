# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    tss_report = fields.Boolean(string='Para Reporte de TSS')

    tss_columns = fields.Many2many('hr.tss_report.tags', 'rule_tag_rel', 'rule_id', 'tag_id', string='TSS Columnas',
                               help='Indique las Columnas '
                                    'donde se introducira el valor de '
                                    'esta novedad en el reporte de '
                                    'Autodeterminacion de la TSS.')


