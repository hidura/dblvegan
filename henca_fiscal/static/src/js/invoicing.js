/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { useChildRef, useService } from "@web/core/utils/hooks";
import rpc from 'web.rpc';
import framework from 'web.framework';


// const { Component, onWillStart } = owl;
const { useSubEnv, useEffect, useRef, onPatched } = owl;

Date.prototype.yyyymmdd = function() {
    let mm = this.getMonth() + 1; // getMonth() is zero-based
    let dd = this.getDate();

    return [this.getFullYear(),
        (mm > 9 ? '' : '0') + mm,
        (dd > 9 ? '' : '0') + dd
    ].join('-');
};



export class InterfacesFormController extends FormController {

    /**
     * @override
     */

    setup() {
        super.setup();
        this.orm = useService("orm");
    }

    async beforeExecuteActionButton(clickParams) {
        let self = this;
        console.log("Button de Interfaz")
        if(!clickParams.context || !clickParams.context.includes('itf_type')) return super.beforeExecuteActionButton(clickParams);

        try {
            let context = JSON.parse(
                clickParams.context.replace(/'/g, '"').replace(/False/g, 'false').replace(/True/g, 'true')
            );
            const itf_type = context.itf_type;
            const InterfaceData = await self.get_host();

            self.host = InterfaceData.host;


                if (itf_type === "fiscal_print") {

                    // const invoiceData = await this.orm.call(
                    //     "account.move",
                    //     "get_invoice_format",
                    //     [this.props.resId],
                    //     {}
                    // );

                    const invoiceData = await rpc.query({
                        model: 'account.move',
                        method: 'get_invoice_format',
                        args: [this.props.resId],
                    })

                    const {
                        name,
                        cashier,
                        client,
                        items,
                        fiscal_sequence_id,
                        invoice_user_id,
                        seller,
                        ref,
                        partner_id,
                        partner_vat,
                        invoice_line_ids,
                        ipf_host,
                        comment,
                        ipf_type,
                        ipf_print_copy_number,
                        amount_residual,
                        origin_out,
                        invoice_payments_widget,
                        invoice_currency_id,
                        dop_currency_id,
                        other_curr_name,
                        payments,
                        amount_total,
                        amount_total_signed,
                        invoice_date_currency_rate: invoice_other_curr_rate
                    } = invoiceData;

                    const comments_array = [];
                    if (comment.length > 0) {
                        const normalized_comment = comment
                            .normalize("NFD")
                            .replace(/<[^>]*>/g, '')
                            .replace(/[\u0300-\u036f]/g, "")
                            .replace(/['"]+/g, '');

                        const comment_words_array = normalized_comment.split(' ');
                        let comments_array_index = 0;
                        let new_string_line = '';

                        for (let i = 0; i < comment_words_array.length; i++) {
                            if (comments_array[comments_array_index]) {
                                new_string_line = comments_array[comments_array_index] + ' ' + comment_words_array[i];
                                if (new_string_line.length > 40) {
                                    comments_array_index++;
                                    if (comments_array_index === 9) break;
                                    comments_array[comments_array_index] = comment_words_array[i]
                                } else {
                                    comments_array[comments_array_index] = new_string_line;
                                }
                            } else {
                                comments_array[comments_array_index] = comment_words_array[i];
                            }
                        }
                    }

                    const ipf_invoice = {
                        type: this.getFiscalType(ref),
                        cashier: cashier,
                        subsidiary: 1,
                        ncf: `00000000${ref}`,
                        client: client.split("\n")[0],
                        rnc: partner_vat || '',
                        items: items.map(({

                            name,
                            quantity,
                            price_unit,
                            tax_amount,
                            tax_amount_type,
                            price_include,
                            tax_ids,
                            discount,
                            currency_id,
                            invoice_date_currency_rate

                        }) => {
                            if (currency_id && invoice_currency_id !== dop_currency_id) {
                                // console.log("Not peso")
                                price_unit = invoice_date_currency_rate * price_unit;
                            }

                            if (!tax_amount) {
                                tax_amount = 0;
                            }

                            const ipf_line = {
                                description: name
                                    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
                                    .replace(/['"]+/g, '')
                                    .slice(0, 40),
                                quantity: quantity,
                                price: price_unit.toFixed(2),
                                itbis: tax_amount,
                            };

                            if (discount) {
                                ipf_line.discount = discount;
                            }

                            return ipf_line;
                        }),
                        comments: [
                            `${name} - ${seller}`,
                            `${other_curr_name ? `TOTAL ${other_curr_name} ES: ${other_curr_name}$ ${(amount_total).toFixed(2)}` : ''}`,
                            `${other_curr_name ? `TASA ${other_curr_name}: ${(invoice_other_curr_rate).toFixed(2)}` : ''}`,

                            ...comments_array
                        ]
                    }

                    ipf_invoice.payments = invoiceData.payments;
                    // const other_payments = invoice_payments_widget ? JSON.parse(invoice_payments_widget).content: [];
                    // if (other_payments) {
                    //     ipf_invoice.payments = other_payments.map(({
                    //         amount,
                    //         ipf_payment_form,
                    //         ipf_payment_description
                    //     }) => ({
                    //         amount,
                    //         type: ipf_payment_form === 'bank' ? 'check' : ipf_payment_form || 'cash',
                    //         description: ipf_payment_description
                    //     }));
                    // }

                    // if (amount_residual) {
                    //     if (!ipf_invoice.payments) {
                    //         ipf_invoice.payments = [];
                    //     }
                    //     ipf_invoice.payments.push({
                    //         type: 'credit',
                    //         description: 'Credito',
                    //         amount: amount_residual
                    //     });
                    // }
                    //
                    // const items_total = ipf_invoice.items.reduce((total, item) =>
                    //     total + (parseFloat(item.price) * item.quantity), 0);
                    //
                    // const payments_total = ipf_invoice.payments.reduce((total, payment) =>
                    //     total + parseFloat(payment.amount), 0);
                    //
                    // if (items_total !== payments_total) {
                    //     const delta_payment = items_total - payments_total
                    //     const last_payment = ipf_invoice.payments.pop();
                    //     last_payment.amount = (parseFloat(last_payment.amount) + delta_payment).toFixed(2);
                    //     ipf_invoice.payments.push(last_payment);
                    // }

                    if (origin_out) {
                        ipf_invoice.reference_ncf = `00000000${origin_out}`;
                        const origin_prefix = origin_out.slice(0, 3);
                        switch (origin_prefix) {
                            case 'B02':
                                ipf_invoice.type = 'final_note';
                                break;
                            case 'B14':
                                ipf_invoice.type = 'special_note';
                                break;
                            default:
                                ipf_invoice.type = 'fiscal_note';
                        }
                    }

                    if (ipf_print_copy_number === 1 && ipf_type === 'epson') {
                        ipf_invoice.copy = true
                    } else if (ipf_print_copy_number === 2 && ipf_type === 'epson') {
                        ipf_invoice.copy2 = true
                    }
                    console.log(ipf_invoice);
                    if (ipf_host) {
                        $.ajax({
                            type: 'POST',
                            url: ipf_host + "/invoice",
                            data: JSON.stringify(ipf_invoice),
                            contentType: "application/json",
                            dataType: "json"
                        }).done(function(response) {
                            try {
                                if (response && response['status'] === "success") {

                                    self.confimeInvoicePrinted(response.response.nif);
                                }
                            } catch (error) {
                                console.log(error);

                                Swal.fire({
                                    title: 'Error en la impresion fiscal',
                                    text: error,
                                    icon: 'error',
                                    confirmButtonText: 'Aceptar'
                                });
                            }
                            if (ipf_type === 'bixolon') {
                                for (let i = 0; i < ipf_print_copy_number; i++) {
                                    console.log(`Requesting copy number ${i}.`);
                                    $.ajax({
                                        type: 'GET',
                                        url: ipf_host + "invoice/last",
                                    }).done(function(response) {
                                        console.log(response);
                                    }).fail(function(response) {
                                        console.log(response);
                                    });
                                }
                            }
                        }).fail(function(response) {
                            let message = response.responseJSON ? response.responseJSON.message : "No hubo comunicacion con la impresora fiscal"
                            Swal.fire({
                                title: 'Error en la impresion fiscal',
                                text: message,
                                icon: 'error',
                                confirmButtonText: 'Aceptar'
                            });
                        });
                    }
                } else if (itf_type === "fiscal_copy") {
                    const {
                        host: ipf_host,
                        ipf_type,
                    } = InterfaceData;

                    if (ipf_type === 'bixolon') {
                        $.ajax({
                            type: 'GET',
                            url: ipf_host + "/invoice/last",
                        }).done(function(response) {
                            console.log(response);
                        }).fail(function(response) {
                            console.log(response);
                        });
                    }
                } else if (itf_type === "z_close_print") {
                    let host = InterfaceData.host;
                    self.get_host({}).then(function() {
                        if(self.host){
                            host = self.host
                        }
                        self.get_report(host + "/zclose/print", "GET", "z_close_print");


                    });
                } else if (itf_type === "start_jornada_print") {
                    const {
                        host,
                    } = InterfaceData;

                    const ipf_invoice = {
                        type: 'nofiscal',
                        cashier: 1,
                        subsidiary: 1,
                        ncf: `0000000000000001`,
                        client: "",
                        rnc: '',
                        items: [{
                            description: "Inicio de Jornada",
                            quantity: 1.000,
                            price: 1.00,
                            itbis: 0,
                        }],
                        comments: [
                            'Inicio de Jornada'
                        ],
                        payments: [{
                            type: 'cash',
                            description: 'Efectivo',
                            amount: 1.0
                        }]
                    }

                    if (host) {
                        $.ajax({
                            type: 'POST',
                            url: host + "/invoice",
                            data: JSON.stringify(ipf_invoice),
                            contentType: "application/json",
                            dataType: "json"
                        }).done(function(response) { }).fail(function(response) { });
                    }
                } else if (itf_type === "get_state") {
                    const {
                        host
                    } = InterfaceData;
                    self.get_state(host);
                } else if (itf_type === "get_advance_paper") {
                    const {
                        host
                    } = InterfaceData;
                    self.get_advance_paper(host);
                } else if (itf_type === "get_x") {
                    const {
                        host
                    } = InterfaceData;
                    let config_printer = InterfaceData;
                    self.get_x(host, config_printer);
                } else if (itf_type === "get_new_shift_print") {
                    const {
                        host
                    } = InterfaceData;
                    self.get_new_shift_print(host);
                } else if (itf_type === "get_printer_information") {
                    const {
                        host
                    } = InterfaceData;
                    self.get_printer_information(host);
                } else if (itf_type === "get_cut_paper") {
                    const {
                        host
                    } = InterfaceData;
                    self.get_cut_paper(host);
                } else if (itf_type === "get_daily_book") {
                    const {
                        host
                    } = InterfaceData;
                    bootbox.prompt({
                        title: "Extracción de libro diario.",
                        value: new Date(),
                        inputType: "date",
                        size: "small",
                        callback(bookday) {
                            if (!bookday) {
                                return
                            } else {
                                self.get_daily_book({}, bookday);
                            }
                        }
                    });
                } else if (itf_type === "get_information_day") {
                    const {
                        host
                    } = InterfaceData;
                    self.get_information_day(host);
                } else if (itf_type === "get_information_shift") {
                    const {
                        host
                    } = InterfaceData;
                    self.get_information_shift(host);
                } else if (itf_type === "get_serial") {
                    self.get_serial();
                } else if (itf_type === "get_monthlybook") {
                    const {
                        host
                    } = InterfaceData;

                    function generateArrayOfYears() {
                        let max = new Date().getFullYear()
                        let min = max - 20
                        let years = []

                        for (let i = max; i >= min; i--) {
                            years.push({
                                text: i,
                                value: i
                            })
                        }
                        return years
                    }

                    function generateMonths() {
                        moment.locale('es');
                        let months = moment.months();
                        let list_month = []
                        let i = 0

                        months.forEach(m => {
                            list_month.push({
                                text: m,
                                value: i
                            })
                            i++;
                        });

                        return list_month
                    }
                    generateMonths();

                    bootbox.prompt({
                        title: "Generar libro mensual: Año a generar",
                        inputOptions: generateArrayOfYears(),
                        inputType: "select",
                        callback(year) {
                            if (!year) {
                                return
                            } else {
                                bootbox.prompt({
                                    title: "Generar libro mensual: Mes a generar",
                                    inputOptions: generateMonths(),
                                    inputType: "select",
                                    callback(month) {
                                        if (!month) {
                                            return
                                        } else {
                                            self.generate_month_book(year, month);
                                        }
                                    }
                                });
                            }
                        }
                    });
                } else if (itf_type === "get_daily_book_by_date") {
                    const {
                        host
                    } = InterfaceData;

                    let getDaysArray = function(start, end) {
                        start = start.setDate(start.getDate() + 1)
                        end = end.setDate(end.getDate() + 1)
                        let dates = []
                        for (let arr = [], dt = new Date(start); dt <= end; dt.setDate(dt.getDate() + 1)) {
                            dates.push(new Date(dt));
                        }
                        return dates;
                    };

                    bootbox.prompt({
                        title: "Extracción de libro diario por fecha: Fecha Desde",
                        value: new Date(),
                        inputType: "date",
                        size: "small",
                        callback(date_from) {
                            if (!date_from) {
                                return
                            } else {
                                bootbox.prompt({
                                    title: "Extracción de libro diario por fecha: Fecha Hasta",
                                    value: new Date(),
                                    inputType: "date",
                                    size: "small",
                                    callback(date_since) {
                                        if (!date_since) {
                                            return
                                        } else {
                                            console.log('date_from', date_from, 'date_since', date_since)
                                            let array_book_date = getDaysArray(new Date(date_from), new Date(date_since));

                                            if (array_book_date) {
                                                async.eachSeries(array_book_date || [],
                                                    function(day_book, _callback_) {
                                                        let bookday = day_book.yyyymmdd()
                                                        self.get_daily_book_by_range({}, host, bookday,
                                                            function(res) {
                                                                if (res) {
                                                                    _callback_();
                                                                } else {
                                                                    self.showDialog("Extraccion libro mensuales por fecha ", "Error generando libro");
                                                                }
                                                            }
                                                        );
                                                    },
                                                    function() {
                                                        self.showDialog("Extraccion libro mensuales por fecha ", "Se ha tratado de generar todos los libros diarios de la fecha solicitada");
                                                        setTimeout(function() {
                                                            location.reload();
                                                        }, 1000);
                                                    });
                                            }
                                        }
                                    }
                                });
                            }
                        }
                    });
                }
                //this._super(event);





        } catch (error) {
            console.log(error);

            Swal.fire({
                title: 'Error en el servidor',
                text: 'Error, no se pudo realizar esta accion, por favor comunicarse con el administrador.',
                icon: 'error',
                confirmButtonText: 'Aceptar'
            });
        }


        return super.beforeExecuteActionButton(clickParams);
    }


    getFiscalType(ref) {
        let fiscal_type = "final"
        let ncf = ref ? ref.substring(1, 3) : "02";

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
        }
        return fiscal_type;
    }

    tingle_popup (content) {
        let tingle_modal = new tingle.modal({
            footer: true,
            stickyFooter: false,
            closeMethods: ['overlay', 'button', 'escape'],
            closeLabel: "Close",
            cssClass: ['custom-class-1', 'custom-class-2'],
            beforeClose() {
                return true; // close the modal
            }
        });
        tingle_modal.setContent(content);
        tingle_modal.addFooterBtn('Cerrar', 'tingle-btn tingle-btn--primary', function() {
            tingle_modal.close();
        });
        tingle_modal.open();
    }
    confimeInvoicePrinted(fiscal_nif) {

        this.orm.call(
            "account.move",
            "action_invoice_printed",
            [this.props.resId, fiscal_nif],
            {}
        ).then(async () => {
            // this.reload();
            await this.props.record.model.root.load()
        });
    }

    async get_host(context) {
        let self = this;
        this.host = null;
        return await this.orm.call(
            "ipf.printer.config",
            "get_ipf_host",
            ['', false],
            {}
        )
    }

    async get_software_version(context) {
        let self = this;
        let {host} = await self.get_host(context);
        let url = host + "/software_version";
        return self.get_report(url, "GET", "get_software_version");
    }

    get_state(host) {
        let self = this;
        let url = host + "/state";
        return self.get_report(url, "GET", "get_state");
    }

    async get_printer_information(context) {
        let self = this;
        let {host} = await self.get_host(context);
        let url = host + "/printer_information";
        return self.get_report(url, "GET", "get_printer_information", context, null);
    }

    async get_advance_paper(context) {
        let self = this;
        let {host} = await self.get_host(context);
        let url = host + "/advance_paper";
        return self.get_report(url, "GET", "get_advance_paper");
    }

    async get_advance_paper_number(context, number) {
        let self = this;
        let {host} = await self.get_host(context);
        let url = host + "/advance_paper/" + number;
        return self.get_report(url, "GET", "post_advance_paper_number");
    }

    async get_cut_paper(context) {
        let self = this;
        let {host} = await self.get_host(context);
        let url = host + "/cut_paper";
        return self.get_report(url, "GET", "get_cut_paper");
    }

    async get_z_close(context) {
        let self = this;
        let {host} = await self.get_host(context);
        let url = host + "/zclose";
        return self.get_report(url, "GET", "get_z_close");
    }

    async get_z_close_print(context) {
        let self = this;
        let {host} = await self.get_host(context);
        let url = host + "/zclose/print";
        return self.get_report(url, "GET", "get_z_close_print");
    }

    async get_new_shift(context) {
        let self = this;
        let {host} = await self.get_host(context);
        let url = host + "/new_shift";
        return self.get_report(url, "GET", "get_new_shift");
    }

    async get_new_shift_print(context) {
        let self = this;
        let {host} = await self.get_host(context);
        let url = host + "/new_shift/print";
        return self.get_report(url, "GET", "get_new_shift_print");
    }

    async get_x(context, printer_info) {
        let self = this;
        let {host} = await self.get_host(context);
        let url = host + "/X";

        if (printer_info && printer_info.ipf_type && printer_info.ipf_type === "bixolon") {
            url = host + "/x";
        }
        return self.get_report(url, "GET", "get_x");
    }

    async get_information_day(context) {
        let self = this;
        let {host} = await self.get_host(context);
        let url = host + "/information/day";
        return self.get_report(url, "GET", "get_information_day");
    }

    async get_information_shift(context) {
        let self = this;
        let {host} = await self.get_host(context);
        let url = host + "/information/shift";
        return self.get_report(url, "GET", "get_information_shift");
    }

    async get_document_header(context) {
        let self = this;
        let {host} = await self.get_host(context);
        let url = host + "/document_header";
        return self.get_report(url, "GET", "get_document_header");
    }

    async post_document_header(context, data) {
        let self = this;
        let {host} = await self.get_host(context);
        let url = host + "/document_header";
        return self.get_report(url, "POST", "post_document_header", context, data);
    }

    async get_daily_book(context, bookday) {
        let self = this;
        let {host} = await self.get_host(context);
        $.ajax({
            "type": "GET",
            "url": host + "/printer_information"
        }).done(function(response) {
            let aplitBookDay = bookday.split("-");
            let serial = "noserial";
            let url = host + "/daily_book/" + "norequerido" + "/" + aplitBookDay[2] + "/" + aplitBookDay[1] + "/" + aplitBookDay[0];

            self.get_book(url, serial, bookday, context);
        }).fail(function(response) {
            let res = false;
            if (response.responseText) {
                console.log(response);
                // let res = JSON.parse(response.responseText);
            }

            if (res) {
                self.showDialog(res.message)
            } else if (response.statusText === "error") {
                self.showDialog("Error de conexion", "El sistema no pudo conectarse a la impresora verifique las conexiones.")
            }
        });
    }

    async get_daily_book_by_range(context, host, bookday, _callback) {
        let self = this;

        $.ajax({
            "type": "GET",
            "url": host + "/printer_information"
        }).done(function(response) {
            let aplitBookDay = bookday.split("-");
            let serial = "noserial";
            let url = host + "/daily_book/" + "norequerido" + "/" + aplitBookDay[2] + "/" + aplitBookDay[1] + "/" + aplitBookDay[0];
            let self = this;
            framework.blockUI();
            $.ajax({
                url: url,
                type: "GET",
                contentType: "text/plain"
            }).done(function(response) {
                console.log(response);
                let self = this;
                if (response) {

                    rpc.query({
                        model: 'ipf.printer.config',
                        method: 'save_book',
                        args: [response, serial, bookday]
                    }).then(function(data) {
                        if (data) {
                            _callback(true)
                        }
                    }).then(function() {
                        framework.unblockUI()
                    });
                } else {
                    framework.unblockUI();
                    _callback(true)
                }
            }).fail(function(response) {
                framework.unblockUI();
            });

        }).fail(function(response) {
            _callback(false)
        });
    }

    async get_serial() {
        let self = this;
        let {host} = await self.get_host();
        $.ajax({
            "type": "GET",
            "url": host + "/printer_information"
        }).done(function(response) {
            let serial = JSON.parse(response).response.serial;
            if (serial) {
                rpc.query({
                    model: 'ipf.printer.config',
                    method: 'save_serial_printer',
                    args: [serial]
                }).then(function(data) {
                    if (data) {
                        // self.reload();
                        location.reload();
                    }
                });
            }
        });
    }

    post_invoice(context) {
        let self = this;
        return self.create_invoice(context);
    }

    get_report(url, type, from, context, data) {
        framework.blockUI();
        let self = this;
        let params = {
            type,
            url
        }
        if (data) {
            params.data = JSON.stringify(data)
        }

        return $.ajax(params)
            .done(function(response) {
                try {
                    if (response) {
                        if (/^[\],:{}\s]*$/.test(response.replace(/\\["\\\/bfnrtu]/g, '@').replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, ']').replace(/(?:^|:|,)(?:\s*\[)+/g, ''))) {
                            console.log(JSON.parse(response));
                            self.show_response(from, JSON.parse(response), context);
                        } else {
                            self.show_response(from, response, context);
                        }
                    }
                } catch (exception) {
                }
                framework.unblockUI();
            })
            .fail(function(response) {
                framework.unblockUI();
                let res = false;
                if (response.responseText) {
                    console.log(response);
                    try {
                       res = JSON.parse(response.responseText);
                    } catch (e) {
                        console.log('ERROR', e);
                        console.log(response.responseText);
                    }
                }
                if (res.message === "Fiscal journey not open, try printing at least one invoice." && res) {
                    self.showDialog("Cierre Z", "No hay cierre Z abierto, intente hacer al menos una factura.")
                } else {
                    self.showDialog("Error de conexion", "El sistema no pudo conectarse a la impresora verifique las conexiones.")
                }
            });
    }

    show_response(from, response, context) {
        let self = this;
        if (from === "get_software_version") {
            self.showDialog("Infomación del software", "<strong>Nombre:</strong> " + response.response.name + "</br> <strong>Version:</strong> " + response.response.version)
        } else if (from === "get_state") {
            let stateTable = "";
            stateTable += "<table class=\"tg table table-hover table-striped\">";
            stateTable += "  <tr>";
            stateTable += "    <th class=\"tg-47zg\">Estatus Fiscal<\/th>";
            stateTable += "    <th class=\"tg-031e\"><\/th>";
            stateTable += "  <\/tr>";
            stateTable += "  <tr>";
            stateTable += "    <td class=\"tg-031e\">Document<\/td>";
            stateTable += "    <td class=\"tg-031e\">" + response.response.fiscal_status.document + "<\/td>";
            stateTable += "  <\/tr>";
            stateTable += "  <tr>";
            stateTable += "    <td class=\"tg-031e\">Memory<\/td>";
            stateTable += "    <td class=\"tg-031e\">" + response.response.fiscal_status.memory + "<\/td>";
            stateTable += "  <\/tr>";
            stateTable += "  <tr>";
            stateTable += "    <td class=\"tg-031e\">Mode<\/td>";
            stateTable += "    <td class=\"tg-031e\">" + response.response.fiscal_status.mode + "<\/td>";
            stateTable += "  <\/tr>";
            stateTable += "  <tr>";
            stateTable += "    <td class=\"tg-031e\">SubState<\/td>";
            stateTable += "    <td class=\"tg-031e\">" + response.response.fiscal_status.substate + "<\/td>";
            stateTable += "  <\/tr>";
            stateTable += "  <tr>";
            stateTable += "    <td class=\"tg-031e\">TechMode<\/td>";
            stateTable += "    <td class=\"tg-031e\">" + response.response.fiscal_status.techmode + "<\/td>";
            stateTable += "  <\/tr>";
            stateTable += "  <tr>";
            stateTable += "    <td class=\"tg-031e\">Open<\/td>";
            stateTable += "    <td class=\"tg-031e\">" + response.response.fiscal_status.open + "<\/td>";
            stateTable += "  <\/tr>";
            stateTable += "  <tr>";
            stateTable += "    <td class=\"tg-qjik\"><strong>Estatus del printer<\/strong><\/td>";
            stateTable += "    <td class=\"tg-031e\"><\/td>";
            stateTable += "  <\/tr>";
            stateTable += "  <tr>";
            stateTable += "    <td class=\"tg-031e\">Cover<\/td>";
            stateTable += "    <td class=\"tg-031e\">" + response.response.printer_status.cover + "<\/td>";
            stateTable += "  <\/tr>";
            stateTable += "  <tr>";
            stateTable += "    <td class=\"tg-031e\">Errors<\/td>";
            stateTable += "    <td class=\"tg-031e\">" + response.response.printer_status.errors + "<\/td>";
            stateTable += "  <\/tr>";
            stateTable += "  <tr>";
            stateTable += "    <td class=\"tg-031e\">MoneyBox<\/td>";
            stateTable += "    <td class=\"tg-031e\">" + response.response.printer_status.moneybox + "<\/td>";
            stateTable += "  <\/tr>";
            stateTable += "  <tr>";
            stateTable += "    <td class=\"tg-031e\">Printer<\/td>";
            stateTable += "    <td class=\"tg-031e\">" + response.response.printer_status.printer + "<\/td>";
            stateTable += "  <\/tr>";
            stateTable += "  <tr>";
            stateTable += "    <td class=\"tg-031e\">State<\/td>";
            stateTable += "    <td class=\"tg-031e\">" + response.response.printer_status.state + "<\/td>";
            stateTable += "  <\/tr>";
            stateTable += "<\/table>";
            self.showDialog("Estado de la impresora", stateTable)
        } else if (from === "get_printer_information") {
            self.tingle_popup(
                "<strong>ID:</strong> " + response.response.id + "</br> <strong>Serial:</strong> " + response.response.serial
            );
        } else if (from === "get_advance_paper") {

        } else if (from === "post_advance_paper_number") {

        } else if (from === "get_cut_paper") {

        } else if (from === "get_z_close") {
            self.tingle_popup("El cierre Z #<strong>" + response.response.znumber + "</strong> se realizo satisfactoriamente");
        } else if (from === "get_z_close_print") {} else if (from === "get_new_shift") {

        } else if (from === "get_new_shift_print") {

        } else if (from === "get_x") {

        } else if (from === "get_information_day") {

            let tableInformation = "";
            tableInformation += "<table class=\"tg table table-hover table-striped\">";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Fecha de inicio<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.init_date + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Hora de inicio<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.init_time + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Número del último cierre Z<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.last_znumber + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Cantidad de documentos de venta<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.invoices + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Cantidad de documentos no fiscales o precuentas<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.documents + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Cantidad de documentos cancelados<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.cancelled + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">NIF inicial<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.first_nif + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">NIF final<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.last_nif + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total de facturas para consumidor final<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de facturas para consumidor final<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final_itbis + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total de facturas fiscales<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de facturas fiscales<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal_itbis + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total notas de crédito para consumidor final<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final_note + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de notas de crédito para consumidor final<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final_note_itbis + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total nota de crédito con crédito fiscal<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal_note + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de nota de crédito con crédito fiscal<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal_note_itbis + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total pagado<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_paid + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "<\/table>";
            self.showDialog("Información de día.", tableInformation)
        } else if (from === "get_information_shift") {
            let tableInformation = "";
            tableInformation += "<table class=\"tg table table-hover table-striped\">";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Fecha de inicio<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.init_date + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Hora de inicio<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.init_time + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Número del último cierre Z<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.last_znumber + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Cantidad de documentos de venta<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.invoices + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Cantidad de documentos no fiscales o precuentas<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.documents + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Cantidad de documentos cancelados<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.cancelled + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">NIF inicial<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.first_nif + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">NIF final<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.last_nif + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total de facturas para consumidor final<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de facturas para consumidor final<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final_itbis + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total de facturas fiscales<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de facturas fiscales<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal_itbis + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total notas de crédito para consumidor final<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final_note + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de notas de crédito para consumidor final<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_final_note_itbis + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total nota de crédito con crédito fiscal<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal_note + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total de ITBIS de nota de crédito con crédito fiscal<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_fiscal_note_itbis + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "  <tr>";
            tableInformation += "    <td class=\"tg-031e\">Total pagado<\/td>";
            tableInformation += "    <td class=\"tg-031e\">" + response.response.total_paid + "<\/td>";
            tableInformation += "  <\/tr>";
            tableInformation += "<\/table>";
            self.showDialog("Información del turno.", tableInformation)
        }
        if (from === "get_document_header") {
            self.showDialog("Infomación de cabezera", "<h3>" + response.response.text + "</h3>")
        } else if (from === "pos_document_header") {

        } else if (from === "get_daily_book") {
            self.save_book(response, context)
        }
    }

    showDialog(title, message) {
        this.tingle_popup(message);
    }

    get_book(url, serial, bookday, context) {
        let self = this;
        framework.blockUI();
        $.ajax({
            url: url,
            type: "GET",
            contentType: "text/plain"
        }).done(function(response) {
            console.log(response);
            self.save_book(response, serial, bookday, context);
        }).fail(function(response) {
            framework.unblockUI();
            console.log(response);
            let res = false;
            if (response.responseText) {
                console.log(response);
                res = JSON.parse(response.responseText);
            }
            if (res) {
                self.showDialog(res.message)
            } else if (response.statusText === "error") {
                self.showDialog("Error de conexion", "El sistema no pudo conectarse a la impresora verifique las conexiones.")
            }

        });
    }

    save_book(response, serial, bookday, context) {
        let self = this;
        if (response) {
            rpc.query({
                model: 'ipf.printer.config',
                method: 'save_book',
                args: [response, serial, bookday]
            }).then(function(data) {
                if (data) {
                    self.showDialog("Extracción libro diario", "El libro de diario fue generado satisfactoriamente.");
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                }
            }).then(function() {
                framework.unblockUI()
            });
        } else {
            framework.unblockUI();
            self.showDialog("Extraccion libro diario", "No hay datos disponibles para esta fecha.");
        }
    }

    generate_month_book(year, month) {
        let self = this;
        if (year && month !== undefined) {
            rpc.query({
                model: 'ipf.printer.config',
                method: 'generate_month_book',
                args: [year, month]
            }).then(function(data) {
                if (data) {
                    self.showDialog("Extracción libro mensual", "El libro de mensual fue generado satisfactoriamente.");
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                }
            }).then(function() {
                framework.unblockUI()
            });
        } else {
            framework.unblockUI();
            self.showDialog("Extraccion libro diario", "No hay datos disponibles para esta fecha.");
        }
    }

    create_invoice(context) {
        let self = this;
        return new openerp.web.Model("ipf.printer.config").call("ipf_print", [], {
                context: context
            })
            .then(function(data) {
                return self.print_receipt(data, context)
            });
    }

    print_receipt(data, context) {
        let self = this;
        return $.ajax({
                type: 'POST',
                url: data.host + "/invoice",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json"
            })
            .done(function(response) {
                console.log(response);
                let responseobj = response;
                self.nif = responseobj.response.nif;
                self.print_done(context, data.invoice_id, responseobj.response.nif);
            })
            .fail(function(response) {
                if (response.responseText) {
                    let message = JSON.parse(response.responseText);
                    self.showDialog(message.status, message.message);
                } else if (response.statusText === "error") {
                    self.showDialog("Error de conexion", "El sistema no pudo conectarse a la impresora verifique las conexiones.")
                }
            });
    }

    print_done(context, invoice_id, nif) {
        let self = this;
        console.log("print_done");
        return new openerp.web.Model("ipf.printer.config").call("print_done", [
                [invoice_id, nif]
            ], {
                context: context
            })
            .then(function(response) {
                return response;
            })
    }



}
InterfacesFormController.props = {
    ...FormController.props,
}

export const InterfacesForm = {
    ...formView,
    Controller: InterfacesFormController,
}

registry.category("views").add('interface_wizard', InterfacesForm);