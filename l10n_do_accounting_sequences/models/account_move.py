# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_fiscal_number_warning = fields.Boolean(
        'Alerta secuencia NCF/e-NCF', compute='_compute_l10n_fiscal_number_warning'
    )

    @api.depends('name', 'l10n_latam_document_type_id', 'journal_id')
    def _compute_l10n_fiscal_number_warning(self):
        for rec in self:
            if rec.l10n_latam_document_type_id and rec.is_sale_document() and rec.journal_id.l10n_latam_use_documents:
                l10n_do_sequence = rec._get_l10n_do_sequence()
                if rec.l10n_do_sequence_number >= l10n_do_sequence.l10n_do_warning_number:
                    rec.l10n_fiscal_number_warning = True
                else:
                    rec.l10n_fiscal_number_warning = False
            else:
                rec.l10n_fiscal_number_warning = False

    def format_sequence(self, prefix, sequence):
        sequence_length = 10 if prefix.startswith('E') else 8
        return f"{prefix}{sequence.zfill(sequence_length)}"

    def _get_fiscal_sequence(self):
        return self.journal_id.l10n_do_document_type_ids.filtered(
            lambda ldti: ldti.l10n_latam_document_type_id == self.l10n_latam_document_type_id
        )

    def _get_l10n_do_sequence(self):
        """Retrieve the sequence for the current document type in the journal."""
        sequence = self._get_fiscal_sequence()
        if not sequence:
            raise ValidationError(
                f"No se puede obtener la secuencia para este tipo de NCF: {self.l10n_latam_document_type_id.name}."
            )
        return sequence

    def _get_next_fiscal_number(self):
        self._check_max_number_exceeded()
        sequence = self._get_l10n_do_sequence()
        return sequence.l10n_do_number_next

    def _get_next_fiscal_sequence(self):
        next_fiscal_number = self._get_next_fiscal_number()
        prefix = self.l10n_latam_document_type_id.doc_code_prefix
        return self.format_sequence(prefix, str(next_fiscal_number))

    def _update_next_sequence(self):
        sequence = self._get_l10n_do_sequence()
        sequence.l10n_do_number_next += 1

    def _check_max_number_exceeded(self):
        sequence = self._get_l10n_do_sequence()
        if sequence.l10n_do_number_next > sequence.l10n_do_max_number:
            raise ValidationError(
                f"No tiene más comprobantes disponibles para la secuencia "
                f"*{self.l10n_latam_document_type_id.doc_code_prefix}-"
                f"{self.l10n_latam_document_type_id.name}*."
            )

    def _get_max_fiscal_number(self):
        sequence = self._get_l10n_do_sequence()
        return sequence.l10n_do_max_number

    def _post(self, soft=True):
        for rec in self:
            # Here we assign the next fiscal sequence before l10n_do_accounting, so
            # when the code goes through the l10n_do_accounting, the sequence assignment logic is not executed
            # this makes the validation of the invoice faster, and allow us to continue using l10n_do_accounting
            if rec.is_sale_document() and rec.journal_id.l10n_latam_use_documents and rec.country_code == 'DO' and not rec.l10n_do_fiscal_number:
                rec.l10n_do_fiscal_number = rec._get_next_fiscal_sequence()
                rec._compute_split_sequence()
                rec._update_next_sequence()
        res = super()._post(soft=soft)
        return res

    # Override to always get the sequence from journal
    @api.depends(
        "journal_id.l10n_latam_use_documents",
        "l10n_latam_manual_document_number",
        "l10n_latam_document_type_id",
        "company_id",
    )
    def _compute_l10n_do_enable_first_sequence(self):
        self.l10n_do_enable_first_sequence = False

    # Override to always get the sequence from journal
    def _l10n_do_is_new_expiration_date(self):
        self.ensure_one()
        return False
