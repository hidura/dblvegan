# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd. (<http://devintellecs.com>).
#
##############################################################################

from odoo import models, fields, api, _


# from openerp.osv import osv
# from datetime import datetime as dt
# import time
# from openerp.exceptions import Warning
# from datetime import date

class AccountAccount(models.Model):
    _inherit = "account.account"

    account_bool = fields.Boolean(string='Is_Bank')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
