
from odoo import models, fields


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
