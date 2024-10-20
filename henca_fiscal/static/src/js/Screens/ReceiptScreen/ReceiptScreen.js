odoo.define('henca_fiscal.ReceiptScreen', function(require) {
    "use strict";

const ReceiptScreen = require('point_of_sale.ReceiptScreen');
const Registries = require('point_of_sale.Registries');
var core = require('web.core');
var _t = core._t;
var rpc = require('web.rpc');



const HencaFiscalReceiptScreen = (ReceiptScreen) => {
    class HencaFiscalReceiptScreen extends ReceiptScreen {
        change_status_printer_display(status, pedding=false) {
            let status_printer = {
                state: status,
                pending: pedding
            }
            this.env.pos.trigger("change:synch_printer", status_printer);
        }
        divide_description_with_discount(limite, description, discount) {
            let lim = limite;
            let dlen = description.length;
            if (dlen <= lim) {
                description = description.padEnd(lim, " ") + "Descuento Aplicado : " + discount + "%"
            } else if (dlen > lim && dlen <= lim * 2) {
                description = description.padEnd(lim, " ") + "Descuento Aplicado : " + discount + "%"
            } else if (dlen > lim * 2 && dlen <= lim * 3) {
                description = description.padEnd(lim * 3, " ") + "Descuento Aplicado : " + discount + "%"
            } else if (dlen > lim * 3 && dlen <= lim * 4) {
                description = description.padEnd(lim * 4, " ") + "Descuento Aplicado : " + discount + "%"
            } else if (dlen > lim * 4 && dlen <= lim * 5) {
                description = description.padEnd(lim * 5, " ") + "Descuento Aplicado : " + discount + "%"
            } else if (dlen > lim * 5 && dlen <= lim * 6) {
                description = description.padEnd(lim * 6, " ") + "Descuento Aplicado : " + discount + "%"
            } else if (dlen > lim * 6 && dlen <= lim * 7) {
                description = description.padEnd(lim * 7, " ") + "Descuento Aplicado : " + discount + "%"
            } else {
                description = description + " Descuento Aplicado : " + discount + "%"
            }
            return description;
        }
    
        product_with_discount(price, discount_porcent) {
            var total_discount = (price) * (discount_porcent / 100)
            var total = price - total_discount;
            return total;
        }
    
        print_order_bill(order) {
            if (!order) { return; }
    
            var self = this.env.pos;
            var self_own = this;
            var client = self.get_order().get_partner();
    
            try {
                const {
                    name,
                    vat
                } = client ? client : {
                    name: '',
                    vat: ''
                }
                const {
                    taxes_by_id,
                    config: {
                        iface_fiscal_printer_host,
                        iface_fiscal_printer_copy_number,
                        ipf_type
                    }
                } = self;
                console.log('IPF TYPE', ipf_type)
    
                let fiscal_position = order.fiscal_position || false
                let apply_law = fiscal_position && fiscal_position.use_for_delivery == true ? false : true
    
                const ipf_invoice = {
                    type: 'nofiscal',
                    cashier: self.user.id,
                    copy: iface_fiscal_printer_copy_number && iface_fiscal_printer_copy_number > 0 ? true : false,
                    subsidiary: self.company.id,
                    ncf: 'Documento de no venta',
                    reference_ncf: '',
                    client: name,
                    rnc: vat || '',
                    legal_tip: apply_law,
                    items: order.get_orderlines().map(({
                        quantity,
                        price,
                        discount,
                        product: {
                            display_name,
                            taxes_id
                        }
                    }) => {
                        // Calculate price based on tax computation type and assign
                        // percentage for itbis
                        const tax_id = taxes_id && taxes_id[0];
                        const tax = taxes_by_id && taxes_by_id[tax_id];
    
                        if (tax) {
                            var {
                                amount,
                                price_include
                            } = tax;
                        } else {
                            var amount = 0;
                            var price_include = false;
                        }
    
                        if (discount && discount > 0) {
                            price = self_own.product_with_discount(price, discount);
                            let lim = ipf_type && ipf_type == 'bixolon' ? 45 : 40;
                            display_name = self_own.divide_description_with_discount(lim, display_name, discount)
                        }
    
                        return {
                            description: display_name,
                            extra_description: "",
                            quantity: quantity,
                            price: parseFloat(price.toFixed(2)),
                            itbis: amount,
                            charges: 0,
                            discount: 0,
                        };
                    }),
                    payments: [],
                    comments: [
                        `${order.name}`,
                        `${order.table ? (order.table.floor.name + ' - Mesa ' + order.table.name): null}`,
                    ],
                    discounts: [],
                    charges: [],
                    invoice_id: 0,
                    host: iface_fiscal_printer_host,
                }
                if (ipf_type === 'epson') {
                    ipf_invoice.type = 'document';
                    delete ipf_invoice.invoice_id;
                    delete ipf_invoice.reference_ncf;
                    delete ipf_invoice.discounts;
                    delete ipf_invoice.charges;
                    delete ipf_invoice.host;
                }
                console.log(ipf_invoice);
                console.log(JSON.stringify(ipf_invoice));
                if (iface_fiscal_printer_host) {
                    // self_own.change_status_printer_display("connecting");
                    $.ajax({
                        type: 'POST',
                        url: iface_fiscal_printer_host + "/invoice",
                        data: JSON.stringify(ipf_invoice),
                        contentType: "application/json",
                        dataType: "json"
                    }).done(function(response) {
                        console.log(response);
                        // self_own.change_status_printer_display("connected");
                    }).fail(function(response) {
                        // self_own.change_status_printer_display("disconnected");
                        console.log(response);
                        let message = response.responseJSON ? response.responseJSON.message : "No hubo comunicacion con la impresora fiscal"
                        Swal.fire({
                            title: 'Error en la impresion fiscal',
                            text: message,
                            icon: 'error',
                            confirmButtonText: 'Aceptar'
                        });
                    });
                    if (ipf_type === 'epson') {
                        for (let i = 0; i < iface_fiscal_printer_copy_number; i++) {
                            $.ajax({
                                type: 'GET',
                                url: iface_fiscal_printer_host + "/copy",
                            }).done(function(response) {
                                console.log(response);
                            }).fail(function(response) {
                                console.log(response);
                            });
                        }
                    } else {
                        for (let i = 0; i < iface_fiscal_printer_copy_number; i++) {
                            $.ajax({
                                type: 'GET',
                                url: iface_fiscal_printer_host + "/last",
                            }).done(function(response) {
                                console.log(response);
                            }).fail(function(response) {
                                console.log(response);
                            });
                        }
                    }
                }
            } catch (error) {
                console.log(error);
            }
        }
    
        renderElement() {
            var self = this;
            this._super();
            this.$('.ipf-print-bill').click(function () {
                if (self.env.pos.config.iface_fiscal_print_order_bill) {
                    self.print_order_bill(self.env.pos.get_order());
                }
            });
        }
    }

    return HencaFiscalReceiptScreen;
};

// const HencaFiscalReceiptScreen = ReceiptScreen =>{ 
//     class HencaFiscalReceiptScreen extends ReceiptScreen {

//         change_status_printer_display(status, pedding=false) {
//             let status_printer = {
//                 state: status,
//                 pending: pedding
//             }
//             this.env.pos.trigger("change:synch_printer", status_printer);
//         }

//     divide_description_with_discount(limite, description, discount) {
//         let lim = limite;
//         let dlen = description.length;
//         if (dlen <= lim) {
//             description = description.padEnd(lim, " ") + "Descuento Aplicado : " + discount + "%"
//         } else if (dlen > lim && dlen <= lim * 2) {
//             description = description.padEnd(lim, " ") + "Descuento Aplicado : " + discount + "%"
//         } else if (dlen > lim * 2 && dlen <= lim * 3) {
//             description = description.padEnd(lim * 3, " ") + "Descuento Aplicado : " + discount + "%"
//         } else if (dlen > lim * 3 && dlen <= lim * 4) {
//             description = description.padEnd(lim * 4, " ") + "Descuento Aplicado : " + discount + "%"
//         } else if (dlen > lim * 4 && dlen <= lim * 5) {
//             description = description.padEnd(lim * 5, " ") + "Descuento Aplicado : " + discount + "%"
//         } else if (dlen > lim * 5 && dlen <= lim * 6) {
//             description = description.padEnd(lim * 6, " ") + "Descuento Aplicado : " + discount + "%"
//         } else if (dlen > lim * 6 && dlen <= lim * 7) {
//             description = description.padEnd(lim * 7, " ") + "Descuento Aplicado : " + discount + "%"
//         } else {
//             description = description + " Descuento Aplicado : " + discount + "%"
//         }
//         return description;
//     }

//     product_with_discount: function(price, discount_porcent) {
//         var total_discount = (price) * (discount_porcent / 100)
//         var total = price - total_discount;
//         return total;
//     }

//     print_order_bill(order) {
//         if (!order) { return; }

//         var self = this.env.pos;
//         var self_own = this;
//         var client = self.get_order().get_partner();

//         try {
//             const {
//                 name,
//                 vat
//             } = client ? client : {
//                 name: '',
//                 vat: ''
//             }
//             const {
//                 taxes_by_id,
//                 config: {
//                     iface_fiscal_printer_host,
//                     iface_fiscal_printer_copy_number,
//                     ipf_type
//                 }
//             } = self;
//             console.log('IPF TYPE', ipf_type)

//             let fiscal_position = order.fiscal_position || false
//             let apply_law = fiscal_position && fiscal_position.use_for_delivery == true ? false : true

//             const ipf_invoice = {
//                 type: 'nofiscal',
//                 cashier: self.user.id,
//                 copy: iface_fiscal_printer_copy_number && iface_fiscal_printer_copy_number > 0 ? true : false,
//                 subsidiary: self.company.id,
//                 ncf: 'Documento de no venta',
//                 reference_ncf: '',
//                 client: name,
//                 rnc: vat || '',
//                 legal_tip: apply_law,
//                 items: order.get_orderlines().map(({
//                     quantity,
//                     price,
//                     discount,
//                     product: {
//                         display_name,
//                         taxes_id
//                     }
//                 }) => {
//                     // Calculate price based on tax computation type and assign
//                     // percentage for itbis
//                     const tax_id = taxes_id && taxes_id[0];
//                     const tax = taxes_by_id && taxes_by_id[tax_id];

//                     if (tax) {
//                         var {
//                             amount,
//                             price_include
//                         } = tax;
//                     } else {
//                         var amount = 0;
//                         var price_include = false;
//                     }

//                     if (discount && discount > 0) {
//                         price = self_own.product_with_discount(price, discount);
//                         let lim = ipf_type && ipf_type == 'bixolon' ? 45 : 40;
//                         display_name = self_own.divide_description_with_discount(lim, display_name, discount)
//                     }

//                     return {
//                         description: display_name,
//                         extra_description: "",
//                         quantity: quantity,
//                         price: parseFloat(price.toFixed(2)),
//                         itbis: amount,
//                         charges: 0,
//                         discount: 0,
//                     };
//                 }),
//                 payments: [],
//                 comments: [
//                     `${order.name}`,
//                     `${order.table ? (order.table.floor.name + ' - Mesa ' + order.table.name): null}`,
//                 ],
//                 discounts: [],
//                 charges: [],
//                 invoice_id: 0,
//                 host: iface_fiscal_printer_host,
//             }
//             if (ipf_type === 'epson') {
//                 ipf_invoice.type = 'document';
//                 delete ipf_invoice.invoice_id;
//                 delete ipf_invoice.reference_ncf;
//                 delete ipf_invoice.discounts;
//                 delete ipf_invoice.charges;
//                 delete ipf_invoice.host;
//             }
//             console.log(ipf_invoice);
//             console.log(JSON.stringify(ipf_invoice));
//             if (iface_fiscal_printer_host) {
//                 self_own.change_status_printer_display("connecting");
//                 $.ajax({
//                     type: 'POST',
//                     url: iface_fiscal_printer_host + "/invoice",
//                     data: JSON.stringify(ipf_invoice),
//                     contentType: "application/json",
//                     dataType: "json"
//                 }).done(function(response) {
//                     console.log(response);
//                     self_own.change_status_printer_display("connected");
//                 }).fail(function(response) {
//                     self_own.change_status_printer_display("disconnected");
//                     console.log(response);
//                     let message = response.responseJSON ? response.responseJSON.message : "No hubo comunicacion con la impresora fiscal"
//                     Swal.fire({
//                         title: 'Error en la impresion fiscal',
//                         text: message,
//                         icon: 'error',
//                         confirmButtonText: 'Aceptar'
//                     });
//                 });
//                 if (ipf_type === 'epson') {
//                     for (let i = 0; i < iface_fiscal_printer_copy_number; i++) {
//                         $.ajax({
//                             type: 'GET',
//                             url: iface_fiscal_printer_host + "/copy",
//                         }).done(function(response) {
//                             console.log(response);
//                         }).fail(function(response) {
//                             console.log(response);
//                         });
//                     }
//                 } else {
//                     for (let i = 0; i < iface_fiscal_printer_copy_number; i++) {
//                         $.ajax({
//                             type: 'GET',
//                             url: iface_fiscal_printer_host + "/last",
//                         }).done(function(response) {
//                             console.log(response);
//                         }).fail(function(response) {
//                             console.log(response);
//                         });
//                     }
//                 }
//             }
//         } catch (error) {
//             console.log(error);
//         }
//     }

//     renderElement: function() {
//         var self = this;
//         this._super();
//         this.$('.ipf-print-bill').click(function () {
//             if (self.env.pos.config.iface_fiscal_print_order_bill) {
//                 self.print_order_bill(self.env.pos.get_order());
//             }
//         });
//     }
// };
// };

Registries.Component.extend(ReceiptScreen, HencaFiscalReceiptScreen);
return HencaFiscalReceiptScreen;

});
