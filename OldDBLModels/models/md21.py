# -*- coding: utf-8 -*-

import logging

from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import rnc, cedula
except (ImportError, IOError) as err:
    _logger.debug(err)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(ResPartner, self).name_search(
            name,
            args=args,
            operator=operator,
            limit=100
        )
        if not res and name:
            if len(name) in (9, 11):
                partners = self.search([('vat', '=', name)])
            else:
                partners = self.search([('vat', 'ilike', name)])
            if partners:
                res = partners.name_get()
        return res

    @api.model
    def validate_rnc_cedula(self, number):

        company_id = self.env.user.company_id

        if number and str(number).isdigit() and len(number) in (9, 11):
            # and company_id.can_validate_rnc:
            #

            result, dgii_vals = {}, False
            model = self.env.context.get('model')

            if model == 'res.partner' and self:
                self_id = [self.id, self.parent_id.id]
            else:
                self_id = [company_id.id]

            # Considering multi-company scenarios
            domain = [
                ('vat', '=', number),
                ('id', 'not in', self_id),
                ('parent_id', '=', False)
            ]

            if self.sudo().env.ref('base.res_partner_rule').active:
                domain.extend([('company_id', '=', company_id.id)])
            contact = self.search(domain)

            if contact:
                name = contact.name if len(contact) == 1 else ", ".join(
                    [x.name for x in contact if x.name])
                raise UserError(_('RNC/Cédula %s is already assigned to %s')
                                % (number, name))

            is_rnc = len(number) == 9
            try:
                rnc.validate(number) if is_rnc else cedula.validate(number)
            except Exception:
                _logger.warning(
                    "RNC/Ced is invalid for partner {}".format(self.name))

            try:
                dgii_vals = rnc.check_dgii(number)
            except:
                pass

            if not bool(dgii_vals):
                result['vat'] = number
            else:
                result['name'] = dgii_vals.get('name', False)
                result['vat'] = dgii_vals.get('rnc')
                if model == 'res.partner':
                    result['is_company'] = is_rnc
            return result

    def _get_updated_vals(self, vals):
        new_vals = {}
        if any([val in vals for val in ['name', 'vat']]):
            vat = vals["vat"] if vals.get('vat') else vals.get('name')
            result = self.with_context(model=self._name).validate_rnc_cedula(vat)
            if result is not None:
                if 'name' in result:
                    new_vals['name'] = result.get('name')
                new_vals['vat'] = result.get('vat')
                new_vals['ref'] = result.get('ref')
                new_vals['is_company'] = result.get('is_company', False)
                new_vals['company_type'] = 'company' if new_vals['is_company'] else 'person'
                if not vals.get('phone'):
                    new_vals['phone'] = result.get('phone')
                if not vals.get('street'):
                    new_vals['street'] = result.get('street')
        return new_vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.update(self._get_updated_vals(vals))
        return super(ResPartner, self).create(vals_list)

    @api.model
    def name_create(self, name):
        if self._context.get('install_mode', False):
            return super(ResPartner, self).name_create(name)
        if self._rec_name:
            if name.isdigit():
                partner = self.search([('vat', '=', name)])
                if partner:
                    return partner.name_get()[0]
                else:
                    new_partner = self.create({"vat": name})
                    return new_partner.name_get()[0]
            else:
                return super(ResPartner, self).name_create(name)
