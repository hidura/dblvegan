# import logging
# _logger = logging.getLogger(__name__)
# try:
#     from stdnum.do import rnc, cedula
# except (ImportError, IOError) as err:
#     _logger.debug(str(err))

from odoo import models, api
# from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create_from_ui(self, partner):
        # Delete search from dict if exists, is only use to search in Partner Screen
        partner.pop('search', False)
        return super().create_from_ui(partner)

    def _format_l10n_do_dgii_payer_type(self, vat, name, country_id):
        """ Compute the type of partner depending on soft decisions"""
        company_id = self.env.user.company_id
        partner = {'l10n_do_dgii_tax_payer_type': ''}
        vat = str(vat if vat else name)

        if country_id and not isinstance(country_id, int):
            country_id = country_id.id

        is_dominican_partner = bool(country_id == self.env.ref("base.do").id)
        if country_id and not is_dominican_partner:
            partner['l10n_do_dgii_tax_payer_type'] = "foreigner"
        elif vat:
            if country_id and is_dominican_partner:
                if vat.isdigit() and len(vat) == 9:
                    if not vat:
                        vat = vat
                    if name and "MINISTERIO" in name:
                        partner['l10n_do_dgii_tax_payer_type'] = "governmental"
                    elif name and any(
                            [n for n in ("IGLESIA", "ZONA FRANCA") if n in name]
                    ):
                        partner['l10n_do_dgii_tax_payer_type'] = "special"
                    elif vat.startswith("1"):
                        partner['l10n_do_dgii_tax_payer_type'] = "taxpayer"
                    elif vat.startswith("4"):
                        partner['l10n_do_dgii_tax_payer_type'] = "nonprofit"
                    else:
                        partner['l10n_do_dgii_tax_payer_type'] = "taxpayer"

                elif len(vat) == 11:
                    if vat.isdigit():
                        payer_type = (
                            "taxpayer"
                            if company_id.l10n_do_default_client == "taxpayer"
                            else "non_payer"
                        )
                        partner['l10n_do_dgii_tax_payer_type'] = payer_type
                    else:
                        partner['l10n_do_dgii_tax_payer_type'] = "non_payer"
                else:
                    partner['l10n_do_dgii_tax_payer_type'] = "non_payer"
        elif not partner['l10n_do_dgii_tax_payer_type']:
            partner['l10n_do_dgii_tax_payer_type'] = "taxpayer"
        else:
            partner['l10n_do_dgii_tax_payer_type'] = (
                partner['l10n_do_dgii_tax_payer_type']
            )

        return partner

    # def format_from_dggi(self, vat):
    #     if not vat.isdigit() or len(vat) not in [9, 11]:
    #         raise UserError("RNC incorrecto, por favor corregir.")
    #
    #     vat_exists = self.search([('vat', '=', vat)])
    #     if vat_exists:
    #         raise UserError("Ya existe un cliente con este RNC")
    #
    #     return {'payer_type': self._format_l10n_do_dgii_payer_type(vat)}
