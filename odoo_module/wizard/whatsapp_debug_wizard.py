# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import json
import importlib.util

_logger = logging.getLogger(__name__)

class WhatsAppDebugTestWizard(models.TransientModel):
    _name = 'whatsapp.debug.test.wizard'
    _description = 'WhatsApp Debug Test Wizard'

    config_id = fields.Many2one(
        'whatsapp.config',
        string='Configuration',
        required=True,
        help='WhatsApp configuration to test'
    )
    
    phone_number = fields.Char(
        string='Test Phone Number',
        required=True,
        help='Phone number to test delivery (include country code, e.g., +1234567890)'
    )
    
    test_message = fields.Text(
        string='Test Message',
        default='🧪 WhatsApp delivery debug test from Odoo - please ignore this message.',
        help='Message to send for testing'
    )

    def action_run_debug_test(self):
        """Run the comprehensive debug test"""
        self.ensure_one()
        
        try:
            # Dynamically import WhatsApp service
            import os
            services_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'services', 'whatsapp_service')
            spec = importlib.util.spec_from_file_location("whatsapp_service", services_path + '.py')
            whatsapp_service_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(whatsapp_service_module)
            WhatsAppService = whatsapp_service_module.WhatsAppService
            
            # Initialize service and run debug test
            service = WhatsAppService(config_record=self.config_id)
            debug_result = service.debug_delivery_test(self.phone_number, self.test_message)
            
            # Create a WhatsApp message record to store the debug results
            message_vals = {
                'subject': f'Debug Test - {self.phone_number}',
                'phone_number': self.phone_number,
                'message_type': 'text',
                'content': self.test_message,
                'config_id': self.config_id.id,
                'state': 'sent' if debug_result['success'] else 'failed',
            }
            
            if debug_result['success']:
                message_vals.update({
                    'provider_message_id': debug_result.get('message_id'),
                    'sent_date': fields.Datetime.now(),
                    'delivery_status': 'pending'
                })
            else:
                message_vals.update({
                    'error_message': debug_result.get('error'),
                    'failure_reason': 'unknown_error'
                })
            
            # Store debug information
            debug_data = {
                'debug_test_result': debug_result,
                'config_used': {
                    'name': self.config_id.name,
                    'provider': self.config_id.provider,
                    'test_mode': self.config_id.test_mode
                }
            }
            
            message_vals.update({
                'api_request_data': json.dumps(debug_data, indent=2),
                'api_response_data': json.dumps(debug_result.get('debug', {}), indent=2)
            })
            
            message = self.env['whatsapp.message'].create(message_vals)
            
            # Prepare result message
            if debug_result['success']:
                result_title = '✅ Debug Test Successful'
                result_message = f'''Debug test completed successfully!

Message ID: {debug_result.get('message_id', 'N/A')}
Phone: {self.phone_number}
Provider: {self.config_id.provider}

Check the created WhatsApp message record for detailed debugging information.'''
                notification_type = 'success'
            else:
                result_title = '❌ Debug Test Failed'
                result_message = f'''Debug test failed: {debug_result.get('error', 'Unknown error')}

Phone: {self.phone_number}
Provider: {self.config_id.provider}

Check the created WhatsApp message record for detailed troubleshooting information.'''
                notification_type = 'danger'
            
            # Show the created message record
            return {
                'type': 'ir.actions.act_window',
                'name': 'Debug Test Result',
                'res_model': 'whatsapp.message',
                'res_id': message.id,
                'view_mode': 'form',
                'target': 'current',
                'context': {
                    'debug_test_result': debug_result,
                    'show_notification': {
                        'title': result_title,
                        'message': result_message,
                        'type': notification_type
                    }
                }
            }
            
        except Exception as e:
            error_msg = str(e)
            _logger.error(f"Debug test wizard failed: {error_msg}")
            raise UserError(f"Debug test failed: {error_msg}")