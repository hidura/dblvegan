# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PayslipInputImport(models.Model):
    _name = "payslip.input.import"
    _description = 'Import Payslip Input'

    name = fields.Char()

    active = fields.Boolean(default=1)
    input_id = fields.Many2one('hr.payslip.input.type', string='Novedad')
    code = fields.Char(related='input_id.code', string='Codigo')
    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True)
    amount = fields.Float(string="Importe")
    frecuency_type = fields.Selection(
        [
            ('fijo', 'Fijo'),
            ('variable', 'Variable')
        ], string="Tipo de frecuencia", default='fijo')

    apply_on = fields.Selection(
        [
            ('1', 'Primera Quincena'),
            ('2', 'Segunda Quincena'),
            ('3', 'Primera y. Segunda Quincena')
        ], string="Aplicar en", default='1'
    )

    frecuency_number = fields.Integer(string="Numero de veces", default=1)
    start_date = fields.Date(string="Fecha inicial", )
    end_date = fields.Date(string="Fecha final") #, compute='_calc_date_end', store=True)

    to_force = fields.Boolean('Solo Nomina Especiales')
    notes = fields.Text('Descripcion/Notas')

    @api.depends('input_id', 'code')
    def name_get(self):
        result = []
        for r in self:
            name = '[%s] %s' % (r.code, r.input_id.name)
            result.append((r.id, name))
        return result

    @api.onchange('frecuency_number', 'start_date', 'apply_on')
    def _calc_date_end(self):
        for i in self:
            if i.start_date:
                end_date = ''
                num_veces = i.frecuency_number -1 if i.frecuency_number > 0 else 1
                if i.apply_on in ('1', '2'):
                    end_date = fields.Date.add(i.start_date, months=num_veces)

                elif i.apply_on == '3':
                    end_date = fields.Date.add(i.start_date, months=int(num_veces/2), days=15)

                i.end_date = end_date
