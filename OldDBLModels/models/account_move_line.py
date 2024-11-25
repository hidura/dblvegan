from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_l10n_do_line_amounts(self):
        res = super()._get_l10n_do_line_amounts()
        group_itbis = self.env.ref("l10n_do.group_itbis")
        group_isr = self.env.ref("l10n_do.group_isr")
        other_taxes_lines = self.filtered(
            lambda x: x.tax_line_id and x.tax_line_id.tax_group_id not in [group_itbis, group_isr]
        )
        other_taxes_amount = sum(
            abs(self.currency_id.round(line.amount_currency)) for line in other_taxes_lines
        )
        rate = round(self.move_id.amount_total_signed / self.move_id.amount_total, 2)
        res["l10n_do_invoice_total"] += other_taxes_amount
        res["l10n_do_invoice_total_currency"] += other_taxes_amount * rate

        return res
