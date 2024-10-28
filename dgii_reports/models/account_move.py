# Part of Domincana Premium.
# See LICENSE file for full copyright and licensing details.

import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InvoiceServiceTypeDetail(models.Model):
    _name = 'invoice.service.type.detail'
    _description = "Invoice Service Type Detail"

    name = fields.Char()
    code = fields.Char(size=2)
    parent_code = fields.Char()

    _sql_constraints = [
        ('code_unique', 'unique(code)', _('Code must be unique')),
    ]


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    l10n_latam_tax_ids = fields.One2many(comodel_name='account.move.line', compute="_compute_l10n_latam_amount_and_taxes")

    def _compute_l10n_latam_amount_and_taxes(self):
        recs_invoice = self.filtered(lambda x: x.is_invoice())
        for invoice in recs_invoice:
            invoice.l10n_latam_tax_ids = invoice.line_ids.filtered('tax_line_id')
        remaining = self - recs_invoice
        remaining.l10n_latam_tax_ids = [(5, 0)]

    def _get_invoice_payment_widget(self):
        return self.invoice_payments_widget.get('content', []) if self.invoice_payments_widget else []

    def _compute_invoice_payment_date(self):
        for inv in self:
            if inv.state == 'posted' and inv.payment_state == 'paid':
                if inv.move_type in ['out_refund', 'in_refund']:
                    inv.payment_date = inv.invoice_date
                else:
                    dates = [
                        payment['date'] for payment in inv._get_invoice_payment_widget()
                    ]
                    if dates:
                        max_date = max(dates)
                        date_invoice = inv.invoice_date
                        inv.payment_date = max_date if max_date >= date_invoice \
                            else date_invoice

    @api.constrains('invoice_line_ids')
    def _check_same_purchase_tax_type(self):
        """Restrict one tax per type per invoice"""
        message_strings = dict(self.env['account.tax']._fields['purchase_tax_type'].selection)
        purchase_tax_types = ['isr', 'ritbis']
        for inv in self:
            for inv_taxed_line in inv.invoice_line_ids.filtered('tax_ids'):
                for ptt in purchase_tax_types:
                    same_type_taxes = inv_taxed_line.tax_ids.filtered(lambda tax: tax.purchase_tax_type == ptt)
                    if len(same_type_taxes) > 1:
                        raise ValidationError(_('An invoice cannot have multiple withholding taxes of type {}.'.format(
                            message_strings.get(same_type_taxes[0].purchase_tax_type)
                        )))

    def _convert_to_local_currency(self, amount):
        # This function is not being used anymore
        sign = -1 if self.move_type in ['in_refund', 'out_refund'] else 1
        rate = abs(self.amount_total_signed / (self.amount_total or 1))
        amount = amount * rate
        return amount * sign

    def _get_tax_line_ids(self):
        # return self.l10n_latam_tax_ids
        return self.line_ids.filtered('tax_line_id')

    @api.model
    @api.depends('l10n_latam_tax_ids', 'line_ids.tax_ids', 'state', 'payment_state')
    def _compute_taxes_fields(self):
        """Compute invoice common taxes fields"""
        for inv in self:

            tax_line_ids = inv._get_tax_line_ids()

            if inv.state != 'draft':
                # Monto Impuesto Selectivo al Consumo
                inv.selective_tax = abs(
                    sum(
                        tax_line_ids.filtered(
                            lambda tax: tax.tax_line_id.tax_group_id.name == 'ISC').mapped('balance')
                    )
                )

                # Monto Otros Impuestos/Tasas
                inv.other_taxes = abs(
                    sum(
                        tax_line_ids.filtered(
                            lambda tax: tax.tax_line_id.tax_group_id.name == 'Otros Impuestos').mapped('balance')
                    )
                )

                # Monto Propina Legal
                inv.legal_tip = abs(
                    sum(
                        tax_line_ids.filtered(
                            lambda tax: tax.tax_line_id.tax_group_id.name == 'Propina').mapped('balance')
                    )
                )

                # ITBIS sujeto a proporcionalidad
                inv.proportionality_tax = abs(
                    sum(
                        tax_line_ids.filtered(
                            lambda tax: tax.account_id.account_fiscal_type in ['A29', 'A30']).mapped('balance')
                    )
                )

                # ITBIS llevado al Costo
                inv.cost_itbis = abs(
                    sum(
                        tax_line_ids.filtered(
                            lambda tax: tax.account_id.account_fiscal_type == 'A51').mapped('balance')
                    )
                )

                # if inv.move_type == 'out_invoice' and any([
                #     inv.third_withheld_itbis,
                #     inv.third_income_withholding
                #         ]):
                #     # Fecha Pago
                #     inv._compute_invoice_payment_date()
                #
                # if inv.move_type == 'in_invoice' and any([
                #     inv.withholded_itbis,
                #     inv.income_withholding
                #         ]):
                #     # Fecha Pago
                #     inv._compute_invoice_payment_date()
                inv._compute_invoice_payment_date()

    @api.model
    @api.depends('invoice_line_ids', 'invoice_line_ids.product_id', 'state')
    def _compute_amount_fields(self):
        """Compute Purchase amount by product type"""
        for inv in self:
            if inv.move_type in ['in_invoice', 'in_refund'] and inv.state != 'draft':
                service_amount = 0
                good_amount = 0

                for line in inv.invoice_line_ids:

                    # Monto calculado en bienes
                    if line.product_id.type in ["product", "consu"]:
                        good_amount += abs(line.balance)

                    # Si la linea no tiene un producto
                    elif not line.product_id:
                        service_amount += abs(line.balance)
                        continue

                    # Monto calculado en servicio
                    else:
                        service_amount += abs(line.balance)

                inv.service_total_amount = service_amount
                inv.good_total_amount = good_amount

    @api.model
    @api.depends('l10n_latam_tax_ids', 'state', 'move_type', 'payment_state')
    def _compute_isr_withholding_type(self):
        """Compute ISR Withholding Type
        Keyword / Values:
        01 -- Alquileres
        02 -- Honorarios por Servicios
        03 -- Otras Rentas
        04 -- Rentas Presuntas
        05 -- Intereses Pagados a Personas Jurídicas
        06 -- Intereses Pagados a Personas Físicas
        07 -- Retención por Proveedores del Estado
        08 -- Juegos Telefónicos
        """
        for inv in self.filtered(
                lambda i: i.move_type == "in_invoice" and i.state == "posted" or i.payment_state in ["paid", "in_payment"] and i.move_type == "in_invoice"):

            tax_l_id = inv.l10n_latam_tax_ids.filtered(
                lambda t: t.tax_line_id.purchase_tax_type == "isr")
            if tax_l_id:  # invoice tax lines use case
                inv.isr_withholding_type = tax_l_id[0].tax_line_id.isr_retention_type
            else:  # in payment/journal entry use case
                aml_ids = self.env["account.move"].browse(
                    p["move_id"] for p in inv._get_invoice_payment_widget()
                ).mapped("line_ids").filtered(
                    lambda aml: aml.account_id.isr_retention_type)
                if aml_ids:
                    inv.isr_withholding_type = aml_ids[0].account_id.isr_retention_type

    def _get_payment_string(self):
        """Compute Vendor Bills payment method string

        Keyword / Values:
        cash        -- 01 Efectivo
        bank        -- 02 Cheques / Transferencias / Depósitos
        card        -- 03 Tarjeta Crédito / Débito
        credit      -- 04 Compra a Crédito
        swap        -- 05 Permuta
        credit_note -- 06 Notas de Crédito
        mixed       -- 07 Mixto
        """
        payments = []
        p_string = ""

        for payment in self._get_invoice_payment_widget():
            payment_id = self.env['account.payment'].browse(
                payment.get('account_payment_id'))
            move_id = False
            if payment_id:
                if payment_id.journal_id.type in ['cash', 'bank']:
                    p_string = payment_id.journal_id.l10n_do_payment_form

            if not payment_id:
                move_id = self.env['account.move'].browse(
                    payment.get('move_id'))
                if move_id:
                    p_string = 'bank'

            # If invoice is paid, but the payment doesn't come from
            # a journal, assume it is a credit note
            payment = p_string if payment_id or move_id else 'credit_note'
            payments.append(payment)

        methods = {p for p in payments}
        if len(methods) == 1:
            return list(methods)[0]
        elif len(methods) > 1:
            return 'mixed'

    @api.model
    @api.depends('state', 'payment_state')
    def _compute_in_invoice_payment_form(self):
        for inv in self:
            if inv.state == 'posted' and inv.payment_state == 'paid':
                payment_dict = {'cash': '01', 'bank': '02', 'card': '03',
                                'credit': '04', 'swap': '05',
                                'credit_note': '06', 'mixed': '07'}
                inv.payment_form = payment_dict.get(inv._get_payment_string())
            else:
                inv.payment_form = '04'

    @api.model
    @api.depends('line_ids', 'line_ids.balance', 'state')
    def _compute_invoiced_itbis(self):
        """Compute invoice invoiced_itbis taking into account the currency"""
        for inv in self:
            amount = 0
            if inv.state != 'draft':
                itbis_taxes = ['ITBIS', 'ITBIS 18%']
                for tax in inv._get_tax_line_ids():
                    if tax.tax_line_id.tax_group_id.name in itbis_taxes and tax.tax_line_id.purchase_tax_type != 'ritbis':
                        amount += abs(tax.balance)
            inv.invoiced_itbis = amount

    @api.depends('state', 'move_type', 'payment_state', 'payment_id')
    def _compute_withheld_taxes(self):
        for inv in self:
            if inv.state == 'posted':
                inv.third_withheld_itbis = 0
                inv.third_income_withholding = 0
                withholding_amounts_dict = {"A34": 0, "A36": 0, "ISR": 0, "A38": 0}

                if inv.move_type == 'in_invoice':
                    tax_line_ids = inv._get_tax_line_ids()

                    # Monto ITBIS Retenido por impuesto
                    inv.withholded_itbis = abs(sum(tax_line_ids.filtered(
                        lambda tax: tax.tax_line_id.purchase_tax_type == 'ritbis'
                        ).mapped('balance')))

                    # Monto Retención Renta por impuesto
                    withheld_isr = abs(sum(tax_line_ids.filtered(
                        lambda tax: tax.tax_line_id.purchase_tax_type == 'isr'
                        ).mapped('balance')))
                    inv.income_withholding = withheld_isr

                move_ids = [p["move_id"] for p in inv._get_invoice_payment_widget()]
                aml_ids = self.env["account.move"].browse(move_ids).mapped(
                    "line_ids").filtered(lambda aml: aml.account_id.account_fiscal_type and aml.move_id.move_type not in ['in_refund', 'out_refund'])
                if aml_ids:
                    for aml in aml_ids:
                        fiscal_type = aml.account_id.account_fiscal_type
                        if fiscal_type in withholding_amounts_dict:
                            withholding_amounts_dict[fiscal_type] += abs(aml.balance)

                    withheld_itbis = sum(v for k, v in withholding_amounts_dict.items()
                                         if k in ("A34", "A36"))
                    withheld_isr = sum(v for k, v in withholding_amounts_dict.items()
                                       if k in ("ISR", "A38"))

                    if inv.move_type == 'out_invoice':
                        inv.third_withheld_itbis += withheld_itbis
                        inv.third_income_withholding += withheld_isr

                    elif inv.move_type == 'in_invoice':
                        inv.withholded_itbis += withheld_itbis
                        inv.income_withholding += withheld_isr


    @api.model
    @api.depends('invoiced_itbis', 'cost_itbis', 'state')
    def _compute_advance_itbis(self):
        for inv in self:
            if inv.state != 'draft':
                inv.advance_itbis = inv.invoiced_itbis - inv.cost_itbis

    @api.model
    @api.depends('l10n_latam_document_type_id')
    def _compute_is_exterior(self):
        for inv in self:
            inv.is_exterior = True if inv.l10n_latam_document_type_id.l10n_do_ncf_type == \
                'exterior' else False

    @api.onchange('service_type')
    def onchange_service_type(self):
        self.service_type_detail = False
        return {
            'domain': {
                'service_type_detail': [
                    ('parent_code', '=', self.service_type)
                    ]
            }
        }

    @api.onchange('journal_id')
    def ext_onchange_journal_id(self):
        self.service_type = False
        self.service_type_detail = False

    # ISR Percibido       --> Este campo se va con 12 espacios en 0 para el 606
    # ITBIS Percibido     --> Este campo se va con 12 espacios en 0 para el 606
    payment_date = fields.Date(compute='_compute_taxes_fields', store=True)
    service_total_amount = fields.Monetary(
        compute='_compute_amount_fields',
        store=True,
        currency_field='company_currency_id')
    good_total_amount = fields.Monetary(compute='_compute_amount_fields',
                                        store=True,
                                        currency_field='company_currency_id')
    invoiced_itbis = fields.Monetary(compute='_compute_invoiced_itbis',
                                     store=True,
                                     currency_field='company_currency_id')
    withholded_itbis = fields.Monetary(compute='_compute_withheld_taxes',
                                       store=True,
                                       currency_field='company_currency_id')
    proportionality_tax = fields.Monetary(compute='_compute_taxes_fields',
                                          store=True,
                                          currency_field='company_currency_id')
    cost_itbis = fields.Monetary(compute='_compute_taxes_fields',
                                 store=True,
                                 currency_field='company_currency_id')
    advance_itbis = fields.Monetary(compute='_compute_advance_itbis',
                                    store=True,
                                    currency_field='company_currency_id')
    isr_withholding_type = fields.Char(compute='_compute_isr_withholding_type',
                                       store=True,
                                       size=2)
    income_withholding = fields.Monetary(compute='_compute_withheld_taxes',
                                         store=True,
                                         currency_field='company_currency_id')
    selective_tax = fields.Monetary(compute='_compute_taxes_fields',
                                    store=True,
                                    currency_field='company_currency_id')
    other_taxes = fields.Monetary(compute='_compute_taxes_fields',
                                  store=True,
                                  currency_field='company_currency_id')
    legal_tip = fields.Monetary(compute='_compute_taxes_fields',
                                store=True,
                                currency_field='company_currency_id')
    payment_form = fields.Selection([('01', 'Cash'),
                                     ('02', 'Check / Transfer / Deposit'),
                                     ('03', 'Credit Card / Debit Card'),
                                     ('04', 'Credit'), ('05', 'Swap'),
                                     ('06', 'Credit Note'), ('07', 'Mixed')],
                                    compute='_compute_in_invoice_payment_form',
                                    store=True)
    third_withheld_itbis = fields.Monetary(
        compute='_compute_withheld_taxes',
        store=True,
        currency_field='company_currency_id')
    third_income_withholding = fields.Monetary(
        compute='_compute_withheld_taxes',
        store=True,
        currency_field='company_currency_id')
    is_exterior = fields.Boolean(compute='_compute_is_exterior', store=True)
    service_type = fields.Selection([
        ('01', 'Gastos de Personal'),
        ('02', 'Gastos por Trabajos, Suministros y Servicios'),
        ('03', 'Arrendamientos'), ('04', 'Gastos de Activos Fijos'),
        ('05', 'Gastos de Representación'), ('06', 'Gastos Financieros'),
        ('07', 'Gastos de Seguros'),
        ('08', 'Gastos por Regalías y otros Intangibles')
    ])
    service_type_detail = fields.Many2one('invoice.service.type.detail')
    fiscal_status = fields.Selection(
        [('normal', 'Partial'), ('done', 'Reported'), ('blocked', 'Not Sent')],
        copy=False,
        help="* The \'Grey\' status means invoice isn't fully reported and may appear "
             "in other report if a withholding is applied.\n"
        "* The \'Green\' status means invoice is fully reported.\n"
        "* The \'Red\' status means invoice is included in a non sent DGII report.\n"
        "* The blank status means that the invoice have"
        "not been included in a report."
    )
