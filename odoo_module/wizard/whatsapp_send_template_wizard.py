# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)

class WhatsAppSendTemplateWizard(models.TransientModel):
    _name = 'whatsapp.send.template.wizard'
    _description = 'Send WhatsApp Template Message Wizard'

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
    
    template_id = fields.Many2one(
        'whatsapp.template',
        string='Template',
        required=True,
        domain=[('active', '=', True)],
        help='Template to use for the message'
    )
    
    template_variables = fields.Text(
        string='Template Variables (JSON)',
        help='Variables for the template in JSON format'
    )
    
    config_id = fields.Many2one(
        'whatsapp.config',
        string='Configuration',
        help='WhatsApp configuration to use (leave empty for default)'
    )
    
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments',
        help='Files to send with the message (for receipt/ebook templates)'
    )
    
    send_immediately = fields.Boolean(
        string='Send Immediately',
        default=True,
        help='Send the message immediately or save as draft'
    )
    
    preview_content = fields.Text(
        string='Preview',
        readonly=True,
        help='Preview of the rendered template'
    )
    
    # Dynamic fields for template variables
    variable_fields = fields.Text(
        string='Variable Fields',
        compute='_compute_variable_fields'
    )
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update phone number when partner changes"""
        if self.partner_id and self.partner_id.mobile:
            self.phone_number = self.partner_id.mobile
        
        # Also update template variables if partner is selected
        self._update_template_variables_from_partner()
    
    @api.onchange('template_id')
    def _onchange_template_id(self):
        """Update preview when template changes"""
        self._update_template_variables_from_partner()
        self._update_preview()
    
    @api.onchange('template_variables')
    def _onchange_template_variables(self):
        """Update preview when variables change"""
        self._update_preview()
    
    @api.depends('template_id')
    def _compute_variable_fields(self):
        """Compute dynamic variable fields based on template"""
        for wizard in self:
            if wizard.template_id:
                variables = wizard.template_id.get_variables_list()
                wizard.variable_fields = json.dumps(variables)
            else:
                wizard.variable_fields = '[]'
    
    def _update_template_variables_from_partner(self):
        """Auto-populate template variables from partner data"""
        if self.partner_id and self.template_id:
            variables = {}
            
            # Get template variables
            template_vars = self.template_id.get_variables_list()
            
            for var in template_vars:
                var_name = var.get('name', '')
                
                # Auto-populate common variables from partner
                if var_name in ['name', 'customer_name']:
                    variables[var_name] = self.partner_id.name
                elif var_name == 'email':
                    variables[var_name] = self.partner_id.email or ''
                elif var_name == 'phone':
                    variables[var_name] = self.partner_id.phone or ''
                elif var_name == 'mobile':
                    variables[var_name] = self.partner_id.mobile or ''
                elif var_name == 'company':
                    variables[var_name] = self.partner_id.company_name or ''
            
            if variables:
                self.template_variables = json.dumps(variables, indent=2)
    
    def _update_preview(self):
        """Update the template preview"""
        if self.template_id:
            try:
                variables = {}
                if self.template_variables:
                    variables = json.loads(self.template_variables)
                
                self.preview_content = self.template_id.render_template(variables)
            except json.JSONDecodeError:
                self.preview_content = "Invalid JSON in template variables"
            except Exception as e:
                self.preview_content = f"Error rendering template: {str(e)}"
        else:
            self.preview_content = ""
    
    def action_preview_template(self):
        """Show detailed template preview"""
        self.ensure_one()
        self._update_preview()
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Preview: {self.template_id.title}',
            'res_model': 'whatsapp.template.preview',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.template_id.id,
                'default_preview_content': self.preview_content,
            }
        }
    
    def action_send_template(self):
        """Send the templated WhatsApp message"""
        self.ensure_one()
        
        # Validate inputs
        if not self.phone_number:
            raise UserError("Phone number is required")
        
        if not self.template_id:
            raise UserError("Template is required")
        
        # Parse template variables
        variables = {}
        if self.template_variables:
            try:
                variables = json.loads(self.template_variables)
            except json.JSONDecodeError:
                raise UserError("Template variables must be valid JSON")
        
        # Determine message type based on template and attachments
        message_type = 'template'
        if self.template_id.category == 'receipt' and self.attachment_ids:
            message_type = 'receipt'
        elif self.template_id.category == 'ebook' and self.attachment_ids:
            message_type = 'ebook'
        elif self.attachment_ids:
            message_type = 'attachment'
        
        # Create message record
        message_vals = {
            'subject': f"{self.template_id.title} to {self.partner_id.name if self.partner_id else self.phone_number}",
            'partner_id': self.partner_id.id if self.partner_id else False,
            'phone_number': self.phone_number,
            'message_type': message_type,
            'template_name': self.template_id.name,
            'template_variables': self.template_variables,
            'content': self.preview_content,
            'config_id': self.config_id.id if self.config_id else False,
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
                        'title': 'Template Message Sent',
                        'message': f'WhatsApp template message sent successfully to {self.phone_number}',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            except Exception as e:
                _logger.error(f"Error sending template message: {str(e)}")
                raise UserError(f"Failed to send template message: {str(e)}")
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Template Message Saved',
                    'message': f'WhatsApp template message saved as draft',
                    'type': 'info',
                    'sticky': False,
                }
            }
    
    def action_send_and_view_message(self):
        """Send template message and open the message record"""
        result = self.action_send_template()
        
        if result.get('params', {}).get('type') == 'success':
            # Find the created message
            message = self.env['whatsapp.message'].search([
                ('phone_number', '=', self.phone_number),
                ('template_name', '=', self.template_id.name)
            ], limit=1, order='create_date desc')
            
            if message:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'WhatsApp Template Message',
                    'res_model': 'whatsapp.message',
                    'res_id': message.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
        
        return result