# -*- coding: utf-8 -*-

import logging
from collections import defaultdict
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


def to_datetime(str_date):
    return fields.Date.from_string(str_date)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    apply_on = fields.Selection(
        [
            ('1', '1ra Quincena'),
            ('2', '2da Quincena'),
        ], string="Aplicar en", default='1'
    )

    @api.onchange('date_from')
    def _onchange_date_from(self):
        self.apply_on = '1' if self.date_from.day <= 15 else '2'

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        res = super(HrPayslip, self)._onchange_employee()

        input_line_vals = []

        self.input_line_ids.unlink()

        values = self.refresh_inputs()
        if values:
            for input_type_id, amount in values.items():
                input_line_vals.append((0, 0, {
                    'amount': amount,
                    'input_type_id': input_type_id,
                }))

        if input_line_vals:
            self.input_line_ids = input_line_vals

        return res

    def refresh_inputs(self):
        for i in self:
            if i.state != 'done':
                i.input_line_ids.unlink()

                i.apply_on = '1' if i.date_from.day <= 15 else '2'
                forced = self.struct_id.type_id.special_structure
                inputs = i.with_context({'forced': forced}).get_inputs()

                input_line_vals = []
                if inputs:
                    for input_type_id, amount in inputs.items():
                        input_line_vals.append({
                            'amount': amount,
                            'input_type_id': input_type_id,
                        })

                input_lines = i.input_line_ids.browse([])
                for r in input_line_vals:
                    input_lines |= input_lines.new(r)

                if input_lines:
                    i.input_line_ids = input_lines

    @api.model
    def get_inputs(self):

        apply_on = self.apply_on
        if not apply_on:
            apply_on = '1' if self.date_from.day <= 15 else '2'

        date_from = self.date_from
        date_to = self.date_to

        forced = self._context.get('forced')

        list_inputs_import = self.env['payslip.input.import'].search([
            ('employee_id', '=', self.employee_id.id),
            ('active', '=', 1),
            ('to_force', '=', forced),
            # ('end_date','>=', date_from),
        ])

        data = {}
        if list_inputs_import:
            for i in list_inputs_import:
                if (not i.end_date or date_from <= i.end_date) \
                        and (not i.start_date or i.start_date <= date_to) \
                        and (i.apply_on == apply_on or i.apply_on == '3'):
                    data.setdefault(i.input_id.id, 0)
                    data[i.input_id.id] += i.amount

        return data

    def action_payslip_verify(self):
        return self.write({'state': 'verify'})

    def get_total_format(self, code):
        return '{:,.2f}'.format(self._get_salary_line_total(code))

    def send_payslip_by_email(self):
        template_id = self.env.ref('l10n_do_hr_payroll.payslip_email')
        self.message_post_with_template(template_id.id)
