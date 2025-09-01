# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class WhatsAppSendMessageWizard(models.TransientModel):
    _name = 'whatsapp.send.message.wizard'
    _description = 'Send WhatsApp Message Wizard'

    partner_id = fields.Many2one(
        'res.partner',
        string='Contact',
        help='Contact to send the message to'
    )
    
    phone_number = fields.Char(
        string='Phone Number',
        required=True,
        help='WhatsApp phone number (with country code)'
    )
    
    message = fields.Text(
        string='Message',
        required=True,
        help='Message content to send'
    )
    
    config_id = fields.Many2one(
        'whatsapp.config',
        string='Configuration',
        help='WhatsApp configuration to use (leave empty for default)'
    )
    
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments',
        help='Files to send with the message'
    )
    
    send_immediately = fields.Boolean(
        string='Send Immediately',
        default=True,
        help='Send the message immediately or save as draft'
    )
    
    pos_order_id = fields.Many2one(
        'pos.order',
        string='POS Order',
        help='Related POS order if message is sent from POS'
    )
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update phone number when partner changes"""
        if self.partner_id and self.partner_id.mobile:
            self.phone_number = self.partner_id.mobile
    
    def action_send_message(self):
        """Send the WhatsApp message"""
        self.ensure_one()
        
        # Validate phone number
        if not self.phone_number:
            raise UserError("Phone number is required")
        
        # Create message record
        message_vals = {
            'subject': f"Message to {self.partner_id.name if self.partner_id else self.phone_number}",
            'partner_id': self.partner_id.id if self.partner_id else False,
            'phone_number': self.phone_number,
            'message_type': 'attachment' if self.attachment_ids else 'text',
            'content': self.message,
            'config_id': self.config_id.id if self.config_id else False,
            'pos_order_id': self.pos_order_id.id if self.pos_order_id else False,
        }
        
        message = self.env['whatsapp.message'].create(message_vals)
        
        # Attach files if any
        if self.attachment_ids:
            for attachment in self.attachment_ids:
                attachment.copy({'res_model': 'whatsapp.message', 'res_id': message.id})
        
        # Send immediately if requested
        if self.send_immediately:
            try:
                message.action_send_message()
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Message Sent',
                        'message': f'WhatsApp message sent successfully to {self.phone_number}',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            except Exception as e:
                _logger.error(f"Error sending message: {str(e)}")
                raise UserError(f"Failed to send message: {str(e)}")
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Message Saved',
                    'message': f'WhatsApp message saved as draft',
                    'type': 'info',
                    'sticky': False,
                }
            }
    
    def action_send_and_view_message(self):
        """Send message and open the message record"""
        result = self.action_send_message()
        
        if result.get('params', {}).get('type') == 'success':
            # Find the created message
            message = self.env['whatsapp.message'].search([
                ('phone_number', '=', self.phone_number),
                ('content', '=', self.message)
            ], limit=1, order='create_date desc')
            
            if message:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'WhatsApp Message',
                    'res_model': 'whatsapp.message',
                    'res_id': message.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
        
        return result