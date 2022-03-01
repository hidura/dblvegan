# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd. (<http://devintellecs.com>).
#
##############################################################################
from odoo import models, fields, api, _
from datetime import datetime as dt
import time
from odoo.exceptions import UserError
from datetime import date


class BankReconciliation(models.Model):
    _name = "bank.reconciliation"
    _description = "Bank Reconciliation"

    name = fields.Char(string='Reference', required="1", default="/")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company, required=True,
                                 index=True)
    account_rec_id = fields.Many2one('account.account', string='Account')
    journal_id = fields.Many2one('account.journal', string='Journal')
    journal_op_id = fields.Many2one('account.journal', string='2nd Journal')
    start_balance = fields.Float(string='Starting Balance')
    end_balance = fields.Float(string='Ending Balance', required="1")
    journal_entry_ids = fields.Many2many('account.move.line', 'account_move_line_rel', 'journal_ids', 'move_ids',
                                         string="Journal Entries")
    state = fields.Selection([('draft', 'Draft'), ('close', 'Close')], string='State', default="draft")
    start_date = fields.Date(string='Start Date', required="1", default=date(date.today().year, 1, 1))
    end_date = fields.Date(string='End Date', required="1", default=fields.Date.today())

    bank_statement = fields.Float(string='Balance as per bank statement', compute='_compute_bank_statement')
    bank_account = fields.Float(string='Balance as per bank account', compute='_compute_bank_account')
    less_unrepresented_amount = fields.Float(string='Less Unrepresented Amount',
                                             compute='_compute_unrepresented_amount')
    deposit_not_credited_bank = fields.Float(string='Add deposit not credited by bank',
                                             compute='_compute_credited_bank')
    differance = fields.Float(string='Differance', compute='_compute_differance')
    currency_id = fields.Many2one('res.currency', string='Moneda/Divisa')

    @api.onchange('account_rec_id', 'end_date')
    def onchange_account_end_date(self):
        if self.account_rec_id and self.end_date:
            self.start_balance = self.search([
                ('account_rec_id', '=', self.account_rec_id.id),
                ('state', '=', 'close')
            ], order='end_date desc', limit=1).end_balance

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        if self.journal_id and self.journal_id.currency_id:
            self.currency_id = self.journal_id.currency_id.id

    def action_confirm(self):
        if self.differance > 0.01:
            raise UserError(_('Reconcile Balance and Ending Balance is should be same'))

        else:
            self.state = 'close'
        return True

    @api.depends('end_balance')
    def _compute_bank_statement(self):
        for rec in self:
            # if rec.end_balance > 0.00:
            rec.bank_statement = rec.end_balance or 0

    # @api.depends('end_balance','start_balance')
    @api.depends('bank_statement', 'less_unrepresented_amount', 'deposit_not_credited_bank', 'bank_account')
    def _compute_differance(self):
        # calc = abs(self.end_balance - self.start_balance - self.less_unrepresented_amount - self.deposit_not_credited_bank - self.bank_account)
        for rec in self:
            calc = 0
            try:
                calc = abs(rec.bank_statement
                           - rec.less_unrepresented_amount
                           + rec.deposit_not_credited_bank
                           - rec.bank_account
                           )
            except:
                calc = 0
            rec.differance = calc or 0  # abs(self.end_balance - self.start_balance - self.less_unrepresented_amount - self.deposit_not_credited_bank - self.bank_account)

    @api.depends('journal_entry_ids', 'start_balance', 'currency_id')
    def _compute_bank_account(self):
        for rec in self:
            total_debit = 0.0
            total_credit = 0.0
            if rec.journal_entry_ids:
                for journal_entry in rec.journal_entry_ids:
                    if rec.currency_id.name != 'DOP':
                        amount = journal_entry.amount_currency
                        total_debit += amount if amount > 0 else 0
                        total_credit += abs(amount) if amount < 0 else 0
                    else:
                        total_debit += journal_entry.debit
                        total_credit += journal_entry.credit

            rec.bank_account = (total_debit - total_credit) + rec.start_balance

    @api.depends('journal_entry_ids', 'currency_id')
    def _compute_unrepresented_amount(self):
        for rec in self:
            total_credit = 0.0
            if rec.journal_entry_ids:
                for journal_entry in rec.journal_entry_ids:
                    if not journal_entry.is_bank_reconcile:
                        if rec.currency_id.name != 'DOP':
                            amount = journal_entry.amount_currency
                            total_credit += abs(amount) if amount < 0 else 0
                        else:
                            total_credit += journal_entry.credit

            rec.less_unrepresented_amount = total_credit

    @api.depends('journal_entry_ids', 'currency_id')
    def _compute_credited_bank(self):
        for rec in self:
            total_debit = 0.0
            if rec.journal_entry_ids:
                for journal_entry in rec.journal_entry_ids:
                    if not journal_entry.is_bank_reconcile:
                        if rec.currency_id.name != 'DOP':
                            amount = journal_entry.amount_currency
                            total_debit += amount if amount > 0 else 0
                        else:
                            total_debit += journal_entry.debit

            rec.deposit_not_credited_bank = total_debit

    def to_conciliation(self):
        view = {
            'name': 'Conciliation',
            'view_mode': 'tree',
            'res_model': 'account.move.line',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('dev_bank_reconciliation.conciliation_list_view').id,
            'domain': [('id', 'in', self.journal_entry_ids.ids)],  # [i.id for i in self.journal_entry_ids])]
        }
        return view

    def button_dummy(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_bank_reconcile = fields.Boolean(string="IS Reconcile")
    is_not_confirm = fields.Boolean(string="Is Not Confirm")

    def action_make_confirm(self):
        if self.env.context.get('state') == 'close':
            raise UserError(_('You can not reconcile the line in close state'))
        else:
            self.is_bank_reconcile = True

        return True

    def action_cancle_confirm(self):
        if self.env.context.get('state') == 'close':
            raise UserError(_('You can not un-reconcile the line in close state'))
        else:
            self.is_bank_reconcile = False

        return True


class WizardAddLines(models.TransientModel):
    _name = 'wizard.add.move.lines'
    _description = 'Wizard Add Move Lines'

    account_id = fields.Many2one('account.account')
    journal_id = fields.Many2one('account.journal')
    move_line_ids = fields.Many2many('account.move.line')

    @api.model
    def default_get(self, fields):
        res = super(WizardAddLines, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        statement_obj = self.env['bank.reconciliation'].browse(active_id)
        res.update({
            'journal_id': statement_obj.journal_id.id,
            'account_id': statement_obj.account_rec_id.id,
        })
        return res

    def set_move_line_ids(self):
        active_id = self.env.context.get('active_id')
        statement_obj = self.env['bank.reconciliation'].browse(active_id)

        line_ids = []
        for ml in self.move_line_ids:
            line_ids.append((4, ml.id))

        if line_ids:
            statement_obj.journal_entry_ids = line_ids

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
