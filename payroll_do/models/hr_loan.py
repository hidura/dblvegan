
from odoo import api, fields, models
import requests

class HRLoans(models.Model):
    _name = "hr.loans"

    name = fields.Char('Name')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    amount = fields.Float("Amount")
    pay_division = fields.Selection([('1','1 Quincena'),
                                     ('2','2 Quincenas'),
                                     ('3','3 Quincenas'),
                                     ('4','4 Quincenas'),
                                     ('5','5 Quincenas'),
                                     ('6','6 Quincenas'),
                                     ('7','7 Quincenas'),
                                     ('8','8 Quincenas'),
                                     ('9','9 Quincenas'),
                                     ('10','10 Quincenas'),
                                     ('11','11 Quincenas'),
                                     ('12','12 Quincenas')])
    date_from = fields.Date("From")
    date_to = fields.Date("To")
    state = fields.Selection([('draft','Borrador'),
                             ('inprogress','En Progreso'),
                             ('done','Hecho'),
                             ('paid','Pagado')])
    struct_id = fields.Many2one('hr.payroll.structure', string="Salary Structure", required=True)

    @api.model
    def create(self, vals):
        record = super(HRLoans, self).create(vals)
        self.env['hr.salary.rule'].create({'name':record.name,
                                           'code':record.name,
                                           'struct_id':record.struct_id.id,
                                           'quantity':1,
                                           'amount_fix':record.amount/int(record.pay_division[0]),
                                           'category_id':4})

        return record

    @api.model
    def write(self, vals, data):
        record = super(HRLoans, self).write(data)
        if 'state' in data:
            if data['state']=='paid':
                loan = self.env['hr.loans'].search([('id','=',vals[0])])
                rule = self.env['hr.salary.rule'].search([('name', '=', loan.name)])
                rule.write({'active':False})
        return record