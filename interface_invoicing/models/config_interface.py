# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ConfigInterface(models.Model):
    _inherit = ['config.interface']

    invoice_printer_type = fields.Selection(
        string=u'Tipo de impresora facturacion',
        selection=[('bixolon', 'Bixolon/HKA'),
                   ('custom', 'Custom'),
                   ('epson', 'Epson'),
                   ('star', 'Star/Citizen')],
        default='bixolon')

    invoice_use_legal_tip = fields.Boolean(
        string=u'Propina legal facturacion',
        help=u"Para que todas los documentos apliquen el 10% de propinal legal"
    )

    invoice_mode_restaurant = fields.Boolean(
        string=u'Modo restaurante facturacion ?',
        default=True,
        help=u"Activado: Impresora Modo FastFood, Desactivado:  \
        Impresora Modo Retail"
    )

    # invoice_automatic_print_after_validation = fields.Boolean(
    #     string=u'Imprimir despues de validar',
    #     default=False,
    #     help=u"Imprimir la factura fiscal despues que se valido la factura"
    # )

    invoice_automatic_payment_after_validation = fields.Boolean(
        string=u'Pagar despues de validar',
        default=False,
    )

    invoice_print_seller = fields.Boolean(
        string=u'Imprimir Vendedor',
        help='Activar si desea que en la factura se imprima el vendedor',
        default=True,
    )

    invoice_print_cashier = fields.Boolean(
        string=u'Imprimir Cajero',
        help='Activar si desea que en la factura se imprima el cajero')

    invoice_note_invoice = fields.Text(
        string=u'Nota para cada factura',
        help='Esta nota sera impresa en el pie de pagina de cada factura')

    invoice_print_product_barcode = fields.Boolean(
        string=u'Imprimir el codigo de barra  del producto',
        help=u"Imprime el codigo de barra del producto en su descripcion"
    )

    invoice_print_product_reference = fields.Boolean(
        string=u'Imprimir la referencia  del producto',
        help=u"Imprime la referencia del producto en su descripcion"
    )
