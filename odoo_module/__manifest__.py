{
    'name': 'WhatsApp Notify Integration',
    'version': '17.0.1.0.0',
    'category': 'Tools',
    'summary': 'WhatsApp messaging integration with Twilio and Meta API support',
    'description': """
WhatsApp Notify Integration
===========================

This module provides comprehensive WhatsApp messaging integration for Odoo CE 17.0.

Features:
---------
* Send WhatsApp messages through Twilio or Meta APIs
* Template-based messaging system
* File attachment support (PDFs, images, documents)
* Message logging and tracking
* Configuration management for multiple providers
* Wizard interfaces for easy message sending
* Integration with Odoo contacts and partners
* POS integration for e-books and receipt delivery
* Digital product management with automatic WhatsApp delivery

Supported Providers:
------------------
* Twilio WhatsApp API
* Meta WhatsApp Business API

Use Cases:
----------
* Send order confirmations and receipts
* Customer notifications and alerts
* Marketing messages with templates
* Document delivery (invoices, reports, etc.)
* Customer support communications
* POS receipt and e-book delivery via WhatsApp
    """,
    'author': 'ht2cloud',
    'website': 'https://github.com/ht2cloud/whatsapp-notify',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'contacts',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/whatsapp_security.xml',
        'data/whatsapp_templates.xml',
        'views/whatsapp_config_views.xml',
        'views/whatsapp_message_views.xml',
        'views/whatsapp_template_views.xml',
        'wizard/whatsapp_send_message_wizard.xml',
        'wizard/whatsapp_send_template_wizard.xml',
        'views/whatsapp_debug_wizard_views.xml',
        'views/res_partner_views.xml',
        'views/product_template_views.xml',
        'views/menu.xml',
    ],
    'demo': [
        'demo/whatsapp_demo.xml',
    ],
    'external_dependencies': {
        'python': ['requests', 'python-dotenv'],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 100,
}
