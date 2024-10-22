odoo.define("l10n_do_pos.MoveReversal", function (require) {
     const PosComponent = require('point_of_sale.PosComponent');
     const Registries = require('point_of_sale.Registries');
     const { useState } = owl;

     class MoveReversal extends PosComponent {
        setup() {
            super.setup();
            this.state = useState({
                'modification_code': this.props.selectedOrder.l10n_do_ecf_modification_code,
            });
        }
        pillClicked(ev) {
            ev.stopPropagation();
            this.trigger('code-updated', {modification_code: this.state.modification_code});
        }
    };
    MoveReversal.template = 'MoveReversal';
    Registries.Component.add(MoveReversal);
 });
