
from odoo import api, fields, models,_
import requests

class News(models.Model):
    _inherit = "hr.payslip.input"


    # name = fields.Char('Name')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    # amount = fields.Float("Amount")
    # date_from = fields.Date("From")
    # date_to = fields.Date("To")
    # state = fields.Selection([('inactive','Inactivo'),
    #                          ('active','Activo')])
    # type = fields.Selection([('recurring','Recurrente'),
    #                          ('unique','Unico')])
    # category_id = fields.Many2one('hr.payslip.input.type', 'Categoria')


class HR_Rule(models.Model):
    _inherit = "hr.salary.rule"

    employee_id = fields.Many2one('hr.employee', 'Employee')


class HRPaysipRun(models.Model):
    _inherit = "hr.payslip.run"

    def action_generate_file(self):
        warning_mess = {
            'title': _('Advertencia'),
            'message': "No tiene cuentas bancarias registradas o un usuario le falta su cuenta"
        }
        return {'warning': warning_mess}