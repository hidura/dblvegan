# -*- coding: utf-8 -*-
import logging
import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    fiscal_printed = fields.Boolean(
        string=u"Impresa por fiscal",
        help="Indica si una factura se ha imprimido por la impresora fiscal",
        copy=False)


    def action_invoice_sent(self):
        for rec in self:
            rec.write({'fiscal_printed': True})


    def get_account_invoice_interface_config(self):
        config = self.env.user.config_interface_id or False
        if config is False:
            return False
        res = {
            'use_legal_tip': config.invoice_use_legal_tip,
            'printer_type': config.invoice_printer_type,
            'mode_restaurant': config.invoice_mode_restaurant,
            'automatic_payment_after_validation':
                config.invoice_automatic_payment_after_validation,
            'print_seller': config.invoice_print_seller,
            'print_cashier': config.invoice_print_cashier,
            'note_invoice': config.invoice_note_invoice,
            'print_product_barcode':
                config.invoice_print_product_barcode,
            'invoice_print_product_reference':
                config.invoice_print_product_reference
        }

        return res


    def get_ncf_type(self, ncf):
        n_type = "nofiscal"
        ncf = ncf[9:11] if len(ncf)==19 else ncf[1:3]
        if ncf == "02":
            n_type = "final"
        elif ncf in ["01", "15"]:
            n_type = "fiscal"
        elif ncf == "14":
            n_type = "special"

        return n_type


    def get_payment_data(self, data):
        payments_info = []
        payments = data
        if payments:
            for con in payments['content']:
                pay ={
                    'type':con['interfaz_payment_form'],
                    'description':con['interfaz_payment_description'],
                    'amount':con['amount'],
                }
                payments_info.append(pay)
        return payments_info

    def get_invoice_format(self):

        ncf_type = self.get_ncf_type(
            self.l10n_latam_document_number if self.move_type == "out_invoice" else self.l10n_do_origin_ncf )

        invoice_dict = {
            'do_print': False,
            'printed': self.fiscal_printed,
            'type': ncf_type,
            'ncf': self.l10n_latam_document_number,
            'cashier': self.env.user.name,
            'seller': self.user_id.name,
            'client': self.partner_id.name,
            'rnc': self.partner_id.vat
        }

     

        if self.move_type == "out_invoice":
            if not invoice_dict['type']:
                invoice_dict.update({'type': 'final'})
        elif self.move_type == "out_refund":

            invoice_dict.update({'ref_ncf': self.l10n_do_origin_ncf})
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
            tax_amout = line.tax_ids[0].amount if bool(line.tax_ids) else 0

            invoice_items_dict["description"] = description
            invoice_items_dict["quantity"] = line.quantity
            invoice_items_dict["itbis"] = int(tax_amout)
            invoice_items_dict["price"] = line.price_unit
            invoice_items_dict["discount"] = line.discount
            invoice_items_dict["default_code"] = line.product_id.default_code
            invoice_items_dict["barcode"] = line.product_id.barcode

            if line.discount > 0:
                total_discount += line.price_unit * (line.discount / 100.0)
            invoice_items_list.append(invoice_items_dict)

        invoice_dict["items"] = invoice_items_list
        invoice_dict["total_discount"] = total_discount

        payment_ids_list = []

        payment_ids_list = self.get_payment_data(self.invoice_payments_widget) if self.invoice_payments_widget else []
        if len(payment_ids_list) == 0:
            payment_ids_list.append(
                dict(type="others", amount=self.amount_total))

        amount_payment = 0.0
        for payment in payment_ids_list:
            amount_payment += payment["amount"]

        if amount_payment < self.amount_total:
            payment_ids_list.append(
                dict(type="others", amount=self.amount_total - amount_payment))

        invoice_dict.update(
            dict(payments=payment_ids_list, invoice_id=self.id))

        invoice_dict['do_print'] = True

        return invoice_dict

    def action_do_nothig(self):
        pass

    
    @api.depends('move_type', 'line_ids.amount_residual')
    def _compute_payments_widget_reconciled_info(self):
        payment_vals = super(AccountMove, self)._compute_payments_widget_reconciled_info()
        payment_vals = []
        for move in self:
            if move.invoice_payments_widget and move.move_type in ['out_invoice', 'out_refund']:
                for payment in move.invoice_payments_widget['content']:
                    if payment['account_payment_id']:
                        payment_id = self.env['account.payment'].browse(payment['account_payment_id'])
                        payment_form = payment_id.journal_id.l10n_do_payment_form
                        journal_name = payment_id.journal_id.name
                        payment['interfaz_payment_form'] = payment_form or False
                        payment['interfaz_payment_description'] = journal_name
                    elif payment['move_id']:
                        move_id = self.env['account.move'].browse(payment['move_id'])
                        ref = move_id.l10n_latam_document_number
                        payment_form = 'credit_note' if 'B04' in ref else 'other'
                        payment['interfaz_payment_form'] = payment_form or False
                        payment['interfaz_payment_description'] = ref
        return payment_vals