{
    'name': "República Dominicana - POS",
    'summary': """Incorpora funcionalidades de facturación con NCF al POS""",
    'author': "Adel Networks S.R.L",
    'license': 'LGPL-3',
    'category': 'Localization',
    'version': '16.0',
    'depends': ['l10n_do_accounting', 'point_of_sale'],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/pos_config.xml',
        'views/pos_view.xml',
        'views/pos_payment_method_view.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'l10n_do_pos/static/src/css/*.css',
            'l10n_do_pos/static/src/js/**/*.js',
            'l10n_do_pos/static/src/xml/**/*',
        ],
    },
}
