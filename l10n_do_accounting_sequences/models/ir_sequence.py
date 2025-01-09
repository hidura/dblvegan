# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountJournalDocumentType(models.Model):
    _inherit = 'l10n_do.account.journal.document_type'

    l10n_do_number_next = fields.Integer(string='Próximo número')
    l10n_do_warning_number = fields.Integer(string='Alerta')
    l10n_do_max_number = fields.Integer(string='Número Máximo')
