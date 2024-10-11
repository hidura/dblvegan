# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class account_payment_select_cost_account(models.Model):
    _inherit = 'account.payment'

    force_destination_account_id = fields.Many2one(
        'account.account', string="Cost Account")

    @api.depends('reconciled_invoice_ids', 'payment_type', 'partner_type', 'partner_id', 'force_destination_account_id')
    def _compute_destination_account_id(self):
        self.destination_account_id = False
        for payment in self:
            if payment.reconciled_invoice_ids:
                payment.destination_account_id = payment.reconciled_invoice_ids[0].mapped(
                    'line_ids.account_id').filtered(
                    lambda account: account.user_type_id.type in ('receivable', 'payable'))[0]
            elif payment.payment_type == 'transfer':
                if not payment.company_id.transfer_account_id.id:
                    raise UserError(
                        _('There is no Transfer Account defined in the accounting settings. Please define one to be able to confirm this transfer.'))
                payment.destination_account_id = payment.company_id.transfer_account_id.id
            elif payment.partner_id:
                partner = payment.partner_id.with_context(force_company=payment.company_id.id)
                if payment.partner_type == 'customer':
                    payment.destination_account_id = partner.property_account_receivable_id.id
                else:
                    payment.destination_account_id = partner.property_account_payable_id.id
            elif payment.partner_type == 'customer':
                default_account = self.env['ir.property'].with_context(force_company=payment.company_id.id).get(
                    'property_account_receivable_id', 'res.partner')
                payment.destination_account_id = default_account.id
            elif payment.partner_type == 'supplier':
                default_account = self.env['ir.property'].with_context(force_company=payment.company_id.id).get(
                    'property_account_payable_id', 'res.partner')
                payment.destination_account_id = default_account.id

        if self.force_destination_account_id:
            self.destination_account_id = self.force_destination_account_id.id
