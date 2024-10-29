from odoo import models, _
from odoo.exceptions import UserError


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _create_invoice_receivable_lines(self, data):
        if self.config_id.invoice_journal_id.l10n_latam_use_documents:
            data.update({
                'combine_invoice_receivable_lines': {},
                'split_invoice_receivable_lines': {},
            })
            return data
        return super(PosSession, self)._create_invoice_receivable_lines(data)

    def _create_bank_payment_moves(self, data):
        if self.config_id.invoice_journal_id.l10n_latam_use_documents:
            data.update({
                'payment_method_to_receivable_lines': {},
                'payment_to_receivable_lines': {},
            })
            return data
        return super(PosSession, self)._create_bank_payment_moves(data)

    def _create_cash_statement_lines_and_cash_move_lines(self, data):
        if self.config_id.invoice_journal_id.l10n_latam_use_documents:
            AccountMoveLine = self.env['account.move.line']
            data.update({
                'split_cash_receivable_lines': AccountMoveLine,
                'split_cash_statement_lines': AccountMoveLine,
                'combine_cash_receivable_lines': AccountMoveLine,
                'combine_cash_statement_lines': AccountMoveLine
            })
            return data
        return super(PosSession, self)._create_cash_statement_lines_and_cash_move_lines(data)

    def _loader_params_res_company(self):
        result = super()._loader_params_res_company()
        result['search_params']['fields'].extend([
            'company_address',
            # 'l10n_do_ncf_expiration_date'
        ])
        return result

    def _loader_params_res_partner(self):
        result = super()._loader_params_res_partner()
        result['search_params']['fields'].extend(['l10n_do_dgii_tax_payer_type'])
        return result
