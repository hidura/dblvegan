from odoo import models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):

            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                # if len(liquidity_lines) != 1:
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, the journal items must "
                #         "include one and only one outstanding payments/receipts account.",
                #         move.display_name,
                #     ))

                # if len(counterpart_lines) != 1:
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, the journal items must "
                #         "include one and only one receivable/payable account (with an exception of "
                #         "internal transfers).",
                #         move.display_name,
                #     ))

                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same currency.",
                        move.display_name,
                    ))

                # if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, the journal items must "
                #         "share the same partner.",
                #         move.display_name,
                #     ))
                if pay.payment_type == 'inbound':
                    partner_type = 'customer'
                else:
                    partner_type = 'supplier'

                # if counterpart_lines.account_id.account_type == 'asset_receivable':
                #     partner_type = 'customer'
                # else:
                #     partner_type = 'supplier'

                liquidity_lines = liquidity_lines and liquidity_lines[0]

                liquidity_amount = liquidity_lines and liquidity_lines.amount_currency

                move_vals_to_write.update({
                    'currency_id': liquidity_lines.currency_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                payment_vals_to_write.update({
                    'amount': abs(liquidity_amount),
                    'partner_type': partner_type,
                    'currency_id': liquidity_lines.currency_id.id,
                    # 'destination_account_id': counterpart_lines.account_id.id,
                    'destination_account_id': pay.destination_account_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                if liquidity_amount > 0.0:
                    payment_vals_to_write.update({'payment_type': 'inbound'})
                elif liquidity_amount < 0.0:
                    payment_vals_to_write.update({'payment_type': 'outbound'})

            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    # def _synchronize_from_moves(self, changed_fields):
    #     """ Update the account.bank.statement.line regarding its related account.move.
    #     Also, check both models are still consistent.
    #     :param changed_fields: A set containing all modified fields on account.move.
    #     """
    #     if self._context.get('skip_account_move_synchronization'):
    #         return
    #
    #     for st_line in self.with_context(skip_account_move_synchronization=True):
    #         move = st_line.move_id
    #         move_vals_to_write = {}
    #         st_line_vals_to_write = {}
    #
    #         if 'line_ids' in changed_fields:
    #             liquidity_lines, suspense_lines, _other_lines = st_line._seek_for_lines()
    #             company_currency = st_line.journal_id.company_id.currency_id
    #             journal_currency = st_line.journal_id.currency_id if st_line.journal_id.currency_id != company_currency\
    #                 else False
    #             _logger.info('liquidity_lines: %s', liquidity_lines.read())
    #             if len(liquidity_lines) != 1:
    #                 raise UserError(_(
    #                     "The journal entry %s reached an invalid state regarding its related statement line.\n"
    #                     "To be consistent, the journal entry must always have exactly one journal item involving the "
    #                     "bank/cash account."
    #                 ) % st_line.move_id.display_name)
    #
    #             st_line_vals_to_write.update({
    #                 'payment_ref': liquidity_lines.name,
    #                 'partner_id': liquidity_lines.partner_id.id,
    #             })
    #
    #             # Update 'amount' according to the liquidity line.
    #
    #             if journal_currency:
    #                 st_line_vals_to_write.update({
    #                     'amount': liquidity_lines.amount_currency,
    #                 })
    #             else:
    #                 st_line_vals_to_write.update({
    #                     'amount': liquidity_lines.balance,
    #                 })
    #
    #             if len(suspense_lines) > 1:
    #                 raise UserError(_(
    #                     "%s reached an invalid state regarding its related statement line.\n"
    #                     "To be consistent, the journal entry must always have exactly one suspense line.", st_line.move_id.display_name
    #                 ))
    #             elif len(suspense_lines) == 1:
    #                 if journal_currency and suspense_lines.currency_id == journal_currency:
    #
    #                     # The suspense line is expressed in the journal's currency meaning the foreign currency
    #                     # set on the statement line is no longer needed.
    #
    #                     st_line_vals_to_write.update({
    #                         'amount_currency': 0.0,
    #                         'foreign_currency_id': False,
    #                     })
    #
    #                 elif not journal_currency and suspense_lines.currency_id == company_currency:
    #
    #                     # Don't set a specific foreign currency on the statement line.
    #
    #                     st_line_vals_to_write.update({
    #                         'amount_currency': 0.0,
    #                         'foreign_currency_id': False,
    #                     })
    #
    #                 else:
    #
    #                     # Update the statement line regarding the foreign currency of the suspense line.
    #
    #                     st_line_vals_to_write.update({
    #                         'amount_currency': -suspense_lines.amount_currency,
    #                         'foreign_currency_id': suspense_lines.currency_id.id,
    #                     })
    #
    #             move_vals_to_write.update({
    #                 'partner_id': liquidity_lines.partner_id.id,
    #                 'currency_id': (st_line.foreign_currency_id or journal_currency or company_currency).id,
    #             })
    #
    #         move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
    #         st_line.write(move._cleanup_write_orm_values(st_line, st_line_vals_to_write))
