odoo.define('l10n_do_pos.PartnerDetailsEdit', function (require) {
    "use strict";

    const { useState, useEffect, useRef,onMounted } = owl;
    const PartnerDetailsEdit = require('point_of_sale.PartnerDetailsEdit');
    const Registries = require("point_of_sale.Registries");
    const { Gui } = require('point_of_sale.Gui');
    const { _t } = require('web.core');

    const PartnerDetailsEditInherit = (PartnerDetailsEdit) => class extends PartnerDetailsEdit {
            setup() {
                super.setup();
                const partner = this.props.partner;
                this.changes.l10n_do_dgii_tax_payer_type = partner.l10n_do_dgii_tax_payer_type || "";
                this.urlInputRef = useRef('partner-name-search');
                onMounted(this.mountAutoComplete);
            }
            saveChanges() {
                if (this.props.partner.id === this.env.pos.config.default_partner_id[0]){
                    Gui.showPopup('ErrorPopup', {
                        title: this.env._t('Permiso denegado'),
                        body: this.env._t('No puede modificar este cliente! Debe crear uno o colocar una referencia desde el pedido'),
                    });
                    return false;
                }
                super.saveChanges();
            }
            mountAutoComplete() {
                var self = this;
                const $input = $(this.urlInputRef.el);
                $input.autocomplete({
                    source: "/dgii_ws",
                    minLength: 3,
                    delay: 200,
                    select: function (event, ui) {
                        if (ui.item.exists) {
                            Gui.showPopup('ErrorPopup', {
                                title: 'Duplicidad',
                                body: 'Ya existe un cliente con este RNC.',
                            });
                            return false;
                        }
                        $input.val(ui.item.name);
                        var $search_input = $("input[name$='search']");
                        var $name_input = $("input[name$='name']");
                        var $rnc_input = $("input[name$='vat']");
                        var $tax_payer_type_input = $("select[name$='l10n_do_dgii_tax_payer_type']");
                        $search_input.val('');
                        $name_input.val(ui.item.name);
                        $rnc_input.val(ui.item.rnc);
                        $tax_payer_type_input.val(ui.item.l10n_do_dgii_tax_payer_type);
                        self.changes.search = '';
                        self.changes.name = ui.item.name;
                        self.changes.vat = ui.item.rnc;
                        self.changes.l10n_do_dgii_tax_payer_type = ui.item.l10n_do_dgii_tax_payer_type;
                    },
                    response: function (event, ui) {
                        // Selecting the first item if the result is only one
                        if (Array.isArray(ui.content) && ui.content.length === 1 && $.isNumeric($input.val())) {
                            var input = $(this);
                            ui.item = ui.content[0];
                            input.data('ui-autocomplete')._trigger('select', 'autocompleteselect', ui);
                            input.autocomplete('close');
                            input.blur();
                        }
                    },
                });
            }
        };
    PartnerDetailsEditInherit.template = "l10n_do_pos.PartnerDetailsEdit";
    Registries.Component.extend(PartnerDetailsEdit, PartnerDetailsEditInherit);
    return PartnerDetailsEdit;
});
