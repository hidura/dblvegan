odoo.define('l10n_do_pos.ClosePosPopup', function(require) {
'use strict';

const ClosePosPopup = require('point_of_sale.ClosePosPopup');
const Registries = require('point_of_sale.Registries');

const ClosePosPopupInherit = ClosePosPopup => class extends ClosePosPopup {
    async confirm() {
        this.downloadSalesReport()
        super.confirm();
    }
};

Registries.Component.extend(ClosePosPopup, ClosePosPopupInherit);
return ClosePosPopup;

});
