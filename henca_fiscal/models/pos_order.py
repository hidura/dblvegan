from odoo import fields, models, api
import re
import time


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def get_pos_invoice_create(self, pos_reference):
        order_id = self.search([('pos_reference', '=', pos_reference)])
        timeout = time.time() + 30 * 1  # 30 seg from now

        while not order_id:
            time.sleep(1)
            if time.time() > timeout:
                break
            self._cr.commit()
            order_id = self.search([('pos_reference', '=', pos_reference)])

        while not order_id.account_move:
            time.sleep(1)
            if time.time() > timeout:
                break
            self._cr.commit()
            order_id = self.search([('pos_reference', '=', pos_reference)])

        if order_id.account_move:
            return order_id.account_move.id
        
        return False
         
