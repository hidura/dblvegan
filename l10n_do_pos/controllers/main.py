# © 2018 Eneldo Serrata <eneldo@marcos.do>
# © 2018 Kevin Jiménez <kevinjimenezlorenzo@gmail.com>
# © 2018 Jorge Hernández <jhernandez@gruponeotec.com>
# © 2018 Francisco Peñaló <frankpenalo24@gmail.com >
# © 2023 Yasmany Castillo <yasmany@codec.do >

import json
import re
import requests
import logging

from odoo import http
from odoo.http import request
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import rnc, cedula
except (ImportError, IOError) as err:
    _logger.debug(str(err))


class Odoojs(http.Controller):

    @http.route('/dgii_ws', auth='public', cors="*")
    def index(self, **kwargs):
        term = kwargs.get("term", False)
        if not term:
            return json.dumps([])
        try:
            if term.isdigit() and len(term) in [9, 11]:
                result = rnc.check_dgii(term)
            else:
                result = rnc.search_dgii(term, end_at=20, start_at=1)

            if result is not None:
                if not isinstance(result, list):
                    result = [result]

                for d in result:
                    d['exists'] = bool(request.env['res.partner'].search([('vat', '=', d["rnc"])]))
                    d.update(request.env['res.partner']._format_l10n_do_dgii_payer_type(
                        d["rnc"], d["name"], request.env.ref("base.do").id))
                    d["name"] = " ".join(
                        re.split(r"\s+", d["name"], flags=re.UNICODE)
                    )  # remove all duplicate white space from the name
                    d["label"] = "{} - {}".format(d["rnc"], d["name"])

                # To prevent error in POS sent query to allow fill input name
                if not result:
                    result.append({
                        'exists': False,
                        'label': term,
                        'name': term,
                        'rnc': False,
                        'l10n_do_dgii_tax_payer_type': 'non_payer',
                    })
                return json.dumps(result)
        except requests.exceptions.ConnectionError:
            _logger.error("Rnc Search Error by %s", str(term), exc_info=True)
        _logger.info("Respuesta para pos final: %r" % term)
        return json.dumps([])

