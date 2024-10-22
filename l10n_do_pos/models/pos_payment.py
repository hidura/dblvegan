from odoo import models, fields, api, _


class PosPayment(models.Model):
    _inherit = "pos.payment"

    def _get_payment_values(self, payment):
        amount = sum(payment.mapped('amount')) if len(payment) > 1 else payment.amount
        payment = payment[0] if len(payment) > 1 else payment
        payment_method = payment.payment_method_id
        payment_session = payment.session_id

        return {
            'amount': amount,
            'payment_type': 'inbound' if amount >= 0 else 'outbound',
            'date': payment.payment_date,
            'partner_id': payment.partner_id.id if payment.partner_id else False,
            'currency_id': payment.currency_id.id,
            'pos_session_id': payment_session.id,
            'ref': _('%s POS payments from %s') % (payment_method.name, payment_session.name),
            'pos_payment_method_id': payment_method.id,
            'journal_id': payment_method.journal_id.id,
        }

    def _create_payment_moves(self, is_reverse=False):

        if self and not self.mapped('session_id.config_id.invoice_journal_id')[0].l10n_latam_use_documents:
            return super(PosPayment, self)._create_payment_moves(is_reverse)

        result = self.env['account.move']
        for payment in self.filtered(lambda p: not p.payment_method_id.use_credit_note and p.amount > 0):
            order = payment.pos_order_id
            payment_method = payment.payment_method_id

            if payment_method.type == 'pay_later' or order.currency_id.is_zero(payment.amount):
                continue

            account_payment = self.env['account.payment'].create(
                self._get_payment_values(payment)
            )
            account_payment.action_post()
            account_payment.move_id.write({
                'pos_payment_ids': payment.ids,
            })
            payment.write({
                'account_move_id': account_payment.move_id.id
            })
            result |= account_payment.move_id

        for credit_note in self.filtered(lambda p: p.payment_method_id.use_credit_note and p.name):
            account_move_credit_note = self.env['account.move'].search([
                ('partner_id', '=', credit_note.partner_id.id),
                ('l10n_do_fiscal_number', '=', credit_note.name),
                ('move_type', '=', 'out_refund'),
                ('company_id', '=', self.env.company.id),
                ('state', '=', 'posted')
                ], limit=1
            )

            if account_move_credit_note and credit_note.amount > 0:
                account_move_credit_note.write({
                    'pos_payment_ids': credit_note.ids,
                })
                credit_note.write({
                    'account_move_id': account_move_credit_note.id
                })
                result |= account_move_credit_note
        return result


    # def _create_payment_moves(self):
    #     """
    #     Interviene la creacion del asiento contable para verificar si el metodo de pago usado es tipo Nota de Credito,
    #     de serlo se usa dicha NC como metodo de pago.
    #     :return: account.move
    #     """
    #     moves = self.env['account.move']
    #     records = self
    #     for payment in self:
    #         order = payment.pos_order_id
    #         payment_method = payment.payment_method_id
    #         if payment_method.type == 'credit_note':
    #             info = order.credit_note_info_from_ui(payment.note)
    #             credit_note_id = self.env[info['model']].browse(info['id'])
    #             payment.write({'res_model': info['model']})
    #             moves |= credit_note_id.account_move if credit_note_id._name == 'pos.order' else credit_note_id
    #             records -= payment
    #         if payment_method.type == 'credit_note':
    #             info = order.credit_note_info_from_ui(payment.note)
    #             credit_note_id = self.env[info['model']].browse(info['id'])
    #             payment.write({'res_model': info['model']})
    #             moves |= credit_note_id.account_move if credit_note_id._name == 'pos.order' else credit_note_id
    #             records -= payment
    #
    #     rstl = super(PosPayment, records)._create_payment_moves()
    #     rstl |= moves
    #     return rstl
