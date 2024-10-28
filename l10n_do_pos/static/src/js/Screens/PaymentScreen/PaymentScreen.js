odoo.define('l10n_do_pos.PaymentScreen', function(require) {
'use strict';

const PaymentScreen = require('point_of_sale.PaymentScreen');
const Registries = require('point_of_sale.Registries');
const NumberBuffer = require('point_of_sale.NumberBuffer');
const { isConnectionError } = require('point_of_sale.utils');
const { useListener } = require("@web/core/utils/hooks");

const PosRestrictInvoice = PaymentScreen => class extends PaymentScreen {
    constructor() {
        super(...arguments);
        this.env.pos.selectedOrder.l10n_do_ecf_modification_code = "1"
    }
    setup() {
        useListener('validate-credit-note', () => this.validateCreditNote({ detail: {}}));
        super.setup();
    }
    async codeUpdated(ev) {
        var modification_code = ev.detail.modification_code
        if (modification_code){
            this.env.pos.selectedOrder.l10n_do_ecf_modification_code = modification_code;
        }
    }

    async _finalizeValidation() {
        let partner = this.currentOrder.get_partner()
        if ((this.env.pos.config.default_partner_id[0] !== partner.id) && !partner.vat && partner.l10n_do_dgii_tax_payer_type !== 'non_payer') {
            this.showPopup('ErrorPopup', {
                title: this.env._t('Validación RNC'),
                body: this.env._t(
                    'El cliente no tiene RNC definido, modifique el contacto o cambie a Cliente de Consumo'
                ),
            });
            return;
        }

        if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
            this.env.proxy.printer.open_cashbox();
        }

        this.currentOrder.initialize_validation_date();
        this.currentOrder.finalized = true;

        let syncOrderResult, hasError;

        try {
            // 1. Save order to server.
            syncOrderResult = await this.env.pos.push_single_order(this.currentOrder);

            // 2. Invoice. ####### AQUI ESTA EL CAMBIO
            if (this.currentOrder.is_to_invoice() && this.env.pos.config.print_pdf) {
                if (syncOrderResult.length) {
                    await this.env.legacyActionManager.do_action('account.account_invoices', {
                        additional_context: {
                            active_ids: [syncOrderResult[0].account_move],
                        },
                    });
                } else {
                    throw { code: 401, message: 'Backend Invoice', data: { order: this.currentOrder } };
                }
            }

            // 3. Post process.
            if (syncOrderResult.length && this.currentOrder.wait_for_push_order()) {
                const postPushResult = await this._postPushOrderResolve(
                    this.currentOrder,
                    syncOrderResult.map((res) => res.id)
                );
                if (!postPushResult) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error: no internet connection.'),
                        body: this.env._t('Some, if not all, post-processing after syncing order failed.'),
                    });
                }
            }
        } catch (error) {
            if (error.code == 700 || error.code == 701)
                this.error = true;

            if ('code' in error) {
                // We started putting `code` in the rejected object for invoicing error.
                // We can continue with that convention such that when the error has `code`,
                // then it is an error when invoicing. Besides, _handlePushOrderError was
                // introduce to handle invoicing error logic.
                await this._handlePushOrderError(error);
            } else {
                // We don't block for connection error. But we rethrow for any other errors.
                if (isConnectionError(error)) {
                    this.showPopup('OfflineErrorPopup', {
                        title: this.env._t('Connection Error'),
                        body: this.env._t('Order is not synced. Check your internet connection'),
                    });
                } else {
                    throw error;
                }
            }
        } finally {
            // Always show the next screen regardless of error since pos has to
            // continue working even offline.
            this.showScreen(this.nextScreen);
            // Remove the order from the local storage so that when we refresh the page, the order
            // won't be there
            this.env.pos.db.remove_unpaid_order(this.currentOrder);

            // Ask the user to sync the remaining unsynced orders.
            if (!hasError && syncOrderResult && this.env.pos.db.get_orders().length) {
                const { confirmed } = await this.showPopup('ConfirmPopup', {
                    title: this.env._t('Remaining unsynced orders'),
                    body: this.env._t(
                        'There are unsynced orders. Do you want to sync these orders?'
                    ),
                });
                if (confirmed) {
                    // NOTE: Not yet sure if this should be awaited or not.
                    // If awaited, some operations like changing screen
                    // might not work.
                    this.env.pos.push_orders();
                }
            }
        }
    }

//    async _finalizeValidation() {
//        let partner = this.currentOrder.get_partner()
//        if ((this.env.pos.config.default_partner_id[0] != partner.id) && !partner.vat && partner.l10n_do_dgii_tax_payer_type != 'non_payer') {
//            this.showPopup('ErrorPopup', {
//                title: this.env._t('Validación RNC'),
//                body: this.env._t(
//                    'El cliente no tiene RNC definido, modifique el contacto o cambie a Cliente de Consumo'
//                ),
//            });
//            return;
//        }
//        super._finalizeValidation();
//    }

    async validateCreditNote({ detail: paymentMethod }) {
        if (!paymentMethod) {
            return;
        }

        let paymentMethodCreditNote = false;
        for (var pm in this.payment_methods_from_config) {
            if (this.env.pos.payment_methods[pm].type === 'credit_note') {
                paymentMethodCreditNote = this.env.pos.payment_methods[pm];
                break;
            }
        }
        const { confirmed, payload: l10n_do_fiscal_number } = await this.showPopup('TextInputPopup', {
            title: 'Introduzca NCF de Nota de Crédito',
            placeholder: 'B0401234567',
            startingValue: '',
        });

        if (confirmed && l10n_do_fiscal_number !== '') {
            let order = this.currentOrder;
            let partner = this.currentOrder.get_partner()
            if (!partner){
                partner = {
                    id: this.env.pos.config.l10n_do_default_partner_id[0]
                }
            }

            const line = this.paymentLines.find((line) => line.note === l10n_do_fiscal_number);
            const result = await this.env.services.rpc({
                model: 'pos.order',
                method: 'credit_note_info_from_ui',
                args: [l10n_do_fiscal_number, partner.id, order.get_total_with_tax()],
            });

            if (result.msg !== '' || line) {
                this.showPopup('ErrorPopup', {
                    title: 'Nota de Crédito',
                    body: result.msg || "Esta Nota de Crédito ya esta aplicada a la Orden",
                });
                return;
            }

            let newPaymentline = this.currentOrder.add_paymentline(paymentMethodCreditNote);
            if (newPaymentline){
                newPaymentline.set_amount(parseFloat(result.residual) || 0);
                // newPaymentline.set_credit_note_id(result.id)
                // newPaymentline.set_note(l10n_do_fiscal_number)
                NumberBuffer.reset();
                return true;
            }
        }
    }
};

Registries.Component.extend(PaymentScreen, PosRestrictInvoice);
return PaymentScreen;

});
