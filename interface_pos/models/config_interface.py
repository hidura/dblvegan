# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ConfingInterface(models.Model):

    # _name = 'config_interface.config'
    _inherit = ['config.interface']

    printer_type = fields.Selection(
        string=u'Tipo de impresora',
        selection=[('bixolon', 'Bixolon/HKA'),
                   ('custom', 'Custom'),
                   ('epson', 'Epson'),
                   ('star', 'Star/Citizen')],
        default="bixolon"
    )

    mode_restaurant = fields.Boolean(
        string=u'Modo restaurante',
        default=True,
        help=u"Activado: Impresora Modo FastFood, \
        Desactivado:  Impresora Modo Retail"
    )

    use_legal_tip = fields.Boolean(
        string=u'Propina legal',
        help=u"Para que todas los documentos apliquen el 10% de propinal legal"
    )

    print_cashier = fields.Boolean(
        string=u'Imprimir cajero',
        help=u"Para que  en la factura fiscal se imprima el cajero"
    )

    print_seller = fields.Boolean(
        string=u'Imprimir vendedor',
        help=u"Para que  en la factura fiscal se imprima el vendedor"
    )

    print_user = fields.Boolean(
        string=u'Imprimir usuario',
        help=u"Para que  en la factura fiscal se imprima el usuario"
    )

    print_receipt_footer = fields.Boolean(
        string=u'Imprimir pie de pagina del ticket',
        help=u"Para que  se imprima la cabezera que se configuro \
        en el Punto de Venta"
    )


class InterfacePosConfig(models.Model):

    _name = 'pos.config'
    _inherit = 'pos.config'

    config_interface_id = fields.Many2one(
        "config.interface", u"Parámetro")


class AccountFiscalPosition(models.Model):

    _inherit = 'account.fiscal.position'

    use_for_delivery = fields.Boolean(
        string=u'Usar para LLevar/Delivery',
        help=u"Activar si desea que esta posicion fiscal,hace que no se \
        aplique el 10% de la propinal legal."
    )

class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    payment_form = fields.Selection(
        [("cash", "Efectivo"),
         ("bank", u"Cheque / Transferencia / Depósito"),
         ("card", u"Tarjeta Crédito / Débito"),
         ("credit", u"A Crédito"),
         ("swap", "Permuta"),
         ("bond", "Bonos o Certificados de Regalo"),
         ("others", "Otras Formas de Venta")],
        string="Forma de Pago")



class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_pos_payment_method(self):
        result = super()._loader_params_pos_payment_method()
        result['search_params']['fields'].append('payment_form')
        return result