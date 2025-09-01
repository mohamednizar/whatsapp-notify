from odoo import models, api, _, fields
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

# Check if pos.order model exists before inheriting
try:
    # Test if POS module is available
    from odoo.addons.point_of_sale.models.pos_order import PosOrder as BasePosOrder
    POS_AVAILABLE = True
except ImportError:
    POS_AVAILABLE = False
    _logger.warning("Point of Sale module not available - POS WhatsApp integration disabled")

if POS_AVAILABLE:
    class PosOrder(models.Model):
        _inherit = "pos.order"

        whatsapp_sent = fields.Boolean(string="WhatsApp Sent", default=False, help="Whether WhatsApp message has been sent for this order")
        whatsapp_message_ids = fields.One2many('whatsapp.message', 'pos_order_id', string="WhatsApp Messages")
        can_send_whatsapp = fields.Boolean(string="Can Send WhatsApp", compute="_compute_can_send_whatsapp", help="Whether WhatsApp can be sent to this customer")

        @api.depends('partner_id', 'partner_id.mobile', 'partner_id.phone')
        def _compute_can_send_whatsapp(self):
            for order in self:
                order.can_send_whatsapp = (
                    order.partner_id and 
                    (order.partner_id.mobile or order.partner_id.phone)
                )

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
                                'download_link': download_link,
                                'quantity': line.qty,
                                'line_id': line.id
                            })
                            _logger.info("Line %d: Added digital link for '%s'", line_num, line.product_id.name)
                        else:
                            _logger.info("Line %d: Product marked as digital but no download links found", line_num)
                    else:
                        _logger.info("Line %d: Product validation failed: %s", line_num, validation_result.get('errors', []))
                else:
                    _logger.info("Line %d: No product_id found", line_num)
            
            _logger.info("=== DIGITAL PRODUCT PROCESSING END ===")
            _logger.info("Total digital products found: %d", len(digital_links))
            
            return digital_links

        def _get_receipt_data(self):
            """Prepare receipt data for WhatsApp message"""
            self.ensure_one()
            
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
                import importlib.util
                import os
                
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
                    raise UserError(_("No active WhatsApp configuration found. Please configure WhatsApp first."))
                
                # Create WhatsApp message record
                subject = f"POS {message_type.title()} - {self.name}"
                if self.partner_id:
                    subject += f" ({self.partner_id.name})"
                
                message_vals = {
                    'subject': subject,
                    'partner_id': self.partner_id.id if self.partner_id else False,
                    'phone_number': phone,
                    'message_type': message_type,
                    'content': message,
                    'pos_order_id': self.id,
                    'config_id': config.id,
                }
                
                whatsapp_message = self.env['whatsapp.message'].create(message_vals)
                
                # Send the message
                result = whatsapp_message.action_send_message()
                
                # Mark order as WhatsApp sent
                self.write({'whatsapp_sent': True})
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('WhatsApp Message Sent'),
                        'message': _('Message sent successfully to %s') % phone,
                        'type': 'success',
                        'sticky': False,
                    }
                }
                
            except Exception as e:
                _logger.error("Failed to send WhatsApp message: %s", str(e))
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('WhatsApp Message Failed'),
                        'message': _('Failed to send message: %s') % str(e),
                        'type': 'danger',
                        'sticky': True,
                    }
                }

        def action_view_whatsapp_messages(self):
            """View WhatsApp messages for this order"""
            return {
                'type': 'ir.actions.act_window',
                'name': _('WhatsApp Messages'),
                'res_model': 'whatsapp.message',
                'view_mode': 'tree,form',
                'domain': [('pos_order_id', '=', self.id)],
                'context': {
                    'default_pos_order_id': self.id,
                    'default_partner_id': self.partner_id.id if self.partner_id else False,
                    'default_phone_number': self.partner_id.mobile or self.partner_id.phone if self.partner_id else '',
                }
            }