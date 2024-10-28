odoo.define('l10n_do_pos.OrderReceipt', function (require) {
"use strict";
    const OrderReceipt = require('point_of_sale.OrderReceipt');
    const Registries = require("point_of_sale.Registries");
    var field_utils = require('web.field_utils');

    const OrderReceiptInherit = (OrderReceipt) => class extends OrderReceipt {
        _formatDate(value) {
            return field_utils.format.date(moment(value), {}, {timezone: false});
        }
    };

    Registries.Component.extend(OrderReceipt, OrderReceiptInherit);
    return OrderReceipt;
});
