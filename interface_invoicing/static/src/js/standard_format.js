
standard_format = (function () {
    var iconfig = {
        printer_type: "custom",
        use_legal_tip: false,
        note_invoice: false,
        print_cashier: false,
        print_seller: false,
        print_product_barcode:false,

    }; //Interface Config-- la configuracion de la interfaz que se le asigno. 
    var taxes_by_id;
    var lim = 40;

    var setConfigInterface = function (config) {
        iconfig = config;
        switch (iconfig.printer_type) {
            case "bixolon":
                lim = 45;
                break;

            case "epson":
            case "custom":
            case "star":
                lim = iconfig.mode_restaurant == true ? 40 : 21;
                break;

            default:
                lim = 40;
        }
    };

    var setTaxes_by_Id = function (taxes) {
        taxes_by_id = taxes;

    };

    var typeInvoices = function (type) {
        var invoice_type;

        switch (type) {
            case 'final':
                invoice_type = 1
                break;

            case 'fiscal':
                invoice_type = 2
                break;

            case 'gov':
                invoice_type = 2
                break;

            case 'special':
                invoice_type = 6
                break;

            case 'fiscal_note':
                invoice_type = 4
                break;

            case 'final_note':
                invoice_type = 3
                break;

            case 'special_note':
                invoice_type = 8
                break;

            case 'nofiscal':
                invoice_type = 9
                break;
                

            default:
                invoice_type = 1
                break;
        }

        return invoice_type;

    };

    var typeCreditNotes = function (type) {
        //este se usa porque cambio la forma de obtener el tipo de la order, simplemente se obtiene por el cliente
        //---Fix Me-- en ningulado se especifica el tipo si es nota de credito, por eso cuando sea nota de creditto, se cambia el tipo
        var credit_note_type;

        switch (type) {

            case 'final':
                credit_note_type = 3
                break;

            case 'fiscal':
                credit_note_type = 4
                break;

            case 'gov':
                credit_note_type = 4
                break;

            case 'special':
                credit_note_type = 8
                break;

            case 'fiscal_note':
                invoice_type = 4
                break;

            case 'final_note':
                invoice_type = 3
                break;

            case 'special_note':
                invoice_type = 8
                break;

            default:
                credit_note_type = 3
                break;
        }

        return credit_note_type;

    };

    var typePayments = function (type) {

        var payment_type;

        switch (type) {

            case 'cash':
                payment_type = 1
                break;

            case 'bank':
                payment_type = 2
                break;

            case 'card':
                payment_type = 3
                break;

            case 'credit_card':
                payment_type = 3
                break;

            case 'debit_card':
                payment_type = 4
                break;

            case 'bond':
                payment_type = 6
                break;

            case 'others':
                payment_type = 7
                break;

            case 'credit':
                payment_type = 7
                break;

            case 'credit_note':
                payment_type = 11
                break;


            default:
                payment_type = 1
                break;
        }

        return payment_type;

    }

    var typeTax = function (type) {
        // return  the tax_type like that the fiscal printers use.

        var tax_type;
        switch (type) {

            case 18:
                tax_type = '1800'
                break;

            case 0:
                tax_type = iconfig.printer_type != "epson" ? '10000' : '00'
                break;

            case 11:
                tax_type = '1100'
                break;

            case 16:
                tax_type = '1600'
                break;

            case 10:
                tax_type = iconfig.printer_type != "epson" ? '10000' : '00'
                break;


            case 8:
                tax_type = '0800'
                break;

            case 5:
                tax_type = '0500'
                break;


            default:
                tax_type = '1800'
                break;
        }

        return tax_type;

    }

    var typeTaxSymbol = function (type) {
        // return the symbol of the tax
        var tax_symbol;

        switch (type) {

            case 18:
                tax_symbol = 'I2'
                break;

            case 0:
                tax_symbol = 'E'
                break;

            case 11:
                tax_symbol = 'I4'
                break;

            case 13:
                tax_symbol = 'I5'
                break;

            case 8:
                tax_symbol = 'I3'
                break;


            case 16:
                tax_symbol = 'I1'
                break;

            case 10:
                tax_symbol = 'E'
                break;


            default:
                tax_symbol = 'I2'
                break;
        }

        return tax_symbol;

    }

    var typeTaxSymbolBixolon = function (type) {
        // return the symbol of the tax
        var tax_symbol;

        switch (type) {

            case "1800":
                tax_symbol = 'B'
                break;

            case "10000":
                tax_symbol = 'E'
                break;

            case "1100":
                tax_symbol = 'I4'
                break;

            case "1300":
                tax_symbol = 'I5'
                break;

            case "0800":
                tax_symbol = 'I3'
                break;

            case "10000":
                tax_symbol = 'E'
                break;


            default:
                tax_symbol = 'B'
                break;
        }

        return tax_symbol;

    }

    var ProductoWithDiscount = function (price, discount_porcent) {

        var total_discount = (price) * (discount_porcent / 100)
        var total = price - total_discount;
        return total;

    }


    var Payments = function (pay_type, mount) {
        this.pay_type = pay_type || 1,
            this.mount = mount || '',
            this.extra_description1 = '',
            this.extra_description2 = '',
            this.extra_description3 = ''
    };

    var Items = function (type, quantity, description, price, tax, extra_description) {
        this.type = type || '';
        this.quantity = quantity || '';
        this.item_description = description || 'Productos Varios';
        this.extra_description = extra_description || [];
        this.unit_price = price || '';
        this.tax = tax || '';
    };

    var Header = function (type, ncf, business_name, rnc, ref_ncf, comments, enable_ley) { // TODO  Header of invoices
        this.type_invoice = type || 1;
        this.quantity_of_copies = 0;
        this.enable_10_percent_law = enable_ley || 0;
        this.logo = ''
        this.density = '';
        this.ncf = ncf || '';
        this.branch = '001';
        this.box = '001';
        this.business_name = business_name || '';
        this.rnc = rnc || '';
        this.ref_ncf = ref_ncf || '';
        this.comments = comments || '';
    };

    var Ticket = function (_Header, _Items, _Payments) {

        this.Header = _Header,
            this.Items = _Items,
            this.Payments = _Payments
    }

    var PadBoth = function (source, length) {

        var spaces = length - source.length;
        var padLeft = spaces / 2 + source.length;

        return source.padEnd(padLeft).padStart(length);
    }


    var CheckIfApplyLaw = (order) => {
        var apply;
        let fiscal_position = order.fiscal_position || false

        if (iconfig.use_legal_tip && !fiscal_position) {

            apply = true

        } else if (iconfig.use_legal_tip && fiscal_position) {

            apply = order.fiscal_position.use_for_delivery == false ? true : false

        } else {

            apply = false

        }

        return apply
    }



    var DivideDescriptionWithDiscount = function (limite, description, discount) {
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


    var ValidateItem = (item) => {
        let vitem = {}, //validated item
        barcode = "",
        default_code = "";

        vitem.type = '1';
        vitem.quantity = iconfig.printer_type != "star" ? Math.abs(item.quantity).toFixed(3) : Math.abs(item.quantity).toFixed(2);
        vitem.description = item.product ? item.product.display_name : item.description;
        vitem.extra_description = item.extra_description || []
        vitem.price = item.price.toFixed(2);
        vitem.tax = item.product ? typeTax(taxes_by_id[item.product.taxes_id[0]].amount) : typeTax(item.itbis) //el producto solamente viene con el id del impuesto,
        //el porcentaje debemos obtenerlo del diccionario de impuesto.

        if (iconfig.print_product_barcode && iconfig.print_product_barcode == true) {
            barcode = item.barcode ? item.barcode + " " : "";
        }

        if (iconfig.print_product_reference && iconfig.print_product_reference == true) {
            default_code = item.default_code ? item.default_code + " " : "";
        }

        vitem.description = barcode + default_code + vitem.description;

        if (item.discount > 0) {
            vitem.price = ProductoWithDiscount(item.price, item.discount).toFixed(2);

            vitem.description = DivideDescriptionWithDiscount(lim, vitem.description, item.discount);
        }



        return vitem;


    }


    var ValidateAndCreateDocument = function (order, options) {
        var doc = {} //Document
        var client = order.get_client();
        doc.type = order.is_return_order ? typeCreditNotes(client.sale_fiscal_type) : typeInvoices(client.sale_fiscal_type);
        doc.ncf = order.ncf;
        doc.rnc = client.vat || '';
        doc.business_name = client.name || '';
        doc.ref_ncf = order.ref_ncf || ''
        doc.comments = ""
        doc.enable_10_percent_law = CheckIfApplyLaw(order) ? 1 : 0;
        doc.list_items = [];
        doc.list_payments = [];

        order.get_orderlines().forEach(function (element) {
            doc.list_items.push(ValidateItem(element)) //Validamos el producto, para anadir impuesto y calcular descuento
        }, this);

        if (!order.is_return_order) {

            order.get_paymentlines().forEach(function (element) {
                var payment = {}
                payment.pay_type = typePayments(element.cashregister.journal.payment_form);
                payment.mount = element.amount.toFixed(2);
                doc.list_payments.push(payment);

            }, this);
        }

        return doc
    }

    var ValidateAndCreateDocumentFromInvoice = function (invoice, options) {
        var doc = {} //Document
        doc.type = typeInvoices(invoice.type);
        doc.ncf = invoice.ncf;
        doc.rnc = invoice.rnc ? invoice.rnc : '';
        doc.business_name = invoice.client || '';
        doc.ref_ncf = invoice.ref_ncf || ''
        doc.discount = invoice.total_discount || 0.0
        doc.comments = ""
        doc.enable_10_percent_law = iconfig.use_legal_tip ? 1 : 0; //  CheckIfApplyLaw(invoice) ? 1 : 0;
        doc.list_items = [];
        doc.list_payments = [];



        if (iconfig.print_seller && iconfig.print_seller == true) {
            let mesg = `VENDEDOR/A: ${invoice.seller}`;
            doc.comments += mesg.padEnd(40, " ")
        }

        if (iconfig.print_cashier && iconfig.print_cashier == true) {
            let mesg = `CAJERO/A: ${invoice.cashier}`;
            doc.comments += mesg.padEnd(40, " ")
        }


        if (iconfig.note_invoice) {
            doc.comments += iconfig.note_invoice
        }



        invoice.items.forEach(function (element) {
            doc.list_items.push(ValidateItem(element)) //Validamos el producto, para anadir impuesto y calcular descuento
        }, this);

        invoice.payments.forEach(function (element) {
            var payment = {}
            payment.pay_type = typePayments(element.type);
            payment.mount = element.amount.toFixed(2);
            doc.list_payments.push(payment);

        }, this);


        return doc
    }

    var FormatFiscalDocument = function (order, options) {
        //Este metodo convierte la order en formato para ser impresora para la impresora fiscales.

        var doc = ValidateAndCreateDocument(order, options)
        var list_items = [];
        var list_payments = [];
        var header = new Header(doc.type, doc.ncf, doc.business_name, doc.rnc, doc.ref_ncf, doc.comments, doc.enable_10_percent_law);

        doc.list_items.forEach(function (e) {
            list_items.push(new Items(e.type, e.quantity, e.description, e.price, e.tax, e.extra_description));
        }, this);
        doc.list_payments.forEach(function (element) {
            list_payments.push(new Payments(element.pay_type, element.mount));
        }, this);


        //Para la interfaz, las facturas o notas de creditos, son ticket
        return new Ticket(header, list_items, list_payments);

    }

    var FormatFiscalDocumentFromInvoice = function (invoice, options) {
        //Este metodo convierte la order en formato para ser impresora para la impresora fiscales.

        var doc = ValidateAndCreateDocumentFromInvoice(invoice, options)
        var list_items = [];
        var list_payments = [];
        var header = new Header(doc.type, doc.ncf, doc.business_name, doc.rnc, doc.ref_ncf, doc.comments, doc.enable_10_percent_law);

        doc.list_items.forEach(function (e) {
            list_items.push(new Items(e.type, e.quantity, e.description, e.price, e.tax, e.extra_description));
        }, this);
        doc.list_payments.forEach(function (element) {
            list_payments.push(new Payments(element.pay_type, element.mount));
        }, this);


        //Para la interfaz, las facturas o notas de creditos, son ticket
        return new Ticket(header, list_items, list_payments);

    }
    var GetAdditionalInfo = function (order) {

        let total = order.get_total_with_tax()
        let taxes = order.get_total_tax()
        let total_without_tax = order.get_total_without_tax()
        let ley_tax = iconfig.use_legal_tip ? (total_without_tax * 0.10) : 0.00;

        if (iconfig.use_legal_tip) {
            taxes = taxes > 0.00 ? taxes - ley_tax : 0.00;
        }


        var info = {

            name: order.pos.company.name,
            email: order.pos.company.email != 'info@yourcompany.com' ? order.pos.company.email : false,
            website: order.pos.company.website != 'http://www.yourcompany.com' ? order.pos.company.website : false,
            phone: order.pos.company.phone,
            cashier: order.pos.cashier || false,
            number_order: order.sequence_number,
            number_table: order.pos.table || false,
            customer_count: order.pos.customer_count || false,
            subtotal_order: total_without_tax.toFixed(2).toString(),
            itbis_order: taxes.toFixed(2).toString(),
            ley_order: ley_tax,
            total_order: total.toFixed(2).toString(),
        };

        return info

    }

    var FormatNoVentaDocument = function (order, options) {
        //Este metodo convierte la order en formato para ser impresora para la impresora fiscales.
        let preorder = []
        let doc = ValidateAndCreateDocument(order, options);
        let info = GetAdditionalInfo(order);
        let pv, lpv; //Pad Value/ Line Pad Value

        switch (iconfig.printer_type) {

            case 'epson':
                pv = 40;
                lpv = 39;
                break;

            case 'custom':
                pv = 40;
                lpv = 39;
                break;

            case 'bixolon':
                pv = 65;
                lpv = 45;
                break;

            default:
                pv = 40;
                lpv = 45;
        }

        preorder.push(PadBoth(info.name.toUpperCase(), pv));
        if (info.email) {
            preorder.push(PadBoth(info.email.toUpperCase(), pv));
        }
        if (info.website) {
            preorder.push(PadBoth(info.website.toUpperCase(), pv));
        }
        if (info.phone) {
            preorder.push(PadBoth(info.phone.toUpperCase(), pv));
        }
        preorder.push("________________________________________________________________");
        preorder.push(PadBoth("***PRE-CUENTA***", pv));
        preorder.push("");
        preorder.push("");

        if (info.cashier) {
            preorder.push(" SERVIDO POR: " + info.cashier.name.toUpperCase());
        }
        if (info.customer_count) {
            preorder.push(" CLIENTES " + info.customer_count.toString().toUpperCase());
        }
        if (info.number_table) {
            preorder.push(" MESA: " + info.number_table.name.toString().toUpperCase());
        }
        preorder.push("================================================================");
        preorder.push(" DESCRIPCION                                              VALOR");
        preorder.push("================================================================");

        doc.list_items.forEach(e => {
            preorder.push(" " + parseFloat(e.quantity).toFixed(2) + " X " + parseFloat(e.price).toFixed(2));

            if (e.description.length >= lpv) {

                preorder.push(" " + e.description.substr(0, lpv));
                preorder.push(" " + e.description.substr(lpv, e.description.length));
            } else {
                preorder.push(" " + e.description);
            }

            if (iconfig.printer_type == "bixolon") {
                preorder.push((parseFloat(e.price) * parseFloat(e.quantity)).toFixed(2).padStart(61, " ") + " " + typeTaxSymbolBixolon(e.tax));
            }
        });

        preorder.push("================================================================");
        preorder.push(" SUBTOTAL" + info.subtotal_order.padStart(pv - 10, " "));
        preorder.push(" TOTAL ITBIS" + info.itbis_order.padStart(pv - 13, " "));
        if (info.ley_order > 0.00) {
            preorder.push(" % LEY" + info.ley_order.toFixed(2).toString().padStart(pv - 7, " "));
        }

        // if (iconfig.printer_type == "bixolon") {
            preorder.push("$TOTAL" + info.total_order.padStart(pv - 55, " "));
        // }
        preorder.push("");
        preorder.push(" NUMERO DE ORDER: " + info.number_order);

        return preorder;

    }


    var exports = {
        setConfigInterface: setConfigInterface,
        setTaxes_by_Id: setTaxes_by_Id,
        FormatFiscalDocument: FormatFiscalDocument,
        FormatNoVentaDocument: FormatNoVentaDocument,
        FormatFiscalDocumentFromInvoice: FormatFiscalDocumentFromInvoice

    };

    return exports;

})();