# -*- coding: utf-8 -*-
{
    'name': "Fiscal Accounting Sequences Limit (Rep. Dominicana)",
    'summary': """Limits for fiscal invoices sequences""",
    'description': """""",
    'author': "José Romero",
    'website': "",
    'category': 'Accounting',
    'version': '16.0.0.1',
    'license': 'LGPL-3',
    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'l10n_do_accounting',
    ],
    # always loaded
    'data': [
        'views/account_journal_views.xml',
        'views/account_move_views.xml',
    ],
}
