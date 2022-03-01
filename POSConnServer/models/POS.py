import json
from odoo import api, fields, models
import requests

class POSORDER(models.Model):
    _inherit = "pos.order"
    @api.model
    def action_add_move_from_pos(self, args):

        # Move Line creation:
        order_info =self.env['pos.order'].search([('id','=',args[0]['order_id'])])
        account_move=order_info.action_pos_order_invoice()
        picking_move = order_info.create_picking()

        return account_move

class POSCONFIG(models.Model):
    _inherit = "pos.config"
    default_partner_id = fields.Integer('default_partner_id')


class account_move(models.Model):
    _inherit = "account.move"
    fiscal_status=fields.Char("Fiscal Status")
    need_certification=fields.Boolean("Need Certification")
    