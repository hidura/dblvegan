# -*- coding: utf-8 -*-
{
    'name': "Interfaz Pos",

    'summary': """
    Permite la impresion de los documentos, por la impresora fiscal""",

    'description': """
       Impresion fiscal por el punto de venta
    """,

    'author': "Neotec Group",
    'website': "http://www.neotec.do/",

    'category': 'Neotec/Pos',
    'version': '16.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'point_of_sale',
        'l10n_do_pos',
        'config_interface',
        'protocol_message'],
    'qweb': ['static/src/xml/pos.xml'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/account_fiscal_position_view.xml',
        'views/config_interface_views.xml'
    ],
     'assets': {
          'point_of_sale.assets': [
            'interface_pos/static/src/js/models.js',
            'interface_pos/static/src/js/standard_format.js',
            'interface_pos/static/src/js/screens.js',
            'interface_pos/static/src/js/Button.js',
            'interface_pos/static/src/xml/pos.xml'
          ]

    },
    "license": "LGPL-3"

}