# -*- coding: utf-8 -*-
import base64
import io
import logging

from odoo.exceptions import UserError

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

SPECIALS = {
    u'á': 'a', u'Á': 'A',
    u'é': 'e', u'É': 'E',
    u'í': 'i', u'Í': 'I',
    u'ó': 'o', u'Ó': 'O',
    u'ú': 'u', u'Ú': 'U',
    u'ñ': 'n', u'Ñ': 'N',
}


class WizardPaymentPopularTXT(models.TransientModel):
    _name = 'wizard.payment.popular.txt'
    _description = 'Wizard Pago Suplidor TXT - Popular'

    file_name = fields.Char()
    file_binary = fields.Binary()

    def remove_accent(self, word):
        # Si el nombre contienes unos de los caracteres especiales
        # lo remplaza con su semejante sin asento.
        for letter in SPECIALS.keys():
            if letter in word:
                word = word.replace(letter, SPECIALS[letter])
        return word

    def generate_txt(self):

        full = '{:%Y%m%d}'.format(fields.Date.today())

#        seq = self.env['ir.sequence'].search(
#            [('code', '=', 'BPD'),
#             #('company_id', '=', self.company_id.id)
#            ], limit=1
#        ).number_next_actual
#        #seq = seq - 1
        seq = self.env['ir.sequence'].next_by_code('BPD')
        file_io = io.BytesIO()

        credit_lines = 0  # cantidad credito / Cuantas Trans. (lineas) se haran.
        amount_credit = 0  # monto credito / El total de Dinero a Trans.

        payment_ids = self.env.context.get('active_ids')
        payments = self.env['account.payment'].browse(payment_ids)
        company_id = payments[0].company_id
        rnc = company_id.vat
        lines = ''
        position = 1
        for line in payments:
            partner = line.partner_id
            name = self.remove_accent(partner.name)

            # Tipo de Documento
            # RN - RNC
            # CE - Cedula
            # PS - Pasaporte
            # OT - Otro (NUmero de Suplidor, ETC)
            doc_type = 'CE'

            num_doc = partner.vat
            if not num_doc:
                raise UserError("%s no tiene una Cedula/RNC establecida" % partner.name)

            if len(num_doc) == 9:
                doc_type = 'RN'

            num_doc = num_doc.replace(' ', '')
            credit_lines += 1
            amount_credit += line.amount

            bank_account_id = partner.bank_ids[0] if partner.bank_ids else False

            if not bank_account_id:
                raise UserError("%s no tiene Cuenta de Banco Registrada" % partner.name)

            account_type = bank_account_id.account_type
            cod_operation = 22 if account_type == '1' else 32

            account = str(bank_account_id.acc_number).replace('-', '').zfill(9)

            amount = str('%.2f' % line.amount).replace('.', '').zfill(13)

            work_email = partner.email
            if work_email:
                work_email = work_email.ljust(40)

            send_email = work_email and '1' or ' '


            linea = "N{rnc}{seq}{posicion}{cuenta}{tipo_cuenta}{moneda}{cod_banco_destino}{digi}{cod_ope}{monto}{tipoid}{id}{nombre}{num_ref}{concepto}{fecha_vencimiento}{forma_contacto}{email_empl}{fax}00{resp_banco}{filler}".format(
                rnc=str(rnc).ljust(15),
                seq=str(seq).zfill(7),
                posicion=str(position).zfill(7),
                tipo_cuenta=account_type,
                moneda=214, # Indique que la moneda es en Peso Dominicano
                cod_banco_destino=bank_account_id.bank_id.bank_code,
                digi=bank_account_id.bank_id.bank_digi,
                cod_ope=cod_operation,
                cuenta=str(account).ljust(20),
                filler=''.ljust(52),
                monto=str(amount).ljust(13),
                tipoid=doc_type,
                id=num_doc.ljust(15),
                nombre=name.ljust(35)[:35],
                num_ref='Pago'.ljust(12),
                concepto=''.ljust(40), fecha_vencimiento='    ',
                forma_contacto=send_email,
                email_empl=work_email,
                fax=''.ljust(12), resp_banco=''.ljust(27)

            )

            lines += linea + '\r\n'
            position += 1

        amount_credit = str('%.2f' % amount_credit).replace('.', '').zfill(13)
        credit_lines = str(credit_lines).zfill(11)

        header = 'H{rnc}{nombre}{seq}{tipo}{fec}{cd}{md}{numtrans}{totalapagar}{num_afil}{fec}{email}{resp_banco}{filler}'.format(
            rnc=str(rnc).ljust(15), nombre=company_id.name.ljust(35)[:35],
            seq=str(seq).zfill(7), tipo='02',
            fec=full, cd='00000000000', md='0000000000000',
            totalapagar=amount_credit, numtrans=credit_lines, num_afil='000000000000000',
            email=company_id.electronic_payroll_email, resp_banco=' ',
            filler=''.ljust(136)
        )

        d = '{}\r\n'.format(header)
        file_io.write(str.encode(d))
        file_io.write(str.encode(lines))
        file_value = file_io.getvalue()
        report = base64.encodestring(file_value)
        file_io.close()
        date = fields.Date.today()
        day = date.day
        month = date.month

        name_report = 'PE{num:>05}{ts}{mm:>02}{dd:>02}{seq}E'.format(
                num=company_id.electronic_payroll_bank_code,
                ts='02', mm=month, dd=day, seq=seq
            )

        self.write({'file_name': name_report + '.txt', 'file_binary':report})

        return {
        'context': self.env.context,
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'wizard.payment.popular.txt',
        'res_id': self.id,
        'view_id': False,
        'type': 'ir.actions.act_window',
        'target': 'new',
    }
