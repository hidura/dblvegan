# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class ConfigInterface(models.Model):
    _name = 'config.interface'
    _description = 'Config Interface'

    name = fields.Char(string="Nombre")
    config_type = fields.Selection(
        string=u'Tipo',
        selection=[('pos', 'Punto de Venta'), ('invoice', u'Facturación')],
        default='pos')
   
    @api.model
    def get_config(self, config_interface_id=None):
        """
        function get config...
        :return: dict
        """
        res = {}
        config_id = self.browse(
            config_interface_id) if config_interface_id else self
        for key, value in config_id.read()[0]:
            res[key] = value
        return res
