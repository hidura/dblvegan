# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResUsers(models.Model):

    _name = 'res.users'
    _inherit = 'res.users'

    config_interface_id = fields.Many2one(
        string=u'Parámetro',
        comodel_name='config.interface',
        ondelete='set null',
        domain="[('config_type','=','invoice')]"
    )