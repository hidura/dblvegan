from odoo import models, fields


class PosConfig(models.Model):
    _inherit = "pos.config"

    iface_fiscal_printer = fields.Many2one(
        comodel_name="ipf.printer.config", string="Impresora fiscal"
    )
    iface_fiscal_printer_host = fields.Char(
        string="IP Impresora Fiscal Interface",
        related="iface_fiscal_printer.host",
        readonly=True,
    )
    iface_fiscal_printer_copy_number = fields.Integer(
        string="Numero de Copias Interface Fiscal",
        related="iface_fiscal_printer.print_copy_number",
        readonly=True,
    )
    iface_fiscal_print_order_bill = fields.Boolean(string="Imprimir cuenta IPF")
    ipf_type = fields.Selection(
        string="IPF de la impresora",
        related="iface_fiscal_printer.ipf_type",
        readonly=True,
    )


class PosSession(models.Model):
    _inherit = "pos.session"

    def z_close_print(self):
        pass


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    use_for_delivery = fields.Boolean(
        string="Usar para LLevar/Delivery",
        help="Activar si desea que esta posicion fiscal,hace que no se \
        aplique el 10% de la propinal legal.",
    )
