odoo.define('interface_pos.screens', function(require) {
    "use strict";

    const Chrome = require('point_of_sale.Chrome');
    const Registries = require('point_of_sale.Registries');


    var rpc = require('web.rpc');
    var is_fiscal_pos = true;

    // -Configuracion de  la Interfaz

    var iconfig = NaN;


    //-Notas:
    /*
    Modulos Interfaz Pos:

    Dependencia
    La comunicacion con la impresora, es por medio de una extension/app, que se comunica con la neoexpress.
    */

    //--------------------------------------------------------------------------------------------------------



    const PosInterfazChrome = (Chrome) =>
        class extends Chrome {
            async start() {

                await super.start();
          
                try {
                    //Id de los impuesto que se estan utilizando en el Pos
    
    
                    standard_format.setTaxes_by_Id(this.env.pos.taxes_by_id)
                        // Obtenemos la configuracion de la Interfaz
                    var config_interface = this.env.pos.config.config_interface_id
                } catch (error) {

                    console.log(error);
                }
    
                if (config_interface) { // llama a este comando para obtener la configuracion de la interfaz configurada, y asi podemos
                    //conectarnos al servidor configurado.
    
                    rpc.query({
                            model: 'config.interface',
                            method: 'get_config',
                            args: [config_interface[0]]
                        }, {})
                        .then(function(pconf) {
                            iconfig = pconf;
                            standard_format.setConfigInterface(pconf);
                            if (pconf.mode_restaurant == false) {
                                $('.interface-order-printbill').hide();
                            }
    
                        });
    
    
    
    
                } else {
                    is_fiscal_pos = false;
                    // if not config, doesnt show the printer options
                    $('.interface-order-printbill').hide();
                    $('.interface_menu_fiscal').hide();
    
                }


            }
        };

    Registries.Component.extend(Chrome, PosInterfazChrome);

   





    //Boton que muestar el menu fiscal de la  impresora

    // var PrinterFiscalOptionButton = screens.ActionButtonWidget.extend({
    //     template: 'PrinterFiscalOption',
    //     button_click: function() {
    //         this.gui.show_popup("selection", {
    //             title: "Menu Fiscal",
    //             list: [{
    //                     label: 'Cierre Z',
    //                     item: "cierrez"
    //                 },
    //                 {
    //                     label: 'Cierre X',
    //                     item: "cierrex"
    //                 },
    //                 {
    //                     label: 'Cancelar Documento',
    //                     item: "cancel_ticket"
    //                 },
    //             ],
    //             confirm: function(item) {
    //                 psend(item, {});

    //             }
    //         });
    //     }
    // });


    // screens.define_action_button({
    //     'name': 'menu_fiscal',
    //     'widget': PrinterFiscalOptionButton,
    //     'condition': function() {
    //         return true;
    //     },
    // });



    // var InterfacecBillButton = screens.ActionButtonWidget.extend({
    //     template: 'InterfaceBillButton',
    //     button_click: function() {
    //         let self = this;
    //         let order = this.pos.get_order()

    //         if (order.get_orderlines().length == 0) {
    //             self.gui.show_popup('error', {
    //                 'title': 'Error: Order Sin Productos',
    //                 'body': 'No se ha agregado productos a la orden, no se puede realiza una precuenta vacia.',
    //                 'cancel': function() {
    //                     self.gui.show_screen('products');
    //                 }
    //             });

    //             return false;
    //         }


    //         let preorder = standard_format.FormatNoVentaDocument(order, {});
    //         psend('nosale', preorder);

    //         return true;

    //     }
    // });

    // screens.define_action_button({
    //     'name': 'interface_print_bill',
    //     'widget': InterfacecBillButton,
    //     'condition': function() {
    //         return true
    //     },
    // });

    return Chrome;
});