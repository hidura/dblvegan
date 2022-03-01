# -*- coding: utf-8 -*-
import logging
import calendar
from datetime import datetime as dt

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ReportIncomeWithholding(models.TransientModel):
    _name = 'income.withholding.report'
    _description = 'Wizard Report Income Withholding'

    period = fields.Char('Period', required=1)
    move_ids = fields.One2many('income.withholding.report.lines', 'report_id', string='lines')

    def generate_report(self):
        period = dt.strptime(self.period, '%m/%Y')

        month, year = self.period.split('/')
        last_day = calendar.monthrange(int(year), int(month))[1]
        start_date = '{}-{}-01'.format(year, month)
        end_date = '{}-{}-{}'.format(year, month, last_day)

        invoice_ids = self.env['account.move'].search([
            ('invoice_payment_state', '=', 'paid'),

            ('payment_date', '>=', start_date),
            ('payment_date', '<=', end_date),
            ('company_id', '=', self.env.company.id),
            ('income_withholding', '!=', 0)
            ('type', 'in', ['in_invoice']),
        ])
        #.filtered(lambda inv: self.get_date_tuple(inv.payment_date) ==
        #         (period.year, period.month))

        lines = []
        _logger.info(invoice_ids)
        for invoice in invoice_ids:
            lines.append(
                (0, 0, {'report_id': self.id,
                        'move_id': invoice.id,
                        'amount': invoice.amount_untaxed,
                        'amount_isr': invoice.income_withholding,
                        'amount_tax': invoice.invoiced_itbis,
                        'description': invoice.invoice_line_ids[0].name,
                        })
            )

        self.move_ids = lines

        _logger.info(lines)

        view = {
            'name': 'Income Withholding',
            'view_mode': 'tree',
            'res_model': 'income.withholding.report.lines',
            'type': 'ir.actions.act_window',
            'view_id':
                self.env.ref('report_income_withholding.view_income_withholding_lines').id,
            'domain': [('report_id', '=', self.id)]
        }

        return view


class ReportIncomeWithholdingLines(models.TransientModel):
    _name = 'income.withholding.report.lines'
    _description = 'Wizard Report Income Withholding Lines'

    report_id = fields.Many2one('income.withholding.report')

    move_id = fields.Many2one('account.move')
    number = fields.Char(related="move_id.l10n_latam_document_number")
    date = fields.Date(related='move_id.date')
    payment_ref = fields.Char()
    parnert_id = fields.Many2one(related='move_id.partner_id')
    description = fields.Char()
    amount = fields.Float()
    amount_isr = fields.Float()
    amount_tax = fields.Float()
