# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class WhatsAppAPI(http.Controller):
    """
    REST API endpoints for WhatsApp integration
    """
    
    @http.route('/api/whatsapp/send', type='json', auth='user', methods=['POST'], csrf=False)
    def send_message(self, **kwargs):
        """Send a WhatsApp message via API"""
        try:
            phone_number = kwargs.get('phone_number')
            message = kwargs.get('message')
            partner_id = kwargs.get('partner_id')
            
            if not phone_number or not message:
                return {'success': False, 'error': 'phone_number and message are required'}
            
            # Create message record
            message_vals = {
                'subject': f"API Message to {phone_number}",
                'phone_number': phone_number,
                'message_type': 'text',
                'content': message,
            }
            
            if partner_id:
                message_vals['partner_id'] = partner_id
            
            message_record = request.env['whatsapp.message'].create(message_vals)
            
            # Send the message
            result = message_record.action_send_message()
            
            return {
                'success': True,
                'message_id': message_record.id,
                'provider_message_id': message_record.provider_message_id
            }
            
        except Exception as e:
            _logger.error(f"API error sending WhatsApp message: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/whatsapp/send-template', type='json', auth='user', methods=['POST'], csrf=False)
    def send_template(self, **kwargs):
        """Send a templated WhatsApp message via API"""
        try:
            phone_number = kwargs.get('phone_number')
            template_name = kwargs.get('template_name')
            variables = kwargs.get('variables', {})
            partner_id = kwargs.get('partner_id')
            
            if not phone_number or not template_name:
                return {'success': False, 'error': 'phone_number and template_name are required'}
            
            # Check if template exists
            template = request.env['whatsapp.template'].search([('name', '=', template_name)], limit=1)
            if not template:
                return {'success': False, 'error': f'Template "{template_name}" not found'}
            
            # Create message record
            message_vals = {
                'subject': f"Template {template_name} to {phone_number}",
                'phone_number': phone_number,
                'message_type': 'template',
                'template_name': template_name,
                'template_variables': json.dumps(variables),
                'content': template.render_template(variables),
            }
            
            if partner_id:
                message_vals['partner_id'] = partner_id
            
            message_record = request.env['whatsapp.message'].create(message_vals)
            
            # Send the message
            result = message_record.action_send_message()
            
            return {
                'success': True,
                'message_id': message_record.id,
                'provider_message_id': message_record.provider_message_id
            }
            
        except Exception as e:
            _logger.error(f"API error sending WhatsApp template: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/whatsapp/status/<int:message_id>', type='json', auth='user', methods=['GET'])
    def get_message_status(self, message_id):
        """Get the status of a WhatsApp message"""
        try:
            message = request.env['whatsapp.message'].browse(message_id)
            if not message.exists():
                return {'success': False, 'error': 'Message not found'}
            
            return {
                'success': True,
                'message_id': message.id,
                'state': message.state,
                'sent_date': message.sent_date.isoformat() if message.sent_date else None,
                'delivered_date': message.delivered_date.isoformat() if message.delivered_date else None,
                'read_date': message.read_date.isoformat() if message.read_date else None,
                'error_message': message.error_message,
                'provider_message_id': message.provider_message_id
            }
            
        except Exception as e:
            _logger.error(f"API error getting message status: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/whatsapp/templates', type='json', auth='user', methods=['GET'])
    def list_templates(self):
        """List available WhatsApp templates"""
        try:
            templates = request.env['whatsapp.template'].search([('active', '=', True)])
            
            template_list = []
            for template in templates:
                template_list.append({
                    'id': template.id,
                    'name': template.name,
                    'title': template.title,
                    'category': template.category,
                    'description': template.description,
                    'variables': template.get_variables_list(),
                    'preview': template.get_preview()
                })
            
            return {
                'success': True,
                'templates': template_list
            }
            
        except Exception as e:
            _logger.error(f"API error listing templates: {str(e)}")
            return {'success': False, 'error': str(e)}