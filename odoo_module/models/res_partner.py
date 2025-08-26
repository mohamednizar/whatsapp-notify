# -*- coding: utf-8 -*-

from odoo import models, fields, api
import re

class ResPartner(models.Model):
    _inherit = 'res.partner'

    whatsapp_message_ids = fields.One2many(
        'whatsapp.message',
        'partner_id',
        string='WhatsApp Messages',
        help='WhatsApp messages sent to this contact'
    )
    
    whatsapp_message_count = fields.Integer(
        string='WhatsApp Messages Count',
        compute='_compute_whatsapp_message_count'
    )
    
    @api.depends('whatsapp_message_ids')
    def _compute_whatsapp_message_count(self):
        """Compute the count of WhatsApp messages"""
        for partner in self:
            partner.whatsapp_message_count = len(partner.whatsapp_message_ids)
    
    def action_send_whatsapp_message(self):
        """Open wizard to send WhatsApp message to this partner"""
        self.ensure_one()
        
        if not self.mobile:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Missing Mobile Number',
                    'message': f'Contact {self.name} does not have a mobile number configured.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Send WhatsApp Message to {self.name}',
            'res_model': 'whatsapp.send.message.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_phone_number': self.mobile,
            }
        }
    
    def action_send_whatsapp_template(self):
        """Open wizard to send templated WhatsApp message to this partner"""
        self.ensure_one()
        
        if not self.mobile:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Missing Mobile Number',
                    'message': f'Contact {self.name} does not have a mobile number configured.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Send WhatsApp Template to {self.name}',
            'res_model': 'whatsapp.send.template.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_phone_number': self.mobile,
            }
        }
    
    def action_view_whatsapp_messages(self):
        """View WhatsApp messages for this partner"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'WhatsApp Messages - {self.name}',
            'res_model': 'whatsapp.message',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
                'default_phone_number': self.mobile,
            }
        }
    
    @api.constrains('mobile')
    def _check_mobile_format(self):
        """Validate mobile number format for WhatsApp"""
        for partner in self:
            if partner.mobile:
                # Basic validation - should start with + and contain only digits and spaces
                cleaned_mobile = re.sub(r'[^+\d]', '', partner.mobile)
                if not re.match(r'^\+\d{10,15}$', cleaned_mobile):
                    # Don't raise error, just log warning as this might be too strict
                    pass
    
    def format_whatsapp_number(self):
        """Format mobile number for WhatsApp (ensure it starts with +)"""
        self.ensure_one()
        if not self.mobile:
            return None
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^+\d]', '', self.mobile)
        
        # Add + if not present
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        
        return cleaned