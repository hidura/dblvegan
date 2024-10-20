odoo.define('henca_fiscal.PaymentScreen', function(require) {
    "use strict";

const PaymentScreen = require('point_of_sale.PaymentScreen');
const Registries = require('point_of_sale.Registries');
var core = require('web.core');
var _t = core._t;


const HencaFiscalPaymentScreen = (PaymentScreen) => {
    class HencaFiscalPaymentScreen extends PaymentScreen {
        constructor() {
            super(...arguments);
            this.env.pos.selectedOrder.l10n_do_ecf_modification_code = "1"
        }

        async _finalizeValidation() {
            await super._finalizeValidation(...arguments);
            this.send_fiscal_invoice()
        }
        async send_fiscal_invoice(error) {
            if (error !== undefined) {
                return;
            }
    
            var self = this.env.pos;
            var self_own = this;
            const order = self.get_order();
            var client = order.get_partner();
    
            await this.env.services.rpc({
                model: 'pos.order',
                method: 'get_pos_invoice_create',
                args: [order.name],
            }, {
                timeout: 30000,
                shadow: true,
            })
            .then(async function(invoice_id) {
                try {
                    if (!invoice_id) {
                        return;
                    }
                    const { name, vat } = client ? client : { name: '', vat: '' }
                    const {
                        taxes_by_id,
                        config: { iface_fiscal_printer_host, iface_fiscal_printer_copy_number, ipf_type }
                    } = self;
                    let fiscal_position = order.fiscal_position || false
                    let apply_law = fiscal_position && fiscal_position.use_for_delivery === true ? false : true
                    let ipf_comments = [
                        `${order.name} - ${order.cashier.name}`,
                    ];
                    const ipf_invoice = {
                        type: self_own.get_fiscal_type(order.l10n_do_fiscal_number, order.l10n_do_origin_ncf ?? false),
                        cashier: self.user.id,
                        subsidiary: self.company.id,
                        ncf: "00000000" + order.l10n_do_fiscal_number,
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
                            },
                        }) => {
                            // Convert quantity to positive in case is a credit note
                            quantity = Math.abs(quantity);
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
                            

                            if (!price_include) {
                                price = price * (amount / 100 + 1);
                            }
    
                            if (discount && discount > 0) {
                                // lots.push("Desc.:" + discount + "%")
                                price = self_own.product_with_discount(price, discount);
                                // let lim = ipf_type && ipf_type == 'bixolon' ? 45 : 40;
                                // display_name = self_own.divide_description_with_discount(lim, display_name, discount)
                            }

                            // if (pack_lot_lines && pack_lot_lines.length > 0) {
                            //     for (const pll of pack_lot_lines) {
                            //         let lot = 'SN: ' + pll.lot_name;
                            //         lots.push(lot);
                            //     }
                            // }
                            // if (order.pricelist.currency_id[0] === otherCurrencyId) {
                            //     price = price / other_curr_rate;
                            // }
                            return {
                                description: display_name,
                                //extra_descriptions: lots,
                                quantity: quantity,
                                price: price,
                                itbis: amount,
                            };
                        }),
                        payments: order.get_paymentlines().map(({
                            name,
                            amount,
                            payment_method: {
                                payment_form
                            }
                        }) => ({
                            type: payment_form === "bank" ? "check" : payment_form || 'cash',
                            amount: Math.abs(amount).toFixed(2),
                            // amount: Math.abs(order.pricelist.currency_id[0] === otherCurrencyId ? amount : amount / other_curr_rate).toFixed(2),
                            description: name
                        })),
                        comments: ipf_comments,
                    }
                    // if (lots.length > 0) {
                    //     ipf_invoice.comments = [...ipf_invoice.comments, lots.join(', ')];
                    // }
                    if (order.l10n_do_origin_ncf) {
                        ipf_invoice.reference_ncf = "00000000" + order.l10n_do_origin_ncf;
                    }
                    //if (ipf_type === 'bixolon') {
                      //  delete ipf_invoice.legal_tip;
                   // }
    
                    if (iface_fiscal_printer_host) {
                        // self_own.change_status_printer_display("connecting");
                        console.log(ipf_invoice);
                        $.ajax({
                            type: 'POST',
                            url: iface_fiscal_printer_host + "/invoice",
                            data: JSON.stringify(ipf_invoice),
                            contentType: "application/json",
                            dataType: "json"
                        }).done(function(response) {
                            console.log(response);
                            // self_own.change_status_printer_display("connected");
    
                            if (response && response['status'] === "success") {
    
                                if (invoice_id) {
                                    self_own.confimeInvoicePrinted(invoice_id, response.response.nif)
                                }
                                for (let i = 0; i < iface_fiscal_printer_copy_number; i++) {
                                    $.ajax({
                                        type: 'GET',
                                        url: iface_fiscal_printer_host + (ipf_type && ipf_type === 'bixolon' ? "/invoice/last" : "/copy"),
                                    }).done(function(response) {
                                        console.log(response);
                                    }).fail(function(response) {
                                        console.log(response);
                                    });
                                }
                            }
                        }).fail((response)=>{
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
                    }
    
    
    
    
    
                } catch (error) {
                    console.log(error);
                }
    
            });
        }
    
        get_fiscal_type(ref, origin_out) {
            console.log("get_fiscal_type", ref, origin_out)
            let fiscal_type = "final"
            let ncf = "02"
            let ncf_origin_out = "02"

            if (ncf) {
                ncf = ref.length === 19 ? ref.substring(9, 11) : ref.substring(1, 3);
            }
            if (origin_out) {
                ncf_origin_out = origin_out.length === 19 ? origin_out.substring(9, 11) : origin_out.substring(1, 3);
            }

            switch (ncf) {
                case "02":
                    fiscal_type = "final";
                    break
    
                case "01":
                    fiscal_type = "fiscal";
                    break
    
                case "15":
                    fiscal_type = "fiscal";
                    break
    
                case "14":
                    fiscal_type = "special";
                    break

                case "04":
                    const fiscalTypeMap = {
                      "01": "fiscal_note",
                      "02": "final_note",
                      "14": "special_note"
                    };
                    fiscal_type = fiscalTypeMap[ncf_origin_out];
                    break
            }
            return fiscal_type;
    
    
        }
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
            let discount_message = "Desc.:" + discount + "%";
            let discount_message_len = discount_message.length;
            let limitWithMessage = lim - discount_message_len;

            if (dlen <= lim) {
                description = description.padEnd(limitWithMessage, " ") + discount_message
            } else if (dlen > lim && dlen <= lim * 2) {
                description = description.padEnd(limitWithMessage, " ") + discount_message
            } else if (dlen > lim * 2 && dlen <= lim * 3) {
                description = description.padEnd(limitWithMessage * 3, " ") + discount_message
            } else if (dlen > lim * 3 && dlen <= lim * 4) {
                description = description.padEnd(limitWithMessage * 4, " ") + discount_message
            } else if (dlen > lim * 4 && dlen <= lim * 5) {
                description = description.padEnd(limitWithMessage * 5, " ") + discount_message
            } else if (dlen > lim * 5 && dlen <= lim * 6) {
                description = description.padEnd(limitWithMessage * 6, " ") + discount_message
            } else if (dlen > lim * 6 && dlen <= lim * 7) {
                description = description.padEnd(limitWithMessage * 7, " ") + discount_message
            } else {
                description = description + discount_message
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
                } else {
                    delete ipf_invoice.legal_tip;
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

        confimeInvoicePrinted(invoice_id, fiscal_nif) {
            this.env.services.rpc({
                model: 'account.move',
                method: 'action_invoice_printed',
                args: [invoice_id, fiscal_nif]
            }).then(() => {
            });
        }
    }

    return HencaFiscalPaymentScreen;
};


Registries.Component.extend(PaymentScreen, HencaFiscalPaymentScreen);
return HencaFiscalPaymentScreen;

});
