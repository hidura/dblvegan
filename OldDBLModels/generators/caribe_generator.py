# -*- coding: utf-8 -*-

import base64
import io
import logging

from .interface import GeneratorInterface

_logger = logging.getLogger(__name__)


class CaribeTemplate(GeneratorInterface):

    name = 'Banco Caribe'
    code = 'BC'

    def generate_txt(self, obj):
        file_io = io.BytesIO()

        origin_account = obj.company_id.electronic_payroll_bank_account_id.acc_number.replace('-', '').zfill(9)

        lines = ''
        for pos, line in enumerate(obj.line_ids.filtered(lambda l: not l.no_file), start=1):
            if line.no_file:
                continue

            account = line.bank_account_id.acc_number.replace('-', '').zfill(9)
            amount = str('%.2f' % line.amount)

            lines += "%s,%s,%s,%s\n" % (pos, account, line.employee_id.name, amount)

        file_io.write(str.encode(lines))

        report_value = file_io.getvalue()

        report = base64.encodestring(report_value)
        file_io.close()

        return report, report_value

