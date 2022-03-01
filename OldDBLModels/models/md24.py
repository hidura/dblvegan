# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PaymentWithoutInvoiceReport(models.TransientModel):
    _name = 'payment.without.invoice.report'
    _description = 'Payment Without Invoice Report'

    line_ids = fields.One2many('payment.without.invoice.report.line', 'report_id')

    def generate(self):
        payments = self.env['account.payment'].search([
            ('company_id', '=', self.env.company.id),
            ('payment_type', '=', 'inbound'),
            ('state', 'in', ['posted', 'send', 'reconciled']),
        ]).filtered(lambda p: not p.reconciled_invoice_ids)

        payment_data = []
        for p in payments:
            payment_data.append((
                0, 0, {
                    'partner_id': p.partner_id.id,
                    'payment_id': p.id,
                    'currency_id': p.currency_id.id,
                    'amount': p.amount,
                    'journal_id': p.journal_id.id,
                    'payment_date': p.payment_date,
                    'communication': p.communication,
                }
            ))

        self.line_ids = payment_data

        view = {
            'name': 'Pagos sin Aplicar',
            'view_mode': 'tree',
            'res_model': 'payment.without.invoice.report.line',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('payment_without_invoice_report.payment_without_invoice_report_line_tree_view').id,
            'domain': [('report_id', '=', self.id)]
        }

        return view


class PaymentWithoutInvoiceReportLine(models.TransientModel):
    _name = 'payment.without.invoice.report.line'
    _description = 'Payment Without Invoice Report Line'

    report_id = fields.Many2one('payment.without.invoice.report')

    partner_id = fields.Many2one('res.partner', string='Customer')
    payment_id = fields.Many2one('account.payment', string='Nombre')
    payment_date = fields.Date('Fecha')
    currency_id = fields.Many2one('res.currency')
    journal_id = fields.Many2one('account.journal', string='Diario')
    amount = fields.Monetary('Importe')
    communication = fields.Char('Circular')
