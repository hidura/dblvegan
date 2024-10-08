# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ParticularReport(models.AbstractModel):
    _name = 'report.payroll_batch_report.report_paysliprun'
    _description = 'AbstractModel Report Payslip Run'

    def _get_column_header(self, run_ids):
        query = '''
          select distinct l.code
          from hr_payslip_line l, hr_salary_rule s 
          where l.salary_rule_id = s.id and slip_id in (
            select id from hr_payslip where payslip_run_id in %s)
          and l.total > 0 and s.appears_on_payslip = true order by s.sequence
        '''
        self.env.cr.execute(query, (tuple(run_ids),))

        cols = self.env.cr.fetchall()
        _logger.info(('aqui/////////', [col[0] for col in cols]))
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

          ORDER BY c.id
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

        header = self._get_column_header(run_ids)
        lines = self._get_data_line(run_ids, header)
        info = self._get_employee_info(run_ids)

        # Default Dict with All Rule Salary in 0 (ZERO)
        ddict = {k: 0 for k in header}

        data_lines = {}
        for line in lines:
            # contract_id
            cid = line[0]

            if cid not in data_lines:
                data_lines[cid] = ddict.copy()

                if cid not in info:
                    continue

                # remove_special_letters(info[cid]['employee_name'])
                name = info[cid]['employee_name']

                data_lines[cid] = {
                    'employee_name': name,
                    'num_document': info[cid]['num_document'],
                    'department_id': info[cid]['department_id'],
                    'job_id': info[cid]['job_id'],
                    'wage': info[cid]['wage'],
                }

            data_lines[cid][line[1]] = line[2]

        return data_lines

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('payroll_batch_report.report_paysliprun')

        data = self._get_data(docids)
        _logger.info(('Los Datos /*/*/*/', docids, self))
        docargs = {
            'doc_ids': docids,
            'doc_model': 'hr.payslip.run',
            'docs': self,
            'data': {'lines': data},
            'header': self._get_column_header(docids)
        }
        return docargs


class PayslipRun(models.AbstractModel):
    _inherit = 'hr.payslip.run'

    def get_code_name(self):
        data = {}
        rules = self.env['hr.salary.rule'].search([])
        for r in rules:
            data[r.code] = r.name
        return data

    def get_data_total(self, run_ids, header):

        query = """
          select code, SUM(total)
            from hr_payslip_line
            where contract_id in (
                select contract_id from hr_payslip where payslip_run_id in %s)
             and slip_id in (select id from hr_payslip where payslip_run_id in %s)
             and code in %s group by code;
        """

        self.env.cr.execute(query, (tuple(run_ids), tuple(run_ids), tuple(header)))

        return dict(self.env.cr.fetchall())

    def get_column_header(self, run_ids):
        query = '''
          select distinct l.code, s.sequence
          from hr_payslip_line l, hr_salary_rule s 
          where l.salary_rule_id = s.id and slip_id in (
            select id from hr_payslip where payslip_run_id in %s)
          and l.total > 0 and s.appears_on_payslip = true order by s.sequence
        '''
        self.env.cr.execute(query, (tuple(run_ids),))

        cols = self.env.cr.fetchall()

        return [col[0] for col in cols]

    def get_data_line(self, run_ids, header):

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

    def get_employee_info(self, run_ids):
        extra = ''

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

    def get_data(self, run_ids):

        header = self.get_column_header(run_ids)
        lines = self.get_data_line(run_ids, header)
        info = self.get_employee_info(run_ids)

        # Default Dict with All Rule Salary in 0 (ZERO)
        ddict = {k: 0 for k in header}

        data_lines = {}
        for line in lines:
            # contract_id
            cid = line[0]

            if cid not in data_lines:
                data_lines[cid] = ddict.copy()

                if cid not in info:
                    continue

                # remove_special_letters(info[cid]['employee_name'])
                name = info[cid]['employee_name']

                data_lines[cid] = {
                    'employee_name': name,
                    'num_document': info[cid]['num_document'],
                    'department_id': info[cid]['department_id'],
                    'job_id': info[cid]['job_id'],
                    'wage': info[cid]['wage'],
                }

            data_lines[cid][line[1]] = line[2]

        return data_lines
