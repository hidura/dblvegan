# -*- coding: utf-8 -*-

import base64
import io
import logging

from .interface import GeneratorInterface

_logger = logging.getLogger(__name__)


class BHDTemplate(GeneratorInterface):

    name = 'Banco BHD'
    code = 'BHD'

    def generate_txt(self, obj):
        file_io = io.BytesIO()

        lines = ''
        for line in obj.line_ids:
            if line.no_file:
                continue

            name = self.remove_accent(line.employee_id.name)

            account = line.bank_account_id.acc_number.replace('-', '')
            amount = str('%.2f' % line.amount)

            lines += "%s;%s;%s;%s;%s;\n" % (account, name, line.employee_id.id, amount, self.description)

        file_io.write(str.encode(lines))

        report_value = file_io.getvalue()

        report = base64.encodestring(report_value)
        file_io.close()

        return report, report_value

