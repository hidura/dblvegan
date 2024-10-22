from odoo import models, fields, api


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    def _get_l10n_do_payment_form(self):
        return self.env["account.journal"].sudo()._get_l10n_do_payment_form()

    l10n_do_payment_form = fields.Selection(
        selection="_get_l10n_do_payment_form",
        string="Forma de Pago",
    )
    use_credit_note = fields.Boolean("Usar para Nota de Crédito")
    type = fields.Selection(selection_add=[('credit_note', 'Nota de Crédito')])

    @api.onchange("journal_id")
    def change_cash_journal_id(self):
        self.l10n_do_payment_form = self.journal_id.l10n_do_payment_form

    @api.depends('journal_id', 'split_transactions')
    def _compute_type(self):
        for pm in self:
            if pm.journal_id.type in {'cash', 'bank'}:
                pm.type = pm.journal_id.type
            elif pm.use_credit_note:
                pm.type = 'credit_note'
            else:
                pm.type = 'pay_later'

    # def write(self, vals):
    #     if vals.get('use_credit_note', False):
    #         journal_id = self.env['account.journal'].search([
    #             ('type', '=', 'sale'),
    #             ('l10n_latam_use_documents', '=', True),
    #             ('company_id', '=', self.env.company.id),
    #         ], limit=1)
    #         vals['journal_id'] = journal_id.id
    #     return super(PosPaymentMethod, self).write(vals)
