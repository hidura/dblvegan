# -*- coding: utf-8 -*-
import logging
import json

from odoo import models, fields, api, _



class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

  
    def _compute_invoice_id(self):

        lines = False
        if self._context.get('active_model') == 'account.move':
            lines = self.env['account.move'].browse(self._context.get('active_ids', [])).line_ids
        elif self._context.get('active_model') == 'account.move.line':
            lines = self.env['account.move.line'].browse(self._context.get('active_ids', []))
        else:
            pass

        if lines:
            self.source_invoice= lines[0].move_id.id
        else:
            self.source_invoice = False

    source_invoice = fields.Integer(
        string=u'Source Invoice Id', compute='_compute_invoice_id')
