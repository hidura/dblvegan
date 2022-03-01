# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Employees',
    'version': '1.0',
    'sequence': 275,
    'category':"Employee",
    'author':'Oikos Chain Team',
    'depends': ['hr_payroll'],
    'summary': "A connection between the Odoo in the PC and the Odoo in the cloud, that allow to make syncronizations",
    'description': """
This implementation will allow the Odoo in premise of the client, to be connected with the Odoo in the
cloud and be updated in real time.

    """,
    'category': 'Employee',

    'data': [
        'views/hr_loan.xml',
        'views/hr_news.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
