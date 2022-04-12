# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def create(self, vals):
        empl_info=self.env['hr.employee'].search([('id','=',vals['employee_id'])])
        vals['name']='Recibo de Salario - {} - {}'.format(self.empl_info.name,self.number)


        record = super(HrPayslip, self).create(vals)
        return record
    def _prepare_line_values(self, line, account_id, date, debit, credit):

        data = {
            'name': line.name,
            'partner_id': line.partner_id.id,
            'account_id': account_id,
            'journal_id': line.slip_id.struct_id.journal_id.id,
            'date': date,
            'debit': debit,
            'credit': credit,
            'analytic_account_id': line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id,
        }

        partner_id = line.slip_id.employee_id.address_home_id.id
        if line.salary_rule_id.show_partner and partner_id:
            data['partner_id'] = partner_id

        return data

    def _get_existing_lines(self, line_ids, line, account_id, debit, credit):
        partner_id = line.slip_id.employee_id.address_home_id.id

        if line.salary_rule_id.show_partner and partner_id:
            partner_id = line.slip_id.employee_id.address_home_id.id
            existing_lines = (
                line_id for line_id in line_ids if
                line_id['name'] == line.name
                and line_id['account_id'] == account_id
                and line_id['analytic_account_id'] == (
                        line.salary_rule_id.analytic_account_id.id
                        or line.slip_id.contract_id.analytic_account_id.id
                )
                and (
                        (line_id['debit'] > 0 and credit <= 0)
                        or (line_id['credit'] > 0 and debit <= 0)
                )
                and (line_id['partner_id'] == partner_id)
            )

        else:
            existing_lines = (
                line_id for line_id in line_ids if
                line_id['name'] == line.name
                and line_id['account_id'] == account_id
                and line_id['analytic_account_id'] == (
                        line.salary_rule_id.analytic_account_id.id
                        or line.slip_id.contract_id.analytic_account_id.id
                )
                and (
                        (line_id['debit'] > 0 and credit <= 0)
                        or (line_id['credit'] > 0 and debit <= 0)
                )
            )

        return next(existing_lines, False)


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    show_partner = fields.Boolean('Mostrar Auxiliar',
                                  help='Muestra el empleado (dirrecion) como auxiliar en el asiento de nomina.')