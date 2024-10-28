# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    l10n_latam_document_number = fields.Char(
        related="account_move.l10n_latam_document_number",
        store=True,
        string="Comprobante fiscal",
    )
    l10n_latam_document_type_id = fields.Many2one(
        related="account_move.l10n_latam_document_type_id",
        readonly=True,
        store=True,
    )
    l10n_do_fiscal_number = fields.Char("NCF")
    l10n_do_ncf_expiration_date = fields.Date(
        related="account_move.l10n_do_ncf_expiration_date"
    )
    # l10n_latam_use_documents = fields.Boolean()
    l10n_latam_country_code = fields.Char(
        related="company_id.country_id.code",
        index=True,
        store=True,
        help="Technical field used to hide/show fields regarding the localization",
    )
    l10n_do_ecf_modification_code = fields.Char(string="Modification Code")
    l10n_do_origin_ncf = fields.Char(related="account_move.l10n_do_origin_ncf", string="NCF origen")
    l10n_do_return_order_id = fields.Many2one(
        "pos.order",
        string="Pedido origen",
        readonly=True,
        copy=False,
    )
    l10n_do_is_return_order = fields.Boolean(
        string="Es una devolución",
        copy=False,
    )

    @api.model
    def get_from_ui(self, order):
        pos_order = self.sudo().search([('pos_reference', '=', order)])
        move_id = pos_order.account_move
        return {
            'l10n_do_fiscal_number': move_id.l10n_do_fiscal_number or pos_order.l10n_latam_document_number,
            'l10n_do_ncf_expiration_date': move_id.l10n_do_ncf_expiration_date or pos_order.l10n_do_ncf_expiration_date,
            'return_order_id': pos_order.id,
            'l10n_do_origin_ncf': pos_order.l10n_do_origin_ncf,
        }

    @api.model
    def create_from_ui(self, orders, draft=False):
        res = super(PosOrder, self).create_from_ui(orders, draft)
        for record in res:
            order_id = self.browse(record.get('id'))
            if order_id:
                record['l10n_do_fiscal_number'] = order_id.l10n_latam_document_number
                record['l10n_do_ncf_expiration_date'] = order_id.l10n_do_ncf_expiration_date
                record['l10n_latam_document_type_id'] = order_id.l10n_latam_document_type_id.name
                order_id.write(record)
        return res

    @api.model
    def _order_fields(self, ui_order):
        res = super()._order_fields(ui_order)

        if ui_order["to_invoice"]:
            res.update({
                'l10n_do_fiscal_number': ui_order.get('l10n_do_fiscal_number', False),
                'l10n_latam_document_number': ui_order.get('l10n_do_fiscal_number', False),
                'l10n_do_ecf_modification_code': ui_order.get('l10n_do_ecf_modification_code', False),
                "l10n_do_origin_ncf": ui_order.get('l10n_do_origin_ncf', False),
                "l10n_do_is_return_order": ui_order.get('l10n_do_is_return_order', False),
                "l10n_do_return_order_id": ui_order.get('l10n_do_return_order_id', False),
            })

        for line in ui_order["lines"]:
            line_dic = line[2]
            refunded_orderline_id = line_dic.get("refunded_orderline_id", False)
            if refunded_orderline_id:
                original_line = self.env["pos.order.line"].browse(refunded_orderline_id)
                original_order_id = original_line.order_id
                res.update({
                    "l10n_do_origin_ncf": original_order_id.l10n_latam_document_number,
                    "l10n_do_is_return_order": True,
                    "l10n_do_return_order_id": original_order_id.id,
                })
                original_line.l10n_do_line_qty_returned += abs(line_dic.get("qty", 0))
        return res

    # @api.model
    # def _payment_fields(self, order, ui_paymentline):
    #     fields = super()._payment_fields(order, ui_paymentline)
    #     fields.update({
    #         'credit_note_id': ui_paymentline.get('credit_note_id', False),
    #         'note': ui_paymentline.get('note', False),
    #     })
    #     return fields

    @api.model
    def _process_order(self, order, draft, existing_order):
        if not order['data']["partner_id"]:
            pos_config = self.env["pos.session"].search([
                ("id", "=", order['data']["pos_session_id"])
            ]).config_id
            if not pos_config.default_partner_id:
                raise UserError(
                    _("This point of sale does not have a default customer.")
                )
            order['data']["partner_id"] = pos_config.default_partner_id.id

            if self.company_id.l10n_do_ecf_issuer:
                order['data']['l10n_latam_document_type_id'] = self.env['l10n_latam.document.type'].search([
                    ('doc_code_prefix', '=', 'E32')]).id
            else:
                order['data']['l10n_latam_document_type_id'] = self.env['l10n_latam.document.type'].search([
                    ('doc_code_prefix', '=', 'B02')]).id
        if not draft:
            order["data"]["to_invoice"] = True
            order["to_invoice"] = True

        for payments in order['data']['statement_ids']:
            payment = payments[2]
           # TODO change credit_note_id for use_credit_note field from payment method
            if payment.get('credit_note_id', False):
                payment_method_id = self.env['pos.payment.method'].search([('use_credit_note', '=', True)])
                payment.update({
                    'payment_method_id': payment_method_id.id,
                })

        res = super(PosOrder, self)._process_order(order, draft, existing_order)
        for line in self.env['pos.order.line'].search([('order_id', '=', res)]):
            if line.refunded_orderline_id.order_id:
                original_account_move = self.env['account.move'].search([
                    ('id', '=', line.refunded_orderline_id.order_id.account_move.id)
                ])
                original_order = {
                    'l10n_do_return_order_id': line.refunded_orderline_id.order_id.id,
                    'l10n_do_origin_ncf': original_account_move.l10n_do_fiscal_number,
                    'l10n_do_is_return_order': True,
                }
                current_order = self.env['pos.order'].search([('id', '=', res)])
                current_order.update(original_order)
                account_move = self.env['account.move'].search([('id', '=', current_order.account_move.id)])
                account_move.update({'l10n_do_origin_ncf': original_account_move.l10n_do_fiscal_number})
        return res

    def _export_for_ui(self, order):
        result = super(PosOrder, self)._export_for_ui(order)
        values = {
            'l10n_latam_document_type_id': order.l10n_latam_document_type_id.id,
            'l10n_do_origin_ncf': order.l10n_do_origin_ncf,
            'l10n_do_fiscal_number': order.l10n_latam_document_number,
            'l10n_do_ncf_expiration_date': order.l10n_do_ncf_expiration_date,
            'l10n_do_ecf_modification_code': order.l10n_do_ecf_modification_code,
        }

        self.write(values)
        values['l10n_latam_document_type_id'] = order.l10n_latam_document_type_id.name
        result.update(values)
        return result

    @api.model
    def credit_note_info_from_ui(self, l10n_do_fiscal_number, partner_id=None, amount_total=None):
        refund_document_type_id = self.env.ref('l10n_do_accounting.ncf_credit_note_client').id

        domain = [
            ("l10n_do_fiscal_number", "=", l10n_do_fiscal_number),
            ("l10n_latam_document_type_id", "=", refund_document_type_id),
        ]
        if partner_id:
            domain.append(('partner_id', '=', partner_id))

        out_refund_invoice = self.env["pos.order"].search(domain)
        if not out_refund_invoice:
            out_refund_invoice = self.env["account.move"].search(domain)
        else:
            out_refund_invoice = out_refund_invoice.account_move

        if out_refund_invoice:
            msg_error = ""
            if partner_id and out_refund_invoice.partner_id.id != partner_id:
                msg_error = "La Nota de Crédito pertenece a otro cliente"
            elif not out_refund_invoice.amount_residual:
                msg_error = "El balance de la Nota de Crédito es 0."

            residual = out_refund_invoice.amount_residual
            if amount_total and amount_total < out_refund_invoice.amount_residual:
                residual = amount_total

            return {
                "model": out_refund_invoice._name,
                "id": out_refund_invoice.id,
                "residual": residual,
                "partner_id": out_refund_invoice.partner_id.id,
                "msg": msg_error
            }
        return {'msg': "La Nota de Crédito no existe."}


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    l10n_do_line_qty_returned = fields.Float(
        string="Return line Qty",
        default=0.0,
    )
    l10n_do_original_line_id = fields.Many2one(
        comodel_name="pos.order.line",
        string="Original line",
    )

    @api.model
    def _order_line_fields(self, line, session_id=None):
        fields_return = super(PosOrderLine, self)._order_line_fields(line, session_id)
        fields_return[2].update({
            "l10n_do_line_qty_returned": line[2].get("l10n_do_line_qty_returned", 0),
            "l10n_do_original_line_id": line[2].get("l10n_do_original_line_id", False),
        })
        return fields_return
