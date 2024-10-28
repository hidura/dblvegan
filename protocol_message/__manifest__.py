# -*- coding: utf-8 -*-
{
    'name': "Procolo:Mensaje",

    'summary': """
        Permite el envio y la recepción de datos con la extension de navegador.
       """,

    'description': """
        Protocolo para comunicarse con la extension, Usando (PostMessage)
    """,

    'author': "Neotec Group",
    'website': "http://www.neotec.do/",

    'category': 'Neotec/Protocolo',
    'version': '16.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','web'],


    'assets': {
           'web.assets_backend': [
            'protocol_message/static/src/js/protocol.js',
        ],
    },
    "license": "LGPL-3"
}