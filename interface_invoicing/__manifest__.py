# -*- coding: utf-8 -*-
{
    'name': "Interfaz Facturacion",

    'summary': """
       Permite la impresion de los documentos, por la impresora fiscal""",

    'description': """
         Impresion fiscal por  facturacion.
    """,

    'author': "Neotec Group",
    'website': "http://www.neotec.do/",

    'category': 'Neotec/Pos',
    'version': '16.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'account',
                'l10n_do_accounting',
                'protocol_message',
                'config_interface'],

    # always loaded
    'data': [
        'security/inteface_invoicing_security.xml',
        'views/account_move_views.xml',
        'views/res_users_views.xml',
        'views/config_interface_views.xml'
    ],

    'assets': {
        'web.assets_backend': [
            '/interface_invoicing/static/src/js/standard_format.js',
            '/interface_invoicing/static/src/js/invoice.js',
        ],
    },
    "license": "LGPL-3"
}