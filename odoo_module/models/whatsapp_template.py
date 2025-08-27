# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json
import logging

_logger = logging.getLogger(__name__)

class WhatsAppTemplate(models.Model):
    _name = 'whatsapp.template'
    _description = 'WhatsApp Message Template'
    _rec_name = 'name'

    name = fields.Char(
        string='Template Name',
        required=True,
        help='Unique name for the template'
    )
    
    title = fields.Char(
        string='Template Title',
        required=True,
        help='Human readable title for the template'
    )
    
    description = fields.Text(
        string='Description',
        help='Description of when to use this template'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this template is active'
    )
    
    content = fields.Text(
        string='Template Content',
        required=True,
        help='Template content with variables in {{variable}} format'
    )
    
    variables = fields.Text(
        string='Variables',
        help='JSON array of variable definitions with names, types, and descriptions'
    )
    
    category = fields.Selection([
        ('welcome', 'Welcome'),
        ('notification', 'Notification'),
        ('receipt', 'Receipt'),
        ('ebook', 'E-book'),
        ('order', 'Order'),
        ('custom', 'Custom'),
    ], string='Category', default='custom', help='Template category')
    
    usage_count = fields.Integer(
        string='Usage Count',
        default=0,
        help='Number of times this template has been used'
    )
    
    @api.constrains('name')
    def _check_unique_name(self):
        """Ensure template names are unique"""
        for record in self:
            if self.search_count([('name', '=', record.name), ('id', '!=', record.id)]) > 0:
                raise ValidationError(f"Template name '{record.name}' already exists")
    
    @api.constrains('variables')
    def _check_variables_json(self):
        """Validate that variables field contains valid JSON"""
        for record in self:
            if record.variables:
                try:
                    json.loads(record.variables)
                except json.JSONDecodeError:
                    raise ValidationError("Variables field must contain valid JSON")
    
    def get_variables_list(self):
        """Get the list of variables as Python objects"""
        self.ensure_one()
        if self.variables:
            try:
                return json.loads(self.variables)
            except json.JSONDecodeError:
                _logger.warning(f"Invalid JSON in template {self.name} variables")
        return []
    
    def render_template(self, variables_dict):
        """Render the template with provided variables"""
        self.ensure_one()
        
        content = self.content
        for key, value in variables_dict.items():
            placeholder = f'{{{{{key}}}}}'
            content = content.replace(placeholder, str(value))
        
        # Increment usage count
        self.usage_count += 1
        
        return content
    
    def get_preview(self, sample_variables=None):
        """Get a preview of the template with sample data"""
        self.ensure_one()
        
        if not sample_variables:
            # Use default sample variables
            variables_list = self.get_variables_list()
            sample_variables = {}
            for var in variables_list:
                var_name = var.get('name', '')
                var_type = var.get('type', 'text')
                
                if var_type == 'text':
                    sample_variables[var_name] = f'[{var_name.upper()}]'
                elif var_type == 'number':
                    sample_variables[var_name] = '123'
                elif var_type == 'date':
                    sample_variables[var_name] = '2024-01-01'
                elif var_type == 'currency':
                    sample_variables[var_name] = '$99.99'
                else:
                    sample_variables[var_name] = f'[{var_name.upper()}]'
        
        return self.render_template(sample_variables)
    
    @api.model
    def create_default_templates(self):
        """Create default templates if they don't exist"""
        default_templates = [
            {
                'name': 'welcome',
                'title': 'Welcome Message',
                'category': 'welcome',
                'description': 'Welcome message for new customers',
                'content': 'Hello {{name}}! Welcome to our service. We\'re excited to have you on board!',
                'variables': json.dumps([
                    {'name': 'name', 'type': 'text', 'description': 'Customer name', 'required': True}
                ])
            },
            {
                'name': 'receipt',
                'title': 'Receipt Delivery',
                'category': 'receipt',
                'description': 'Send receipt with PDF attachment',
                'content': 'Hi {{customer_name}}, your receipt for order {{order_id}} ({{amount}}) is attached. Thank you for your business!',
                'variables': json.dumps([
                    {'name': 'customer_name', 'type': 'text', 'description': 'Customer name', 'required': True},
                    {'name': 'order_id', 'type': 'text', 'description': 'Order ID', 'required': True},
                    {'name': 'amount', 'type': 'currency', 'description': 'Order amount', 'required': True}
                ])
            },
            {
                'name': 'ebook',
                'title': 'E-book Delivery',
                'category': 'ebook',
                'description': 'Send e-book with file attachment',
                'content': 'Here\'s your e-book "{{book_title}}" by {{author}}. Enjoy your reading!',
                'variables': json.dumps([
                    {'name': 'book_title', 'type': 'text', 'description': 'Book title', 'required': True},
                    {'name': 'author', 'type': 'text', 'description': 'Book author', 'required': True}
                ])
            },
            {
                'name': 'order_confirmation',
                'title': 'Order Confirmation',
                'category': 'order',
                'description': 'Confirm order placement',
                'content': 'Hi {{customer_name}}, your order {{order_id}} for {{amount}} has been confirmed. Expected delivery: {{delivery_date}}.',
                'variables': json.dumps([
                    {'name': 'customer_name', 'type': 'text', 'description': 'Customer name', 'required': True},
                    {'name': 'order_id', 'type': 'text', 'description': 'Order ID', 'required': True},
                    {'name': 'amount', 'type': 'currency', 'description': 'Order amount', 'required': True},
                    {'name': 'delivery_date', 'type': 'date', 'description': 'Expected delivery date', 'required': True}
                ])
            }
        ]
        
        for template_data in default_templates:
            existing = self.search([('name', '=', template_data['name'])], limit=1)
            if not existing:
                self.create(template_data)
                _logger.info(f"Created default template: {template_data['name']}")
    
    def action_preview_template(self):
        """Show template preview"""
        self.ensure_one()
        preview_content = self.get_preview()
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Preview: {self.title}',
            'res_model': 'whatsapp.template.preview',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.id,
                'default_preview_content': preview_content,
            }
        }