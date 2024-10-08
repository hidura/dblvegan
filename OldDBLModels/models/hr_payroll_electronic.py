from odoo import models, fields, api


class ElectronicPayrollLine(models.Model):
    _name = 'electronic.payroll.line'
    _description = 'Electronic Payroll Line'

    electronic_id = fields.Many2one('electronic.payroll',
                                    string='Electonic Payroll')
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  readonly=True)

    bank_account_id = fields.Many2one('res.partner.bank',
                                      related='employee_id.bank_account_id')

    amount = fields.Float('Amount', readonly=True)

    no_file = fields.Boolean(string='No va al Archivo')


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    paid = fields.Selection([
        ('no', 'No pagada'),
        ('partial', 'Parcialmente Pagada'),
        ('complete', 'Pagada'),
    ], string='Estado del Pago', compute='set_paid_status')

    @api.depends('slip_ids')
    def set_paid_status(self):
        for i in self:
            paid_slips = i.slip_ids.filtered(lambda x: x.paid == True)
            no_paid_slips = i.slip_ids.filtered(lambda x: x.paid == False)

            total_slip = len(i.slip_ids)
            if len(paid_slips) == total_slip:
                status = 'complete'

            elif paid_slips and no_paid_slips:
                status = 'partial'

            elif not total_slip:
                status = 'no'

            else:
                status = 'no'

            i.paid = status



class ElectronicPayroll(models.Model):
    _inherit = 'electronic.payroll'

    def account_payment_method(self, date=None):
        """
        Method to create account Payment for each employee and Post it.

        :param date: Date the payment will be registered.
        """

        if not date:
            date = fields.Date.today()

        Payments = self.env['account.payment']

        line_ids = self.line_ids.filtered(lambda r: r.no_file is False)

        name = self.name
        payment_method_id = self.journal_id.inbound_payment_method_ids[0]
        journal_id = self.journal_id.id
        currency_id = self.company_id.currency_id.id
        for line in line_ids:
            partner_id = line.employee_id.address_home_id
            #partner_id.property_account_receivable_id = self.company_id.electronic_payroll_account_account.id
            payment_info = {
                'partner_id': partner_id.id,
                'payment_type': 'outbound',
                'partner_type': 'supplier',
                'amount': line.amount,
                'journal_id': journal_id,
                'currency_id': currency_id,
                'payment_date': date,
                'communication': _('Electronic Payroll: %s' % name),
                'payment_method_id': payment_method_id.id,
            }
            if hasattr(Payments, 'force_destination_account_id'):
                payment_info['force_destination_account_id'] = self.company_id.electronic_payroll_account_account.id

            payment_id = self.env['account.payment'].create(payment_info)
            Payments += payment_id

        self.write({'payment_count': len(line_ids), 'date_payment': date})
        Payments.post()
        Payments.create_batch_payment()
