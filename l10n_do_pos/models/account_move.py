from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_document_type_dict(self, prefix):
        document_type = self.env['l10n_latam.document.type'].search([
            ('doc_code_prefix', '=', prefix)
        ])
        if not document_type:
            raise ValidationError('No se ha encontrado tipo de documento para el código {}'.format(prefix))

        return document_type.id

    @api.constrains('state', 'l10n_latam_document_type_id')
    def _check_l10n_latam_documents(self):
        """ This constraint checks that if a invoice is posted and does not have a document type configured will raise
        an error. This only applies to invoices related to journals that has the "Use Documents" set as True.
        And if the document type is set then check if the invoice number has been set, because a posted invoice
        without a document number is not valid in the case that the related journals has "Use Docuemnts" set as True """
        validated_invoices = self.filtered(
            lambda x: x.l10n_latam_use_documents
                      and x.state == 'posted'
                      and x.country_code == "DO"
                      and x.is_sale_document()
                      and x.partner_id
        )
        without_doc_type = validated_invoices.filtered(lambda x: not x.l10n_latam_document_type_id)
        for inv in without_doc_type:
            tax_payer_type = inv.partner_id.l10n_do_dgii_tax_payer_type
            is_ecf_issuer = inv.company_id.l10n_do_ecf_issuer
            if tax_payer_type in ('taxpayer', 'nonprofit'):
                without_doc_type.l10n_latam_document_type_id = self._get_document_type_dict(is_ecf_issuer and "E31" or "B01")
            elif not tax_payer_type and inv.partner_id.country_id.code == 'DO' or tax_payer_type == 'non_payer':
                without_doc_type.l10n_latam_document_type_id = self._get_document_type_dict(is_ecf_issuer and "E32" or "B02")
            elif tax_payer_type == 'special':
                without_doc_type.l10n_latam_document_type_id = self._get_document_type_dict(is_ecf_issuer and "E44" or "B14")
            elif tax_payer_type == 'governmental':
                without_doc_type.l10n_latam_document_type_id = self._get_document_type_dict(is_ecf_issuer and "E45" or "B15")

        if without_doc_type:
            raise ValidationError(_(
                'The journal require a document type but not document type has been selected on invoices %s.',
                without_doc_type.ids
            ))
        without_number = validated_invoices.filtered(
            lambda x: not x.l10n_latam_document_number and x.l10n_latam_manual_document_number)

        if without_number:
            raise ValidationError(_(
                'Please set the document number on the following invoices %s.',
                without_number.ids
            ))
