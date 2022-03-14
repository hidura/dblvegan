# -*- coding: utf-8 -*-

import base64
import io
import logging

from .interface import GeneratorInterface

_logger = logging.getLogger(__name__)


class BDRTemplate(GeneratorInterface):

    name = 'Banco del Reservas'
    code = 'BDR'

    def generate_txt(self, obj):
        """
        Ejemplo del formato suministrado por la empresa Laso.
        Estos utilizan un excel suministrado por BanReservas dicho excel
        genera el TXT de la siguiente forma.

        tipo_cuenta,moneda,cueta_origen,tipo_cuenta,moneda,cuenta_empl,monto,descripcion
        CA,DOP,9603137901,CA,DOP,9603417833,8232.88,Nomina Q1 de Julio 2021
        """
        file_io = io.BytesIO()

        origin_account_obj = obj.company_id.electronic_payroll_bank_account_id
        origin_account_number = origin_account_obj.acc_number.replace('-', '').zfill(9)
        origin_account_type = origin_account_obj.account_type
        origin_account_currency = origin_account_obj.currency_id.name or 'DOP'

        lines = ''
        for line in obj.line_ids:
            if line.no_file:
                continue

            account_empl_obj = line.bank_account_id
            account_empl_number = account_empl_obj.acc_number.replace('-', '').zfill(9)
            account_empl_type = account_empl_obj.account_type
            account_empl_currency = account_empl_obj.currency_id.name or 'DOP'

            amount = str('%.2f' % line.amount)

            data = {
                'company_acc_type': origin_account_type,
                'company_acc_number': origin_account_number,
                'company_acc_currency': origin_account_currency,
                'employee_acc_type': account_empl_type,
                'employee_acc_number': account_empl_number,
                'employee_acc_currency': account_empl_currency,
                'amount': amount,
                'description': self.description,
            }

            lines += "{company_acc_type},{company_acc_currency},{company_acc_number},{employee_acc_type},{employee_acc_currency},{employee_acc_number},{amount},{description}\n".format(**data)

        file_io.write(str.encode(lines))

        report_value = file_io.getvalue()

        report = base64.encodestring(report_value)
        file_io.close()

        return report, report_value

