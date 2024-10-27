/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { useChildRef, useService } from "@web/core/utils/hooks";
import rpc from "web.rpc";
import framework from "web.framework";

//protocol_send
var psend = window.interfaz_protocol.send_message; // Interfaz_Protocol es una variable global creada por cualquier modulo neotec
//que implemente algun protocolo;

export class InterfacesNeotecFormController extends FormController {
  /**
   * @override
   */

  setup() {
    super.setup();
    this.orm = useService("orm");
    rpc
      .query(
        {
          model: "account.move",
          method: "get_account_invoice_interface_config",
          args: [0],
        },
        {}
      )
      .then(function (pconf) {
        console.log(pconf);
        standard_format.setConfigInterface(pconf);
      });
  }

  async beforeExecuteActionButton(clickParams) {
    var self = this;
    if (!clickParams.context)
      return super.beforeExecuteActionButton(clickParams);

    try {
      let context = JSON.parse(clickParams.context);
      const itf_type = context.itf_type;
      debugger;
      if (itf_type === "invoice") {
        // Imprimir Factura
        this.sendInvoice(this.model.root.data.id, false);
      } else if (itf_type === "reinvoice") {
        // ReImprimir Factura
        this.sendInvoice(this.model.root.data.id, true);
      }
    } catch (error) {
      console.log(error);
    }

    return super.beforeExecuteActionButton(clickParams);
  }

  sendInvoice(invoice_id, permit_reprint = false) {
    self = this;
    rpc
      .query(
        {
          model: "account.move",
          method: "get_invoice_format",
          args: [invoice_id],
        },
        {}
      )
      .then(function (invoice) {
        let print =
          permit_reprint == false
            ? invoice.do_print && invoice.printed == false
            : invoice.do_print;

        if (print) {
          var ticket = standard_format.FormatFiscalDocumentFromInvoice(
            invoice,
            {
              seller: true,
              cashier: true,
            }
          );
          psend("invoice", ticket);
          console.log(ticket);
          self.confimeInvoiceSent(invoice_id);
        }
      });
  }
  async reload() {
    await this.model.root.load();
    this.model.notify();
  }
  confimeInvoiceSent(invoice_id) {
    let self = this;
    rpc
      .query({
        model: "account.move",
        method: "action_invoice_sent",
        args: [invoice_id],
      })
      .then(() => {
        self.reload();
      });
  }
}
InterfacesNeotecFormController.props = {
  ...FormController.props,
};

export const InterfacesForm = {
  ...formView,
  Controller: InterfacesNeotecFormController,
};

registry.category("views").add("fiscal_interface_wizard", InterfacesForm);
