# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TSSTipoNomina(models.Model):
    _name = "tss.tipo_nomina"
    _description = 'TSS Tipo Nomina'

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Code", help='Codigo de Identificacion Suministrado por la TSS')
