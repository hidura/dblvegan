# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'POS-CONNServer',
    'version': '1.0',
    'sequence': 265,
    'category':"Sales",
    'author':'Oikos Chain Team',
    'depends': ['pos_sale', 'purchase', 'sale', 'stock'],
    'summary': "A connection between the Odoo in the PC and the Odoo in the cloud, that allow to make syncronizations"
               "for the server side",
    'description': """
This implementation will allow the Odoo in premise of the client, to be connected with the Odoo in the
cloud and be updated in real time.

    """,
    'category': 'Sales',

    'data': [
        'security/ir.model.access.csv'
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
