odoo.define("henca_fiscal.ProxyStatus", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const ProxyStatus = require("point_of_sale.SyncNotification");

    const HencaFiscalProxyStatus = (ProxyStatus) => class extends ProxyStatus {
        _set_status_printer(status, msg) {
            for (var i = 0; i < this.status.length; i++) {
                this.$('.js_printer_' + this.status[i]).addClass('oe_hidden');
            }
            this.$('.js_printer_' + status).removeClass('oe_hidden');

            if (msg) {
                this.$('.js_msg_printer').removeClass('oe_hidden').html(msg);
            } else {
                this.$('.js_msg_printer').addClass('oe_hidden').html('');
            }
        }
    };
    Registries.Component.extend(ProxyStatus, HencaFiscalProxyStatus);
    return HencaFiscalProxyStatus;

});

