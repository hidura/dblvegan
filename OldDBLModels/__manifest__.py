# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'OldDBLVeganSer',
    'version': '13.0.3',
    'sequence': 265,
    'category':"Sales",
    'author':'Oikos Chain Team',
    'depends': ['pos_sale', 'purchase', 'sale', 'stock', 'hr_payroll', 'l10n_do_accounting', 'l10n_latam_invoice_document'],
    'summary': "The old fields that the system needs to be working.",
    'description': """
    """,
    'category': 'Administration',

    'data': [
        'security/ir.model.access.csv',
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
