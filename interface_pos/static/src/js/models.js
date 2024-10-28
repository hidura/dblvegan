odoo.define('interface_pos.models', function(require) {
    "use strict";
    var rpc = require("web.rpc");
    const Registries = require('point_of_sale.Registries');
    var { PosGlobalState, Order, Payment, models, } = require('point_of_sale.models');

    // -Instancia del Protocol
    //protocol_send
    var psend = window.interfaz_protocol.send_message; // Interfaz_Protocol es una variable global creada por cualquier modulo neotec
   
   

    const PosGlobalStateInherit = (PosGlobalState) => class PosGlobalStateInherit extends PosGlobalState {
        constructor() {
            super(...arguments);
        }

        create_invoice_document (order) {

            console.log(order.pos);
            var ticket = standard_format.FormatFiscalDocument(order, {});
    
            console.log(ticket);
            psend('invoice', ticket);
        }
    
        _save_to_server (orders, options) {
            var self = this;
            var server = super._save_to_server(...arguments);
    
            server.then(function (result){
                let currentOrder = self.get_order();
                if (result.length > 0 && currentOrder){
                    if(result[0].pos_reference == currentOrder.name){
                        let ncf = result[0].l10n_latam_document_number ? result[0].l10n_latam_document_number : '';
                        currentOrder.l10n_do_fiscal_number = ncf || result[0].l10n_do_fiscal_number;
                        currentOrder.l10n_latam_document_type_id = result[0].l10n_latam_document_type_id;
                        currentOrder.l10n_do_origin_ncf = result[0].l10n_do_origin_ncf;
                        currentOrder.l10n_do_ecf_modification_code = result[0].l10n_do_ecf_modification_code;

                        self.create_invoice_document(currentOrder);
                    }
                }
            });
    
            return server;
        }
    
    };

    Registries.Model.extend(PosGlobalState, PosGlobalStateInherit);
});