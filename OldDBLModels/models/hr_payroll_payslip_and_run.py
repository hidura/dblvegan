# -*- coding: utf-8 -*-


from odoo import models, fields, api, _


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

    special_structure = fields.Boolean('Estructura Especial')


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    def set_simple_config(self):
        code = self.code

        amount_select = 'code'
        amount_python_compute = f'result = inputs.{code}.amount if inputs.{code} else 0'

        input_type = self.env['hr.payslip.input.type'].create({
            'name': self.name,
            'code': code,
            'struct_ids': [(4, self.struct_id.id, False)]
        })

        self.write({'amount_select': amount_select, 'amount_python_compute': amount_python_compute})




class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    @api.onchange('date_start')
    def _onchange_date_start(self):
        self.apply_on = '1' if self.date_start.day <= 15 else '2'

    def action_draft(self):
        slips = self.slip_ids.filtered(lambda slip: slip.state != 'done')

        for slip in slips:
            slip.action_payslip_cancel()
            slip.action_payslip_draft()

        return super(HrPayslipRun, self).action_draft()

    def re_calculate(self):
        for slip in self.slip_ids:
            if slip.state != 'done':
                slip.refresh_inputs()
                slip.compute_sheet()

    def verify_payslips(self):
        for slip in self.slip_ids:
            if slip.state not in ('done', 'cancel'):
                slip.action_payslip_verify()

        return self.write({'state': 'verify'})

    def remove_slips(self):
        slips = self.slip_ids.filtered(lambda slip: slip.state not in ('done', 'verify'))
        slips.unlink()

    def cancel_and_draft(self):
        for slip in self.slip_ids:
            slip.move_id.button_cancel()
            slip.state = 'verify'
            slip.action_payslip_cancel()
            slip.action_payslip_draft()

        self.action_draft()

    def send_payslip_by_email(self):
        self.slip_ids.send_payslip_by_email()


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

class PayslipInputImport(models.Model):
    _name = "payslip.input.import"
    _description = 'Import Payslip Input'

    name = fields.Char()

    active = fields.Boolean(default=1)
    input_id = fields.Many2one('hr.payslip.input.type', string='Novedad')
    code = fields.Char(related='input_id.code', string='Codigo')
    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True)
    amount = fields.Float(string="Importe")
    frecuency_type = fields.Selection(
        [
            ('fijo', 'Fijo'),
            ('variable', 'Variable')
        ], string="Tipo de frecuencia", default='fijo')

    apply_on = fields.Selection(
        [
            ('1', 'Primera Quincena'),
            ('2', 'Segunda Quincena'),
            ('3', 'Primera y. Segunda Quincena')
        ], string="Aplicar en", default='1'
    )

    frecuency_number = fields.Integer(string="Numero de veces", default=1)
    start_date = fields.Date(string="Fecha inicial", )
    end_date = fields.Date(string="Fecha final") #, compute='_calc_date_end', store=True)

    to_force = fields.Boolean('Solo Nomina Especiales')
    notes = fields.Text('Descripcion/Notas')

    @api.depends('input_id', 'code')
    def name_get(self):
        result = []
        for r in self:
            name = '[%s] %s' % (r.code, r.input_id.name)
            result.append((r.id, name))
        return result

    @api.onchange('frecuency_number', 'start_date', 'apply_on')
    def _calc_date_end(self):
        for i in self:
            if i.start_date:
                end_date = ''
                num_veces = i.frecuency_number -1 if i.frecuency_number > 0 else 1
                if i.apply_on in ('1', '2'):
                    end_date = fields.Date.add(i.start_date, months=num_veces)

                elif i.apply_on == '3':
                    end_date = fields.Date.add(i.start_date, months=int(num_veces/2), days=15)

                i.end_date = end_date
