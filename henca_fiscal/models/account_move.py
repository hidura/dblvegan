# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
import logging
import json
import logging
import re

_logger = logging.getLogger(__name__)


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    payment_form = fields.Selection([
        ("cash", "Efectivo"),
        ("bank", u"Cheque / Transferencia / Depósito"),
        ("card", u"Tarjeta Crédito / Débito"),
        ("credit", u"A Crédito"),
        ("swap", "Permuta"),
        ("bond", "Bonos o Certificados de Regalo"),
        ("others", "Otras Formas de Venta")
    ],
        string="Forma de Pago Impresora Fiscal",
    )


class AccountMove(models.Model):
    _inherit = "account.move"

    fiscal_nif = fields.Char("NIF", default="false", copy=False)
    fiscal_printed = fields.Boolean(string='Imprimido Fiscal', copy=False)
    show_print_fiscal = fields.Boolean(
        string='Mostrar boton para imprimir fiscal ?',
        compute='_compute_fiscal_printer',
        copy=False,
    )

    ipf_printer_id = fields.Many2one(
        string='Impresora Fiscal',
        comodel_name='ipf.printer.config',
        compute='_compute_fiscal_printer'
    )
    ipf_host = fields.Char(
        string='IPF Host',
        related='ipf_printer_id.host'
    )
    ipf_type = fields.Selection(
        string="IPF Impresora",
        readonly=True,
        related='ipf_printer_id.ipf_type'
    )
    ipf_print_copy_number = fields.Integer(
        string="Numero de Copias",
        related='ipf_printer_id.print_copy_number'
    )
    print_manual_copy = fields.Boolean(
        string="Imprimir copia manual",
        related='ipf_printer_id.print_manual_copy'
    )
    partner_vat = fields.Char(
        string='RNC',
        related='partner_id.vat',
        readonly=True
    )
    invoice_date_currency_rate = fields.Float(
        string="Tasa de Cambio Fecha Factura",
        compute="_compute_invoice_date_currency_rate",
        default=0.0,
    )
    dop_currency_id = fields.Many2one(
        comodel_name='res.currency',
        default=lambda self: self.env.ref('base.DOP').id,
        string='DOP Currency ID',
        readonly=True
    )

    def _compute_invoice_date_currency_rate(self):
        for move in self:
            if move.company_id.currency_id.id != move.currency_id.id:
                # If date not specified on the invoice default to today's date
                invoice_date = move.invoice_date if move.invoice_date else date.today()
                currency_rates = self.env['res.currency.rate'].search([
                    ('company_id', '=', move.company_id.id),
                    ('currency_id', '=', move.currency_id.id),
                    ('name', '<=', invoice_date)
                ], order='name desc', limit=1)

                move.invoice_date_currency_rate = currency_rates.inverse_company_rate if currency_rates else 1
            else:
                move.invoice_date_currency_rate = 0.0

    def configurate_fiscal_printer_invoice(self):
        for move in self:
            move._compute_fiscal_printer()

    def _compute_fiscal_printer(self):
        for move in self:
            ipf_printer_id = move.env['ipf.printer.config'].search([
                ('user_ids', '=', move.user_id.id)
            ])

            if len(ipf_printer_id) > 1:
                ipf_printer_id = ipf_printer_id[0]

            move.ipf_printer_id = ipf_printer_id.id if ipf_printer_id else False
            if move.move_type == 'out_invoice' or move.move_type == 'out_refund':
                move.show_print_fiscal = True
            else:
                move.show_print_fiscal = False

    @api.model
    def action_invoice_printed(self, invoice_id, fiscal_nif):
        if invoice_id:
            invoice = self.browse([invoice_id])
            if invoice:
                invoice.write({'fiscal_printed': True, 'fiscal_nif': fiscal_nif})

    @api.depends('move_type', 'line_ids.amount_residual')
    def _compute_payments_widget_reconciled_info(self):
        payment_vals = super(AccountMove, self)._compute_payments_widget_reconciled_info()
        for move in self:
            if move.invoice_payments_widget and move.move_type in ['out_invoice', 'out_refund']:
                for payment in move.invoice_payments_widget['content']:
                    if payment['account_payment_id']:
                        payment_id = self.env['account.payment'].browse(payment['account_payment_id'])
                        payment_form = payment_id.journal_id.l10n_do_payment_form == 'bank' and 'check' or payment_id.journal_id.l10n_do_payment_form
                        journal_name = payment_id.journal_id.name
                        payment['ipf_payment_form'] = payment_form or False
                        payment['ipf_payment_description'] = journal_name
                    elif payment['move_id']:
                        move_id = self.env['account.move'].browse(payment['move_id'])
                        ref = move_id.ref
                        if ref:
                            payment_form = 'credit_note' if 'B04' in ref else 'other'
                            payment['ipf_payment_form'] = payment_form or False
                            payment['ipf_payment_description'] = ref
        return payment_vals

    def get_payment_data(self, data):
        currency_rate = self.invoice_date_currency_rate
        payments_info = []
        payments = data
        if payments:
            for con in payments['content']:
                if con.get('account_payment_id'):
                    pay = {
                        'type': con['ipf_payment_form'],
                        'description': con['ipf_payment_description'],
                        'amount': (con['amount'] * currency_rate) if currency_rate > 0 else con['amount'],
                    }
                    payments_info.append(pay)
        return payments_info

    def get_ncf_type(self, ncf):
        n_type = "nofiscal"
        ncf = ncf[9:11] if len(ncf) == 19 else ncf[1:3]
        if ncf == "02":
            n_type = "final"
        elif ncf in ["01", "15"]:
            n_type = "fiscal"
        elif ncf == "14":
            n_type = "special"

        return n_type

    def get_invoice_format(self):

        ncf_type = self.get_ncf_type(self.ref if self.move_type == "out_invoice" else self.origin_out)

        invoice_dict = {
            'do_print': False,
            'printed': self.fiscal_printed,
            'type': ncf_type,
            'ncf': self.ref,
            'cashier': self.env.user.id,
            'seller': self.user_id.name,
            'other_curr_name': self.currency_id.name if self.currency_id != self.company_id.currency_id else False,
            'client': self.partner_id.name,
            'rnc': self.partner_id.vat,
            'invoice_currency_id': self.currency_id.id,
            'amount_total': self.amount_total,
            'amount_total_signed': self.amount_total_signed,
            'amount_residual': self.amount_residual,
            'invoice_date_currency_rate': self.invoice_date_currency_rate,
        }

        if self.move_type == "out_invoice":
            if not invoice_dict['type']:
                invoice_dict.update({'type': 'final'})
        elif self.move_type == "out_refund":

            invoice_dict.update({'ref_ncf': self.origin_out})
            if ncf_type == "final":
                invoice_dict.update({'type': 'final_note'})
            elif ncf_type in ["fiscal", "gov"]:
                invoice_dict.update({'type': 'fiscal_note'})
            elif ncf_type == "special":
                invoice_dict.update({'type': 'special_note'})

        if self.fiscal_position_id:
            invoice_dict.update({'fiscal_position': self.fiscal_position_id})

        total_discount = 0.0
        invoice_items_list = []
        for line in self.invoice_line_ids:
            invoice_items_dict = {}
            description = re.sub(r'^\[[\s\d]+\]\s+', '', line.name).strip()
            description = re.sub(r'[^\w.]', ' ', description)

            extra_description = line.name.splitlines()
            if len(extra_description) > 1:
                invoice_items_dict["extra_description"] = extra_description
            else:
                invoice_items_dict["extra_description"] = []
            tax_amount = line.tax_ids and line.tax_ids[0].amount or 0
            tax_amount_type = line.tax_ids and line.tax_ids[0].amount_type
            price_include = line.tax_ids and line.tax_ids[0].price_include
            price_unit = line.price_unit
            if not price_include:
                price_unit = price_unit * (tax_amount / 100.0 + 1)

            invoice_items_dict["description"] = description
            invoice_items_dict["quantity"] = line.quantity
            invoice_items_dict["itbis"] = int(tax_amount)
            invoice_items_dict["price"] = price_unit
            invoice_items_dict["price_unit"] = price_unit
            invoice_items_dict["discount"] = line.discount
            invoice_items_dict["default_code"] = line.product_id.default_code
            invoice_items_dict["barcode"] = line.product_id.barcode
            invoice_items_dict["currency_id"] = line.currency_id.id
            invoice_items_dict["name"] = line.name
            invoice_items_dict["tax_amount_type"] = tax_amount_type
            invoice_items_dict["tax_amount"] = int(tax_amount)
            invoice_items_dict["invoice_date_currency_rate"] = line.invoice_date_currency_rate
            invoice_items_dict["currency_id"] = line.currency_id.id

            if line.discount > 0:
                total_discount += line.quantity * line.price_unit * (line.discount / 100.0)
            invoice_items_list.append(invoice_items_dict)

        invoice_dict["items"] = invoice_items_list
        invoice_dict["total_discount"] = total_discount

        payment_ids_list = []
        # import ipdb; ipdb.set_trace()
        payment_ids_list = self.get_payment_data(self.invoice_payments_widget) if self.invoice_payments_widget else []
        if len(payment_ids_list) == 0:
            payment_ids_list.append(
                dict(type="credit", description="Credito", amount=self.amount_total))

        amount_payment = 0.0
        for payment in payment_ids_list:
            amount_payment += payment["amount"]

        if amount_payment < self.amount_total:
            payment_ids_list.append(
                dict(type="credit", amount=self.amount_total - amount_payment))

        invoice_dict.update(
            dict(payments=payment_ids_list, invoice_id=self.id))

        invoice_dict['do_print'] = True

        # Henca Addionatal Data
        # invoice_dict = {}
        invoice_dict['name'] = self.name
        invoice_dict['invoice_user_id'] = self.invoice_user_id
        invoice_dict['ref'] = self.ref
        invoice_dict['origin_out'] = self.origin_out
        invoice_dict['partner_id'] = self.partner_id.id
        invoice_dict['partner_vat'] = self.partner_vat
        invoice_dict['invoice_line_ids'] = self.invoice_line_ids.ids
        invoice_dict['ipf_host'] = self.ipf_host
        invoice_dict['comment'] = self.narration
        invoice_dict['ipf_type'] = self.ipf_type
        invoice_dict['ipf_print_copy_number'] = self.ipf_print_copy_number
        invoice_dict['currency_id'] = self.currency_id.id
        invoice_dict['dop_currency_id'] = self.dop_currency_id.id

        lots = []
        pickings = self.env['stock.picking'].search([('origin', '=', self.invoice_origin)])
        for picking in pickings:
            for move in picking.move_ids:
                for move_line in move.move_line_ids:
                    if move_line.lot_id:
                        lots.append('SN: {}'.format(move_line.lot_id.name))
        if lots:
            invoice_dict['comment'] += ' '.join(lots)

        return invoice_dict

    def ipf_fiscal_print(self):
        pass

    def ipf_fiscal_copy(self):
        pass


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    invoice_date_currency_rate = fields.Float(
        related='move_id.invoice_date_currency_rate',
        string='Tasa',
    )
    tax_amount_type = fields.Char(
        string='Tax Computation',
        compute='_compute_tax_amount_and_type',
        store=True,
        readonly=True,
    )
    tax_amount = fields.Float(
        string='Tax Amount',
        compute='_compute_tax_amount_and_type',
        store=True,
        readonly=True,
    )

    @api.depends('tax_ids', 'product_id', 'price_unit')
    def _compute_tax_amount_and_type(self):
        for line in self:
            try:
                if line.tax_ids and line.price_unit:
                    tax_amount_list = [18.0, 13.0, 11.0, 8.0, 5.0, 0.0]
                    # tax_list = [tax.amount for tax in line.tax_ids]
                    # tax_match = [i for i, j in zip(tax_list, tax_amount_list) if i == j]
                    # if True:
                    for t in line.tax_ids:
                        if t.amount in tax_amount_list:
                            line.tax_amount_type = t.amount_type
                            line.tax_amount = t.amount
                        else:
                            line.tax_amount_type = "except"
                            line.tax_amount = 0.0
                else:
                    line.tax_amount_type = "except"
                    line.tax_amount = 0.0
            except Exception as e:
                print(e)
