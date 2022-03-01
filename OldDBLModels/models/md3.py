
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


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
