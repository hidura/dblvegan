//En fin de este metodo es poder llamar al window.postMessage de manera rapida.
// Y si se necesesita otro protocolo cambiarlo rapidamente

//console.log("Se cargo protocol message");
odoo.define('protocol_message.protocol_message', function () {

    window.interfaz_protocol = (function () {
        var oevent;
        
        class Message {
            constructor(action, data) {
                this.action = action,
                this.data = data
            };
        }


        var send_message = function (action, data) {

            try {
                // Simplemente anadimos la data que queremos enviar al evento y lo disparamos

                oevent = new CustomEvent("odoo_message", {
                    detail: JSON.stringify(new Message(action, data))
                });


                this.dispatchEvent(oevent);


            } catch (error) {
                console.log("No se pudo enviar el mensaje:", error);

            }
        }

        var exports = {
            send_message: send_message
        }

        return exports;

    })();


});