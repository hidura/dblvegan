from odoo import models, _
from odoo.exceptions import UserError


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_res_company(self):
        result = super()._loader_params_res_company()
        result['search_params']['fields'].extend([
            'company_address',
            # 'l10n_do_ncf_expiration_date'
        ])
        return result

    def _loader_params_res_partner(self):
        result = super()._loader_params_res_partner()
        result['search_params']['fields'].extend(['l10n_do_dgii_tax_payer_type'])
        return result
