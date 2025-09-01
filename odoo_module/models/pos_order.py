from odoo import models, api, _, fields
from odoo.exceptions import UserError
import logging
import importlib.util
import os

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = "pos.order"

    whatsapp_sent = fields.Boolean(string="WhatsApp Sent", default=False, help="Whether WhatsApp message has been sent for this order")
    whatsapp_message_ids = fields.One2many('whatsapp.message', 'pos_order_id', string="WhatsApp Messages")

    def _get_digital_product_links(self):
        """Extract download links for digital products (E-Books) in the POS order"""
        _logger.info("=== DIGITAL PRODUCT PROCESSING START ===")
        _logger.info("Processing POS order '%s' (ID: %s) for digital product links", self.name, self.id)
        _logger.info("Order has %d line(s)", len(self.lines))
        
        digital_links = []
        for line_num, line in enumerate(self.lines, 1):
            _logger.info("--- Processing order line %d ---", line_num)
            _logger.info("Line %d: product_id=%s, qty=%s", line_num, line.product_id.id if line.product_id else None, line.qty)
            
            # Validate product schema and get digital product info
            if line.product_id:
                _logger.info("Line %d: Validating product '%s' (ID: %s)", line_num, line.product_id.name, line.product_id.id)
                validation_result = line.product_id._validate_digital_product_schema()
                _logger.info("Line %d: Validation result: %s", line_num, validation_result)
                
                if validation_result['is_valid']:
                    _logger.info("Line %d: Product is valid digital product", line_num)
                    # Handle multiple download links per product
                    download_links = validation_result.get('download_links', [])
                    _logger.info("Line %d: Found %d download link(s)", line_num, len(download_links))
                    
                    if download_links:
                        # Use the first download link for backward compatibility
                        download_link = download_links[0] if isinstance(download_links, list) else download_links
                        _logger.info("Line %d: Using download link: %s", line_num, download_link)
                        
                        digital_links.append({
                            'product_name': line.product_id.name,
                            'product_id': line.product_id.id,
                            'download_link': download_link,
                            'quantity': line.qty,
                            'line_id': line.id
                        })
                    else:
                        _logger.warning("Line %d: No download links found for digital product", line_num)
                else:
                    _logger.info("Line %d: Product is not a digital product", line_num)
            else:
                _logger.warning("Line %d: No product found for order line", line_num)
        
        _logger.info("=== DIGITAL PRODUCT PROCESSING END ===")
        _logger.info("Total digital products found: %d", len(digital_links))
        return digital_links

    def _get_receipt_data(self):
        """Get receipt data for WhatsApp message"""
        receipt_data = {
            'order_name': self.name,
            'order_date': self.date_order.strftime('%Y-%m-%d %H:%M:%S') if self.date_order else '',
            'partner_name': self.partner_id.name if self.partner_id else 'Walk-in Customer',
            'total_amount': self.amount_total,
            'currency': self.currency_id.name if self.currency_id else '',
            'order_lines': []
        }
        
        for line in self.lines:
            receipt_data['order_lines'].append({
                'product_name': line.product_id.name if line.product_id else '',
                'quantity': line.qty,
                'price_unit': line.price_unit,
                'price_subtotal': line.price_subtotal_incl,
            })
        
        return receipt_data

    def _load_whatsapp_service(self):
        """Dynamically load WhatsApp service"""
        try:
            # Get the path to the services directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            services_path = os.path.join(os.path.dirname(current_dir), 'services', 'whatsapp_service')
            
            # Dynamically load the WhatsApp service
            spec = importlib.util.spec_from_file_location("whatsapp_service", services_path + '.py')
            whatsapp_service_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(whatsapp_service_module)
            
            return whatsapp_service_module.WhatsAppService
        except Exception as e:
            _logger.error("Failed to load WhatsApp service: %s", str(e))
            raise UserError(_("Failed to load WhatsApp service: %s") % str(e))

    def action_send_whatsapp_receipt(self):
        """Send receipt via WhatsApp"""
        if not self.partner_id:
            raise UserError(_("Please select a customer to send WhatsApp message."))
        
        if not self.partner_id.mobile and not self.partner_id.phone:
            raise UserError(_("Customer does not have a phone number."))

        # Get phone number
        phone = self.partner_id.mobile or self.partner_id.phone
        
        # Get receipt data
        receipt_data = self._get_receipt_data()
        
        # Create receipt message
        message_text = f"""🧾 *Receipt - {receipt_data['order_name']}*

📅 Date: {receipt_data['order_date']}
👤 Customer: {receipt_data['partner_name']}

📋 *Order Details:*
"""
        
        for line in receipt_data['order_lines']:
            message_text += f"• {line['product_name']} x {line['quantity']} = {line['price_subtotal']:.2f} {receipt_data['currency']}\n"
        
        message_text += f"\n💰 *Total: {receipt_data['total_amount']:.2f} {receipt_data['currency']}*"
        
        # Add digital product links if any
        digital_links = self._get_digital_product_links()
        if digital_links:
            message_text += "\n\n📚 *Your E-Books:*\n"
            for link_data in digital_links:
                message_text += f"📖 {link_data['product_name']}: {link_data['download_link']}\n"

        return self._send_whatsapp_message(phone, message_text, "receipt")

    def action_send_whatsapp_ebooks(self):
        """Send only e-books via WhatsApp"""
        if not self.partner_id:
            raise UserError(_("Please select a customer to send WhatsApp message."))
        
        if not self.partner_id.mobile and not self.partner_id.phone:
            raise UserError(_("Customer does not have a phone number."))

        # Get digital product links
        digital_links = self._get_digital_product_links()
        if not digital_links:
            raise UserError(_("No e-books or digital products found in this order."))

        # Get phone number
        phone = self.partner_id.mobile or self.partner_id.phone
        
        # Create e-books message
        message_text = f"📚 *Your E-Books from Order {self.name}*\n\n"
        
        for link_data in digital_links:
            message_text += f"📖 *{link_data['product_name']}*\n"
            message_text += f"🔗 Download: {link_data['download_link']}\n"
            if link_data['quantity'] > 1:
                message_text += f"📦 Quantity: {link_data['quantity']}\n"
            message_text += "\n"
        
        message_text += "Thank you for your purchase! 🎉"

        return self._send_whatsapp_message(phone, message_text, "ebook")

    def _send_whatsapp_message(self, phone, message, message_type="receipt"):
        """Send WhatsApp message using the service"""
        try:
            WhatsAppService = self._load_whatsapp_service()
            
            # Get WhatsApp configuration
            config = self.env['whatsapp.config'].search([('active', '=', True)], limit=1)
            if not config:
                raise UserError(_("No active WhatsApp configuration found. Please configure WhatsApp settings first."))

            # Create WhatsApp message record
            message_data = {
                'phone': phone,
                'message': message,
                'partner_id': self.partner_id.id,
                'pos_order_id': self.id,
                'state': 'draft',
                'config_id': config.id,
                'message_type': message_type,
                'subject': f"POS {message_type.title()} - {self.name}",
            }
            
            whatsapp_message = self.env['whatsapp.message'].create(message_data)
            
            # Send the message
            result = whatsapp_message.action_send_message()
            
            # Mark as sent if successful
            if result and whatsapp_message.state == 'sent':
                self.whatsapp_sent = True
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'success',
                        'title': _("WhatsApp Sent"),
                        'message': _("WhatsApp %s sent successfully to %s") % (message_type, phone),
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'warning',
                        'title': _("WhatsApp Failed"),
                        'message': _("Failed to send WhatsApp %s. Check the message logs for details.") % message_type,
                        'sticky': True,
                    }
                }
                
        except Exception as e:
            _logger.error("Error sending WhatsApp message: %s", str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'title': _("Error"),
                    'message': _("Error sending WhatsApp message: %s") % str(e),
                    'sticky': True,
                }
            }

    def action_open_whatsapp_wizard(self):
        """Open WhatsApp send wizard for POS order"""
        return {
            'name': _('Send WhatsApp Message'),
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.send.message.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id if self.partner_id else False,
                'default_pos_order_id': self.id,
                'default_subject': f"POS Order - {self.name}",
            }
        }