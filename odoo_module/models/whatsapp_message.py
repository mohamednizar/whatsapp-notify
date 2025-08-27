# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import json
from datetime import datetime

_logger = logging.getLogger(__name__)

MESSAGE_STATES = [
    ('draft', 'Draft'),
    ('sending', 'Sending'),
    ('sent', 'Sent'),
    ('delivered', 'Delivered'),
    ('read', 'Read'),
    ('failed', 'Failed'),
]

MESSAGE_TYPES = [
    ('text', 'Text Message'),
    ('template', 'Template Message'),
    ('receipt', 'Receipt'),
    ('ebook', 'E-book'),
    ('attachment', 'With Attachment'),
]

class WhatsAppMessage(models.Model):
    _name = 'whatsapp.message'
    _description = 'WhatsApp Message Log'
    _order = 'create_date desc'
    _rec_name = 'subject'

    subject = fields.Char(
        string='Subject',
        required=True,
        help='Message subject or description'
    )
    
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
    
    message_type = fields.Selection(
        MESSAGE_TYPES,
        string='Message Type',
        required=True,
        default='text'
    )
    
    state = fields.Selection(
        MESSAGE_STATES,
        string='Status',
        default='draft',
        help='Current status of the message'
    )
    
    content = fields.Text(
        string='Message Content',
        help='The actual message content sent'
    )
    
    template_name = fields.Char(
        string='Template Name',
        help='Name of the template used (if template message)'
    )
    
    template_variables = fields.Text(
        string='Template Variables',
        help='JSON of variables used in template'
    )
    
    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=[('res_model', '=', 'whatsapp.message')],
        string='Attachments'
    )
    
    provider_message_id = fields.Char(
        string='Provider Message ID',
        help='Message ID from the WhatsApp provider'
    )
    
    config_id = fields.Many2one(
        'whatsapp.config',
        string='Configuration Used',
        help='WhatsApp configuration used to send this message'
    )
    
    error_message = fields.Text(
        string='Error Message',
        help='Error details if message failed'
    )
    
    sent_date = fields.Datetime(
        string='Sent Date',
        help='When the message was sent'
    )
    
    delivered_date = fields.Datetime(
        string='Delivered Date',
        help='When the message was delivered'
    )
    
    read_date = fields.Datetime(
        string='Read Date',
        help='When the message was read'
    )
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update phone number when partner changes"""
        if self.partner_id and self.partner_id.mobile:
            self.phone_number = self.partner_id.mobile
    
    def action_send_message(self):
        """Send the WhatsApp message"""
        self.ensure_one()
        
        if self.state != 'draft':
            raise UserError("Only draft messages can be sent")
        
        try:
            # Import the WhatsApp service
            from ..services.whatsapp_service import WhatsAppService
            
            # Get configuration
            config = self.config_id or self.env['whatsapp.config'].get_default_config()
            if not config:
                raise UserError("No WhatsApp configuration found. Please configure a provider first.")
            
            # Initialize service
            service = WhatsAppService(config_record=config)
            
            # Update state
            self.write({
                'state': 'sending',
                'config_id': config.id
            })
            
            # Send based on message type
            result = None
            
            if self.message_type == 'text':
                result = service.send_message(self.phone_number, self.content)
                
            elif self.message_type == 'template':
                variables = {}
                if self.template_variables:
                    try:
                        variables = json.loads(self.template_variables)
                    except json.JSONDecodeError:
                        _logger.warning(f"Invalid template variables JSON: {self.template_variables}")
                
                result = service.send_templated_message(
                    self.phone_number,
                    self.template_name,
                    variables
                )
                
            elif self.message_type in ['receipt', 'ebook', 'attachment']:
                # Handle file attachments
                if not self.attachment_ids:
                    raise UserError("File attachment is required for this message type")
                
                attachment = self.attachment_ids[0]  # Use first attachment
                file_path = attachment._full_path(attachment.store_fname)
                
                if self.message_type == 'receipt':
                    # Extract receipt parameters from template variables
                    variables = json.loads(self.template_variables or '{}')
                    result = service.send_receipt(
                        self.phone_number,
                        variables.get('customer_name', ''),
                        variables.get('order_id', ''),
                        variables.get('amount', ''),
                        file_path
                    )
                elif self.message_type == 'ebook':
                    variables = json.loads(self.template_variables or '{}')
                    result = service.send_ebook(
                        self.phone_number,
                        variables.get('book_title', ''),
                        variables.get('author', ''),
                        file_path
                    )
                else:  # attachment
                    result = service.send_message_with_files(
                        self.phone_number,
                        self.content,
                        [file_path]
                    )
            
            # Update based on result
            if result and result.get('success'):
                self.write({
                    'state': 'sent',
                    'sent_date': fields.Datetime.now(),
                    'provider_message_id': result.get('message_id')
                })
                
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
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Unknown error'
                self.write({
                    'state': 'failed',
                    'error_message': error_msg
                })
                raise UserError(f"Failed to send message: {error_msg}")
                
        except Exception as e:
            _logger.error(f"Error sending WhatsApp message: {str(e)}")
            self.write({
                'state': 'failed',
                'error_message': str(e)
            })
            raise UserError(f"Error sending message: {str(e)}")
    
    def action_retry_send(self):
        """Retry sending a failed message"""
        self.ensure_one()
        if self.state == 'failed':
            self.state = 'draft'
            return self.action_send_message()
        else:
            raise UserError("Only failed messages can be retried")
    
    @api.model
    def create_from_partner(self, partner_id, message_type='text', content='', template_name=None, template_vars=None):
        """Helper method to create message from partner"""
        partner = self.env['res.partner'].browse(partner_id)
        if not partner.mobile:
            raise UserError(f"Partner {partner.name} does not have a mobile number")
        
        values = {
            'subject': f"Message to {partner.name}",
            'partner_id': partner.id,
            'phone_number': partner.mobile,
            'message_type': message_type,
            'content': content,
        }
        
        if template_name:
            values['template_name'] = template_name
        if template_vars:
            values['template_variables'] = json.dumps(template_vars)
            
        return self.create(values)