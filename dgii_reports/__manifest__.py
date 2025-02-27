# Part of Domincana Premium.
# See LICENSE file for full copyright and licensing details.
# © 2018 José López <jlopez@indexa.do>
# © 2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2018 Eneldo Serrata <eneldo@marcos.do>

{
    'name': "Declaraciones DGII",

    'summary': """
        Este módulo extiende las funcionalidades del do_accounting,
        integrando los reportes de declaraciones fiscales""",

    'author': "Indexa, SRL, "
              "iterativo SRL",
    'license': 'LGPL-3',
    'category': 'Accounting',
    'version': '16.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'l10n_do_accounting'],

    # always loaded
    'data': [
        'data/invoice_service_type_detail_data.xml',
        'data/ir_config_parameter_data.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/res_partner_views.xml',
        'views/account_tax_views.xml',
        'views/account_account_views.xml',
        'views/account_move_views.xml',
        'views/dgii_report_views.xml',
        'wizard/dgii_report_regenerate_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/dgii_reports/static/src/less/dgii_reports.scss',
            '/dgii_reports/static/src/js/widget.js'
        ],
    },
    'external_dependencies': {
        'python': ['pycountry']
    },
}
