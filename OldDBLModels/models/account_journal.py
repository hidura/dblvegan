# -*- coding: utf-8 -*-
from odoo import models, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    @api.constrains('type')
    def _check_type(self):
        # Disable the constraint for POS journals
        pass
