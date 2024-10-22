odoo.define("l10n_do_pos.models", function (require) {
    "use strict";

var rpc = require("web.rpc");
const Registries = require('point_of_sale.Registries');
var { PosGlobalState, Order, Payment, models, } = require('point_of_sale.models');


const PosGlobalStateInherit = (PosGlobalState) => class PosGlobalStateInherit extends PosGlobalState {
    constructor() {
        super(...arguments);
        this.payer_types_selection = {
            'taxpayer': 'Contribuyente',
            'non_payer': 'Cliente de Consumo',
            'nonprofit': 'Sin fines de lucro',
            'special': 'Exento',
            'governmental': 'Gubernamental',
            'foreigner': 'Extranjero',
        }
    }

    _save_to_server (orders, options) {
        var self = this;
        var server = super._save_to_server(...arguments);

        server.then(function (result){
            let currentOrder = self.get_order();
            if (result.length > 0 && currentOrder){
                if(result[0].pos_reference === currentOrder.name){
                    let ncf = result[0].l10n_latam_document_number ? result[0].l10n_latam_document_number : '';
                    currentOrder.l10n_do_fiscal_number = ncf || result[0].l10n_do_fiscal_number;
                    currentOrder.l10n_do_ncf_expiration_date = result[0].l10n_do_ncf_expiration_date;
                    currentOrder.l10n_latam_document_type_id = result[0].l10n_latam_document_type_id;
                    currentOrder.l10n_do_origin_ncf = result[0].l10n_do_origin_ncf;
                    currentOrder.l10n_do_ecf_modification_code = result[0].l10n_do_ecf_modification_code;
                }
            }
        });

        return server;
    }

};
Registries.Model.extend(PosGlobalState, PosGlobalStateInherit);

const OrderInherit = (Order) => class OrderInherit extends Order {
    constructor() {
        super(...arguments);
        this.to_invoice = true;
        if (this.pos.config.only_invoice && !this.get_partner())
            this.to_invoice = true;

        if (!this.get_partner()) {
            let pos_default_partner = this.pos.config.default_partner_id;

            if (pos_default_partner) {
                let client = this.pos.db.get_partner_by_id(pos_default_partner[0]);
                if (client) {
                    this.set_partner(client);
                }
            }
        }
        this.save_to_db();
    }
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.l10n_do_fiscal_number = json.l10n_do_fiscal_number;
        this.l10n_do_ncf_expiration_date = json.l10n_do_ncf_expiration_date;
        this.l10n_latam_document_type_id = json.l10n_latam_document_type_id;
        this.to_invoice = json.to_invoice;
        this.l10n_do_origin_ncf = json.l10n_do_origin_ncf;
        this.l10n_do_is_return_order = json.l10n_do_is_return_order;
        this.l10n_do_return_order_id = json.l10n_do_return_order_id;
    }
    export_as_JSON() {
        var json = super.export_as_JSON(...arguments);
        json.l10n_do_fiscal_number = this.l10n_do_fiscal_number;
        json.l10n_do_ncf_expiration_date = this.l10n_do_ncf_expiration_date;
        json.l10n_latam_document_type_id = this.l10n_latam_document_type_id;
        json.to_invoice = this.to_invoice;
        json.l10n_do_ecf_modification_code = this.l10n_do_ecf_modification_code;
        json.l10n_do_origin_ncf = this.l10n_do_origin_ncf;
        json.l10n_do_is_return_order = this.l10n_do_is_return_order;
        json.l10n_do_return_order_id = this.l10n_do_return_order_id;
        return json;
    }
    export_for_printing() {
        var self = this;
        var result = super.export_for_printing(...arguments);
        result.company.company_address = self.pos.company.company_address;
        result.l10n_do_ncf_expiration_date = self.l10n_do_ncf_expiration_date;
        result.company.l10n_do_ecf_issuer = self.pos.company.l10n_do_ecf_issuer;
        result.l10n_do_fiscal_number = self.l10n_do_fiscal_number;
        result.l10n_latam_document_type_id = self.l10n_latam_document_type_id;
        result.to_invoice = self.to_invoice;
        result.l10n_do_origin_ncf = self.l10n_do_origin_ncf;
        result.l10n_do_is_return_order = self.l10n_do_is_return_order;
        result.l10n_do_return_order_id = self.l10n_do_return_order_id;
        return result;
    }
}
Registries.Model.extend(Order, OrderInherit);

const PaymentCreditNote = (Payment) => class PaymentCreditNote extends Payment {
    constructor() {
        super(...arguments);
        // this.credit_note_id = '';
        // this.note = '';
    }
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        // this.credit_note_id = json.credit_note_id;
        // this.note = json.note;
    }
    // set_credit_note_id(credit_note_id){
    //     if(this.credit_note_id !== credit_note_id){
    //         this.credit_note_id = credit_note_id;
    //     }
    // }

    // get_credit_note_id(){
    //     return this.credit_note_id;
    // }

    // set_note(note){
    //     if(this.note !== note){
    //         this.note = note;
    //     }
    // }

    // get_note(){
    //     return this.note;
    // }
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        // json.credit_note_id = this.credit_note_id;
        // json.note = this.note;
        return json;
    }
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        // result.credit_note_id = this.credit_note_id;
        // result.note = this.note;
        return result;
    }
};
Registries.Model.extend(Payment, PaymentCreditNote);
});
