odoo.define("henca_fiscal.SyncNotification", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const SyncNotification = require("point_of_sale.SyncNotification");

    const HencaFiscalSyncNotification = (SyncNotification) => class extends SyncNotification {
        set_status_printer(status, msg) {
            console.log('1111111111', status, msg);
            const posibleStatuses = ['connected', 'connecting', 'disconnected', 'error'];
            for (var i = 0; i < posibleStatuses.length; i++) {
                if (posibleStatuses[i] !== status) {
                    document.querySelector('.js_printer_' + posibleStatuses[i]).classList.add('oe_hidden');
                } else {
                    document.querySelector('.js_printer_' + posibleStatuses[i]).classList.remove('oe_hidden');
                }
            }
            let js_msg_element = document.querySelector('.js_msg_printer');
            if (msg) {
                js_msg_element.classList.remove('oe_hidden');
                js_msg_element.innerHTML = msg;
            } else {
                js_msg_element.classList.add('oe_hidden');
                js_msg_element.innerHTML = '';
            }
        }
        onClick() {
            super.onClick();
            var self = this;

            let iface_fiscal_printer_host = self.env.pos.config.iface_fiscal_printer_host;
            if (iface_fiscal_printer_host) {
                $.ajax({
                    type: 'GET',
                    url: iface_fiscal_printer_host + "/state",
                }).done(function (response) {
                    console.log('Successful response', response);
                    let data = {}
                    if (response) {
                        try {
                            data = JSON.parse(response);
                        } catch (error) {
                            data = response;
                        }
                        let state = data["response"]["printer_status"]["state"];
                        if (state === "online") {
                            self.set_status_printer("connected", false);
                            Swal.fire({
                                title: 'Estado de la impresora',
                                text: "En linea",
                                icon: 'success',
                                confirmButtonText: 'Aceptar'
                            });
                        } else {
                            self.set_status_printer("disconnected", false);
                            Swal.fire({
                                title: 'Estado de la impresora',
                                text: "No hay conexion con la impresora",
                                icon: 'error',
                                confirmButtonText: 'Aceptar'
                            });
                        }
                    } else {
                        self.set_status_printer("disconnected", false);
                        Swal.fire({
                            title: 'Estado de la impresora',
                            text: "No hubo respuesta con la interfaz",
                            icon: 'error',
                            confirmButtonText: 'Aceptar'
                        });
                    }
                }).fail(function (response) {
                    console.log('Failed response', response);
                    self.set_status_printer("disconnected", false);
                    Swal.fire({
                        title: 'Error en la impresion fiscal',
                        text: 'Error al intentar conectarse con la impresora fiscal',
                        icon: 'error',
                        confirmButtonText: 'Aceptar'
                    });
                });
            }
        }
    };

    Registries.Component.extend(SyncNotification, HencaFiscalSyncNotification);
    return HencaFiscalSyncNotification;
});
