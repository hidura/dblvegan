# -*- coding: utf-8 -*-
{
    'name': "Fiscal Henca",

    'summary': """
      
       Controlador para impresoras fiscales.
        
        Este modulo permite que odoo pueda imprimir desde el facturacion o el Pos

        en la impresora fiscal EPSON TM-T88v y Bixolon utilizando una interfaz fiscal

        """,

    'description': """
         Controlador para impresoras fiscales.
    """,
    'author': "Grupo Consultoria Henca, Jorge Miguel Hernandez Santos(dev.jhernandez@gmail.com)",
    'category': 'Fiscal',
      'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'account', 'l10n_do_accounting','l10n_do_pos','pos_restaurant'],

    # always loaded
     'data': [
        'security/ir.model.access.csv',
        # 'views/templates.xml',
        'views/ipf_view.xml',
        'views/account_invoice_view.xml',
        'views/pos_payment_method_views.xml',
        'views/pos_config_view.xml',
        'views/pos_session.xml'

    ],
    'assets': {
        'web.assets_backend': [
            'henca_fiscal/static/src/libs/*.css',
            'henca_fiscal/static/src/libs/*.js',
            'henca_fiscal/static/src/js/invoicing.js'
        ],
        'point_of_sale.assets': [
            'henca_fiscal/static/src/libs/*.css',

            'henca_fiscal/static/src/libs/*.js',
            # 'henca_fiscal/static/src/js/ChromeWidgets/ProxyStatus.js',
            'henca_fiscal/static/src/js/ChromeWidgets/SyncNotification.js',
            'henca_fiscal/static/src/js/Screens/PaymentScreen/PaymentScreen.js',
            'henca_fiscal/static/src/js/Screens/ReceiptScreen/ReceiptScreen.js',
            'henca_fiscal/static/src/xml/**/*',
        ],
    },
}
