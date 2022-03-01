# -*- coding: utf-8 -*-

import logging
from itertools import groupby
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class WizardPayslipReportXlsx(models.TransientModel):
    _name = 'wizard.payroll_report.xlsx'
    _description = 'Wizard Payroll Report XLSX'

    payslip_run_ids = fields.One2many('wizard.payroll_report_line.xlsx', 'wizard_id',
                                      string='Payslip Run',
                                      required=1)

    num_document = fields.Boolean(default=1, string="Num. Document")
    department = fields.Boolean(default=1, string="Department")
    job = fields.Boolean(default=1, string="Job Position")
    wage = fields.Boolean(default=1, string="Wage")

    filter_by = fields.Selection([
        ('department', 'Department'),
        ('job', 'Job'),
    ], string='Filter BY')

    department_id = fields.Many2one('hr.department', string='By Department')
    job_id = fields.Many2one('hr.job', string='By Job position')

    def _get_column_header(self, run_ids):
        query = '''
          select distinct l.code
          from hr_payslip_line l, hr_salary_rule s
          where l.salary_rule_id = s.id and slip_id in (
            select id from hr_payslip where payslip_run_id in %s)
          and l.total > 0
        '''
        self.env.cr.execute(query, (tuple(run_ids),))

        cols = self.env.cr.fetchall()

        return [col[0] for col in cols]

    def _get_data_line(self, run_ids, header):

        query = """
          select contract_id, code, SUM(total)
            from hr_payslip_line
            where contract_id in (
                select contract_id from hr_payslip where payslip_run_id in %s)
             and slip_id in (select id from hr_payslip where payslip_run_id in %s)
             and code in %s group by contract_id, code
            order by contract_id;
        """

        self.env.cr.execute(query, (tuple(run_ids), tuple(run_ids), tuple(header)))

        return self.env.cr.fetchall()

    def _get_employee_info(self, run_ids):
        extra = ''
        if self.filter_by == 'department':
            extra = 'and d.id = %d' % self.department_id.id
        elif self.filter_by == 'job':
            extra = 'and j.id = %d' % self.job_id.id

        query = """
          SELECT DISTINCT c.id, e.name, e.identification_id, 
            COALESCE(d.id, 0), COALESCE(d.name, 'Indefinido'),
            COALESCE(j.id, 0), COALESCE(j.name, 'Indefinido'), c.wage
          FROM hr_contract AS c 
              INNER JOIN hr_employee AS e ON c.employee_id = e.id
              INNER JOIN hr_payslip AS s ON s.contract_id = c.id
              LEFT JOIN hr_job AS j ON j.id = c.job_id
              LEFT JOIN hr_department AS d ON d.id = c.department_id
          WHERE c.id IN (
              SELECT contract_id FROM hr_payslip WHERE payslip_run_id in %s )

          ORDER BY e.name
        """
        self.env.cr.execute(query, (tuple(run_ids),))

        employees = self.env.cr.fetchall()
        info = {
            e[0]: {
                'employee_name': e[1],
                'num_document': e[2],
                'wage': e[7],
                'department_id': {'id': e[3], 'name': e[4]},
                'job_id': {'id': e[5], 'name': e[6]},
                'none': {'id': '', 'name': ' '},  # When not GroupBy
            } for e in employees
        }
        return info

    def _get_data(self, run_ids):
        filter = False
        if self.filter_by == 'department':
            filter = self.department_id.id
        elif self.filter_by == 'job':
            filter = self.job_id.id

        header = self._get_column_header(run_ids)
        lines = self._get_data_line(run_ids, header)
        info = self._get_employee_info(run_ids)

        # Default Dict with All Rule Salary in 0 (ZERO)
        ddict = {k: 0 for k in header}

        data_lines = {}
        for line in lines:
            # contract_id
            cid = line[0]
            contract_name = self.env['hr.contract'].browse(cid).name

            if self.filter_by:
                opc = info[cid][self.filter_by + '_id']['id']
                if not opc or opc != filter:
                    continue

            if cid not in data_lines:
                data_lines[cid] = ddict.copy()

                if cid not in info:
                    continue

                name = info[cid]['employee_name']  # remove_special_letters(info[cid]['employee_name'])

                data_lines[cid] = {
                    'employee_name': name,
                    'num_document': info[cid]['num_document'],
                    'department_id': info[cid]['department_id'],
                    'job_id': info[cid]['job_id'],
                    'contract': contract_name,
                    'wage': info[cid]['wage'],
                }
                # data_lines[cid][self.group_by] = info[cid][self.group_by]

            data_lines[cid][line[1]] = line[2]

        # sort = sorted(data_lines, key=lambda i: data_lines[i]['department_id']['id'])
        # groups = groupby(sort, key=lambda i: data_lines[i]['department_id']['name'])
        #
        # data = {}
        # for key, vals in groups:
        #     data[key] = []
        #
        #     for v in vals:
        #         data[key].append(data_lines[v])

        return data_lines

    @api.onchange('filter_by')
    def onchange_filter_by(self):
        self.department_id = False
        self.job_id = False

    def generate_report(self):
        run_ids = [i.run_id.id for i in self.payslip_run_ids]
        company_id = self.payslip_run_ids[0].run_id.company_id.logo
        #
        # if self.by_period:
        #     temp = self.env['hr.payslip.run'].search(
        #         [
        #             ('date_start', '>=', '{}-{}-01'.format(self.year, self.month)),
        #             ('date_end', '<', '{}-{}-01'.format(self.year, str(int(self.month) + 1))),
        #             # ('company_id', '=', self.env.user.company_id.id)
        #         ]
        #     )
        #     run_ids = [t.id for t in temp]

        data = self._get_data(run_ids)

        opcs_dict = {
            'department': self.department,
            'job': self.job,
            'wage': self.wage,
            'num_document': self.num_document,
        }

        hidden = [k for k, v in opcs_dict.items() if v == False]

        return self.env.ref('payroll_report.template_xlsx').with_context({
            'lines': data, 'hidden': hidden, 'run_ids': run_ids, 'logo': company_id}).report_action(self)  # ,data=})


class WizardPayslipReportLineXlsx(models.TransientModel):
    _name = 'wizard.payroll_report_line.xlsx'
    _description = 'Wizard Payroll Report Line XLSX'

    wizard_id = fields.Many2one('wizard.payroll_report.xlsx')

    run_id = fields.Many2one('hr.payslip.run', string="Nomina")
