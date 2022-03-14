from odoo import models, fields, api

from odoo.exceptions import UserError


class ResBank(models.Model):
    _inherit = 'res.bank'

    bank_code = fields.Char()
    bank_digi = fields.Char()


class ResCompany(models.Model):
    _inherit = 'res.partner.bank'

    account_type = fields.Selection([
        ('CC', 'Cuenta Corriente'),
        ('CA', 'Cuenta de Ahorro'),
    ], string='Account Type', default='CA')

    electronic_payroll_type = fields.Selection([
        ('BHD', 'Banco BHD'),
        ('BPD', 'Banco Popular'),
        ('BDR', 'Banco Reservas'),
        ('SCB', 'ScotianBank'),
        ('BC', 'Banco Caribe'),
    ], string='Electroni Payroll'
    )
    electronic_payroll_email = fields.Char(string='Email Payroll')
    electronic_payroll_bank_code = fields.Char(string='Bank Code')
    electronic_payroll_bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account')

class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    scotianban_sucursal = fields.Char(string="ScotianBank Sucursal")



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    electronic_payroll_type = fields.Selection([],
        readonly=0
    )
    electronic_payroll_email = fields.Char([],
        readonly=0
    )
    electronic_payroll_bank_code = fields.Char([],
        readonly=0
    )
    electronic_payroll_bank_account_id = fields.Many2one('res.partner.bank',
        [],
        readonly=0
    )
    module_electronic_payroll_account = fields.Boolean(
        string="Electronic Payroll - Account"
    )
    module_electronic_payroll_batch = fields.Boolean(
        string="Electronic Payroll - Batch Payment"
    )


class ElectronicPayroll(models.Model):
    _name = 'electronic.payroll'
    _description = 'Electronic Payroll'

    @api.depends('line_ids.amount')
    def _get_total(self):
        for rec in self:
            rec.total = sum([i.amount for i in rec.line_ids])
            rec.total_valid = sum([i.amount for i in rec.line_ids if not i.no_file])

    name = fields.Char(readonly=1)
    effective_date = fields.Date(string='Efective Date', required=1)
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Run',
                                     required=1)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda x: x.env.company)
    electronic_payroll_type = fields.Selection([], string='Type')
    binary = fields.Binary(readonly=1)
    binary_name = fields.Char(readonly=1)
    binary_ext = fields.Selection([('txt','TXT'), ('csv', 'CSV')], string='Extension', default='txt', required=1)
    total = fields.Float(compute='_get_total', string='Total')
    total_valid = fields.Float(compute='_get_total', string='Total to Paid')
    line_ids = fields.One2many('electronic.payroll.line', 'electronic_id')

    @api.onchange('payslip_run_id')
    def onchange_run_id(self):
        self.effective_date = self.payslip_run_id.date_end

    @api.model
    def create(self, vals):
        vals['company_id'] = self.env.user.company_id.id
        company = self.env['res.company'].browse(
            vals['company_id']
        )

        # code = company.electronic_payroll_type
        # if not code:
        #     raise UserError(
        #         "Your Company doesn't have Electronic Payroll configuration")

        seq = self.env['ir.sequence'].next_by_code('EP')

        #vals['name'] = code + seq

        #if code == 'BPD':
        #    date = fields.Date.to_date(vals['effective_date'])
        #    day = date.day
        #    month = date.month

        #    name_report = 'PE{num:>05}{ts}{mm:>02}{dd:>02}{seq}E'.format(
        #        num=company.electronic_payroll_bank_code,
        #        ts='01', mm=month, dd=day, seq=seq
        #    )

        #vals['name'] = name_report
        return super(ElectronicPayroll, self).create(vals)

    def set_line_ids(self):
        for electronic in self:
            if electronic.line_ids:
                raise UserError('Already the lines are loaded.')

            lines = []
            for slip in electronic.payslip_run_id.slip_ids:

                employee_id = slip.employee_id
                amount = slip._get_salary_line_total('NET')

                no_file = False
                if not amount or not employee_id.bank_account_id:
                    no_file = True

                lines.append(
                    (0, 0, {
                        'employee_id': employee_id.id,
                        'amount': amount,
                        'no_file': no_file,
                    })
                )

            electronic.line_ids = lines

    def generate_txt(self):
        if not self.line_ids:
            raise UserError('There are no lines to generate the file.')

        # ep_type = self.company_id.electronic_payroll_type
        # if not ep_type:
        #     raise UserError("Your Company doesn't have Electronic Payroll configuration")

        records = self.line_ids.filtered(
            lambda r: r.no_file == False and not r.bank_account_id
        )

        if records:
            raise UserError('Records without Bank Account')

        # generator = GeneratorType.get(ep_type)
        # file_io, file_value = generator.generate_txt(self)
        #
        # name = "{}.{}".format(self.name, self.binary_ext)
        # self.write({'binary': file_io, 'binary_name': name})

