odoo.define("interface_pos.Button", function (require) {
  "use strict";

  const PosComponent = require("point_of_sale.PosComponent");
  const ProductScreen = require("point_of_sale.ProductScreen");
  const { useListener } = require("@web/core/utils/hooks");
  const Registries = require("point_of_sale.Registries");
    // -Instancia del Protocol
    //protocol_send
    var psend = window.interfaz_protocol.send_message; // Interfaz_Protocol es una variable global creada por cualquier modulo neotec

  class PrinterFiscalOptionButton extends PosComponent {
    setup() {
      super.setup();
      useListener("click", this.onClick);
    }
    async onClick() {

    const { confirmed, payload: seletedItem } = await this.showPopup('SelectionPopup', {
        title: this.env._t('Menu Fiscal'),
        list: [
                  { id:1,
                    label: "Cierre Z",
                    item: "cierrez",
                  },
                  { id:2,
                    label: "Cierre X",
                    item: "cierrex",
                  },
                  { id:3,
                    label: "Cancelar Documento",
                    item: "cancel_ticket",
                  },
                ],
    });

    if(confirmed)  psend(seletedItem, {});

    }
  }
  PrinterFiscalOptionButton.template = "PrinterFiscalOption";

  ProductScreen.addControlButton({
    component: PrinterFiscalOptionButton,
    condition: function () {
      return true;
    },
  });

  Registries.Component.add(PrinterFiscalOptionButton);


  class PrinterBillPreOrderFiscal extends PosComponent {
    setup() {
      super.setup();
      useListener("click", this.onClick);
    }
    async onClick() {
        let self = this;
        let order = this.env.pos.get_order();
        if (order.get_orderlines().length == 0) {
            self.showPopup('ErrorPopup',  {
                'title': 'Error: Order Sin Productos',
                'body': 'No se ha agregado productos a la orden, no se puede realiza una precuenta vacia.',
            });

            return false;
        }


        let preorder = standard_format.FormatNoVentaDocument(order, {});
        console.log(preorder);
        psend('nosale', preorder);

        return true;

    }
  }
  PrinterBillPreOrderFiscal.template = "InterfaceBillButton";

  ProductScreen.addControlButton({
    component: PrinterBillPreOrderFiscal,
    condition: function () {
      return true;
    },
  });

  Registries.Component.add(PrinterBillPreOrderFiscal);



  return PrinterFiscalOptionButton;
});
