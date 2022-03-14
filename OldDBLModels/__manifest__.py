# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'OldDBLVeganSer',
    'version': '1.0',
    'sequence': 265,
    'category':"Sales",
    'author':'Oikos Chain Team',
    'depends': ['pos_sale', 'purchase', 'sale', 'stock'],
    'summary': "The old fields that the system needs to be working.",
    'description': """
    """,
    'category': 'Administration',

    'data': [
        'views/ir_config_empl.xml',
        'views/views_elec_empl.xml',
        'views/res_bank_empl.xml',
        'views/hr_employee_.xml'
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
