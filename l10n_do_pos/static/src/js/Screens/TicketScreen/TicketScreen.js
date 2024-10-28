odoo.define('l10n_cu_pos.TicketScreen', function(require) {
    'use strict';

    const TicketScreen = require('point_of_sale.TicketScreen');
    const Registries = require('point_of_sale.Registries');

    const TicketScreenInherit = TicketScreen => class extends TicketScreen {
            _getSearchFields() {
                var result = super._getSearchFields(...arguments);
                result.RECEIPT_NUMBER.modelField = 'display_name'
                return result;
            }

            async _onDoRefund() {
                // Este metodo es llamado al dar clik en Refund
                const order = this.getSelectedSyncedOrder();
                const partner = order.get_partner();
                const destinationOrder =
                    this.props.destinationOrder && partner === this.props.destinationOrder.get_partner()
                        ? this.props.destinationOrder
                        : this._getEmptyOrder(partner);

                let result = await this.rpc({
                    model: "pos.order",
                    method: "get_from_ui",
                    args: [order.name]
                });

                if (destinationOrder){
                    destinationOrder.set_partner(partner)
                    destinationOrder.l10n_do_fiscal_number = result.l10n_do_fiscal_number;
                    destinationOrder.l10n_do_ncf_expiration_date = result.l10n_do_ncf_expiration_date;
                    destinationOrder.l10n_do_origin_ncf = result.l10n_do_fiscal_number;
                    destinationOrder.l10n_do_return_order_id = result.return_order_id;
                    destinationOrder.l10n_do_is_return_order = true;
                }
                super._onDoRefund();
            }
            getNcfExpirationDate(order) {
                return moment(order.l10n_do_ncf_expiration_date).format('DD-MM-YYYY');
            }
        };

    Registries.Component.extend(TicketScreen, TicketScreenInherit);
    return TicketScreen;
});
