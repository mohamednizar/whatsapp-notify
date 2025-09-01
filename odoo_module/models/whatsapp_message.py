# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import json
import importlib.util
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
    
    pos_order_id = fields.Many2one(
        'pos.order',
        string='POS Order',
        help='Related POS order if message was sent from POS'
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
    
    # Enhanced logging fields
    api_request_data = fields.Text(
        string='API Request Data',
        help='JSON data sent to the WhatsApp API'
    )
    
    api_response_data = fields.Text(
        string='API Response Data',
        help='Full response received from the WhatsApp API'
    )
    
    api_status_code = fields.Integer(
        string='API Status Code',
        help='HTTP status code from the API response'
    )
    
    failure_reason = fields.Selection([
        ('invalid_phone', 'Invalid Phone Number'),
        ('not_whatsapp', 'Number Not on WhatsApp'),
        ('blocked_contact', 'Contact Blocked Us'),
        ('api_limit', 'API Rate Limit Exceeded'),
        ('template_rejected', 'Template Rejected'),
        ('media_failed', 'Media Upload Failed'),
        ('network_error', 'Network Connection Error'),
        ('auth_error', 'Authentication Error'),
        ('config_error', 'Configuration Error'),
        ('provider_error', 'Provider Service Error'),
        ('unknown_error', 'Unknown Error'),
    ], string='Failure Reason', help='Specific reason why the message failed')
    
    retry_count = fields.Integer(
        string='Retry Count',
        default=0,
        help='Number of times this message has been retried'
    )
    
    last_retry_date = fields.Datetime(
        string='Last Retry Date',
        help='When the message was last retried'
    )
    
    delivery_status = fields.Selection([
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('failed', 'Delivery Failed'),
        ('read', 'Read by Recipient'),
    ], string='Delivery Status', help='Actual delivery status from WhatsApp')
    
    webhook_data = fields.Text(
        string='Webhook Data',
        help='Delivery status updates received via webhooks'
    )
    
    # Computed fields for better display
    failure_reason_display = fields.Char(
        string='Failure Reason',
        compute='_compute_failure_reason_display',
        help='Human-readable description of the failure reason'
    )
    
    can_retry = fields.Boolean(
        string='Can Retry',
        compute='_compute_can_retry',
        help='Whether this message can be retried'
    )
    
    status_summary = fields.Char(
        string='Status Summary',
        compute='_compute_status_summary',
        help='Summary of message status with key details'
    )
    
    @api.depends('failure_reason')
    def _compute_failure_reason_display(self):
        """Compute human-readable failure reason"""
        reason_map = {
            'invalid_phone': 'Invalid or malformed phone number',
            'not_whatsapp': 'Phone number is not registered on WhatsApp',
            'blocked_contact': 'Contact has blocked this WhatsApp Business number',
            'api_limit': 'API rate limit exceeded - too many requests',
            'template_rejected': 'Message template was rejected by WhatsApp',
            'media_failed': 'Media file upload or processing failed',
            'network_error': 'Network connection error - check internet connectivity',
            'auth_error': 'Authentication failed - check API credentials',
            'config_error': 'WhatsApp configuration is missing or invalid',
            'provider_error': 'WhatsApp provider service error - try again later',
            'unknown_error': 'Unknown error occurred - check logs for details',
        }
        
        for record in self:
            record.failure_reason_display = reason_map.get(record.failure_reason, 'No error')
    
    @api.depends('state', 'retry_count')
    def _compute_can_retry(self):
        """Compute if message can be retried"""
        for record in self:
            # Allow retry for failed messages, but limit to 3 retries
            record.can_retry = record.state == 'failed' and record.retry_count < 3
    
    @api.depends('state', 'delivery_status', 'failure_reason', 'retry_count')
    def _compute_status_summary(self):
        """Compute status summary for quick overview"""
        for record in self:
            if record.state == 'draft':
                record.status_summary = 'Ready to send'
            elif record.state == 'sending':
                record.status_summary = 'Sending to WhatsApp API...'
            elif record.state == 'sent':
                if record.delivery_status == 'delivered':
                    record.status_summary = 'Successfully delivered'
                elif record.delivery_status == 'read':
                    record.status_summary = 'Delivered and read'
                elif record.delivery_status == 'failed':
                    record.status_summary = 'Sent but delivery failed'
                else:
                    record.status_summary = 'Sent - delivery status pending'
            elif record.state == 'failed':
                retry_info = f" (Retried {record.retry_count}x)" if record.retry_count > 0 else ""
                record.status_summary = f'Failed: {record.failure_reason_display}{retry_info}'
            else:
                record.status_summary = record.state.title()
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update phone number when partner changes"""
        if self.partner_id and self.partner_id.mobile:
            self.phone_number = self.partner_id.mobile
    
    def _safe_json_dumps(self, data, indent=2):
        """Safely serialize data to JSON, handling circular references"""
        def default_serializer(obj):
            """Custom serializer for non-serializable objects"""
            if hasattr(obj, '__dict__'):
                return f"<{type(obj).__name__} object>"
            return str(obj)
        
        try:
            return json.dumps(data, indent=indent, default=default_serializer)
        except (TypeError, ValueError) as e:
            _logger.warning(f"JSON serialization warning: {str(e)}")
            # Fallback: convert to string representation
            return json.dumps(str(data), indent=indent)

    def action_send_message(self):
        """Send the WhatsApp message"""
        self.ensure_one()
        
        if self.state != 'draft':
            raise UserError("Only draft messages can be sent")
        
        # Prepare request data for logging
        request_data = {
            'phone_number': self.phone_number,
            'message_type': self.message_type,
            'content': self.content,
            'template_name': self.template_name,
            'template_variables': self.template_variables,
            'timestamp': fields.Datetime.now().isoformat()
        }
        
        try:
            # Get configuration
            config = self.config_id or self.env['whatsapp.config'].get_default_config()
            if not config:
                self._log_failure('config_error', "No WhatsApp configuration found. Please configure a provider first.", request_data)
                raise UserError("No WhatsApp configuration found. Please configure a provider first.")
            
            # Dynamically import the WhatsApp service to avoid module loading conflicts
            import importlib
            import os
            services_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'services', 'whatsapp_service')
            spec = importlib.util.spec_from_file_location("whatsapp_service", services_path + '.py')
            whatsapp_service_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(whatsapp_service_module)
            WhatsAppService = whatsapp_service_module.WhatsAppService
            
            # Initialize service
            service = WhatsAppService(config_record=config)
            
            # Update state and log request
            self.write({
                'state': 'sending',
                'config_id': config.id,
                'api_request_data': self._safe_json_dumps(request_data)
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
                    self._log_failure('media_failed', "File attachment is required for this message type", request_data)
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
            
            # Safely extract and log debug information
            debug_data_to_log = None
            if result:
                # Create a clean copy of result data for logging, excluding circular references
                safe_result = {
                    'success': result.get('success'),
                    'message_id': result.get('message_id'),
                    'status': result.get('status'),
                    'error': result.get('error'),
                    'error_code': result.get('error_code'),
                    'status_code': result.get('status_code')
                }
                
                # Safely add provider response if it exists
                provider_response = result.get('provider_response')
                if provider_response:
                    try:
                        # Only include serializable parts of provider response
                        safe_provider_response = {}
                        for key, value in provider_response.items():
                            if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                                safe_provider_response[key] = value
                            else:
                                safe_provider_response[key] = str(value)
                        safe_result['provider_response'] = safe_provider_response
                    except Exception as e:
                        _logger.warning(f"Could not serialize provider response: {str(e)}")
                        safe_result['provider_response'] = str(provider_response)
                
                # Log the safe result data
                debug_data_to_log = self._safe_json_dumps(safe_result)
                
                # Also update request data with debug info if available
                debug_info = result.get('debug_info')
                if debug_info:
                    safe_debug_info = {}
                    try:
                        # Safely extract only serializable debug information
                        if 'phone_validation' in debug_info:
                            safe_debug_info['phone_validation'] = debug_info['phone_validation']
                        if 'api_request' in debug_info and isinstance(debug_info['api_request'], dict):
                            safe_debug_info['api_request'] = debug_info['api_request']
                        
                        enhanced_request_data = request_data.copy()
                        enhanced_request_data['debug_info'] = safe_debug_info
                        self.api_request_data = self._safe_json_dumps(enhanced_request_data)
                    except Exception as e:
                        _logger.warning(f"Could not serialize debug info: {str(e)}")
            
            # Update based on result
            if result and result.get('success'):
                # Update the record with safe serialized data
                update_values = {
                    'state': 'sent',
                    'sent_date': fields.Datetime.now(),
                    'provider_message_id': result.get('message_id'),
                    'delivery_status': 'pending'
                }
                
                if debug_data_to_log:
                    update_values['api_response_data'] = debug_data_to_log
                    
                if result.get('status_code'):
                    update_values['api_status_code'] = result.get('status_code', 0)
                
                self.write(update_values)
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Message Sent Successfully',
                        'message': f'WhatsApp message sent to {self.phone_number}. Check WhatsApp Logs for delivery tracking. Message ID: {result.get("message_id", "N/A")}',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Unknown error'
                failure_reason = self._determine_failure_reason(result)
                self._log_failure(failure_reason, error_msg, request_data, result)
                raise UserError(f"Failed to send message: {error_msg}")
                
        except Exception as e:
            error_msg = str(e)
            _logger.error(f"Error sending WhatsApp message: {error_msg}")
            failure_reason = self._determine_failure_reason_from_exception(e)
            self._log_failure(failure_reason, error_msg, request_data)
            raise UserError(f"Error sending message: {error_msg}")
    
    def _log_failure(self, failure_reason, error_msg, request_data, response_data=None):
        """Log failure details"""
        update_values = {
            'state': 'failed',
            'error_message': error_msg,
            'failure_reason': failure_reason,
            'api_request_data': self._safe_json_dumps(request_data),
            'api_status_code': response_data.get('status_code', 0) if response_data else 0
        }
        
        if response_data:
            # Create a safe copy of response data for logging
            safe_response_data = {}
            try:
                for key, value in response_data.items():
                    if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        safe_response_data[key] = value
                    else:
                        safe_response_data[key] = str(value)
                update_values['api_response_data'] = self._safe_json_dumps(safe_response_data)
            except Exception as e:
                _logger.warning(f"Could not serialize response data: {str(e)}")
                update_values['api_response_data'] = self._safe_json_dumps(str(response_data))
        
        self.write(update_values)
    
    def _determine_failure_reason(self, result):
        """Determine failure reason from API result"""
        if not result:
            return 'unknown_error'
        
        error_msg = result.get('error', '').lower()
        status_code = result.get('status_code', 0)
        error_code = result.get('error_code')
        error_type = result.get('error_type', '')
        
        # Twilio-specific error codes
        if error_code:
            twilio_error_map = {
                '21211': 'invalid_phone',  # Invalid 'To' phone number
                '21214': 'invalid_phone',  # 'To' phone number cannot be reached
                '21610': 'not_whatsapp',   # Phone number is not WhatsApp enabled
                '21408': 'api_limit',      # Permission to send an SMS or MMS has not been enabled for the region
                '21617': 'blocked_contact', # Contact has blocked the number
                '21619': 'api_limit',      # SMS or MMS message body exceeds character limit
                '30007': 'network_error',  # Message delivery: unknown error
                '30008': 'provider_error', # Message delivery: unknown error
            }
            if str(error_code) in twilio_error_map:
                return twilio_error_map[str(error_code)]
        
        # Meta-specific error analysis
        if error_type:
            meta_error_map = {
                'OAuthException': 'auth_error',
                'GraphMethodException': 'config_error',
                'Application request limit reached': 'api_limit',
                'Unsupported post request': 'config_error',
            }
            for error_pattern, reason in meta_error_map.items():
                if error_pattern.lower() in error_type.lower():
                    return reason
        
        # HTTP status code analysis
        if status_code == 401:
            return 'auth_error'
        elif status_code == 403:
            return 'blocked_contact'
        elif status_code == 429:
            return 'api_limit'
        elif status_code >= 500:
            return 'provider_error'
        
        # Content-based error analysis
        error_patterns = {
            'invalid phone': 'invalid_phone',
            'not on whatsapp': 'not_whatsapp',
            'not registered': 'not_whatsapp',
            'blocked': 'blocked_contact',
            'template': 'template_rejected',
            'media': 'media_failed',
            'file': 'media_failed',
            'attachment': 'media_failed',
            'rate limit': 'api_limit',
            'limit exceeded': 'api_limit',
            'authentication': 'auth_error',
            'unauthorized': 'auth_error',
            'configuration': 'config_error',
            'network': 'network_error',
            'connection': 'network_error',
            'timeout': 'network_error',
        }
        
        for pattern, reason in error_patterns.items():
            if pattern in error_msg:
                return reason
        
        return 'unknown_error'
    
    def _determine_failure_reason_from_exception(self, exception):
        """Determine failure reason from Python exception"""
        error_msg = str(exception).lower()
        
        if 'connection' in error_msg or 'network' in error_msg:
            return 'network_error'
        elif 'authentication' in error_msg or 'auth' in error_msg:
            return 'auth_error'
        elif 'configuration' in error_msg or 'config' in error_msg:
            return 'config_error'
        elif 'file' in error_msg or 'attachment' in error_msg:
            return 'media_failed'
        else:
            return 'unknown_error'
    
    def action_retry_send(self):
        """Retry sending a failed message"""
        self.ensure_one()
        if self.state == 'failed':
            self.write({
                'state': 'draft',
                'retry_count': self.retry_count + 1,
                'last_retry_date': fields.Datetime.now(),
                'error_message': False,  # Clear previous error
                'failure_reason': False
            })
            return self.action_send_message()
        else:
            raise UserError("Only failed messages can be retried")

    def action_debug_delivery(self):
        """Run comprehensive delivery debugging for this message"""
        self.ensure_one()
        
        try:
            # Get configuration
            config = self.config_id or self.env['whatsapp.config'].get_default_config()
            if not config:
                raise UserError("No WhatsApp configuration found")
            
            # Dynamically import WhatsApp service
            import importlib
            import os
            services_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'services', 'whatsapp_service')
            spec = importlib.util.spec_from_file_location("whatsapp_service", services_path + '.py')
            whatsapp_service_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(whatsapp_service_module)
            WhatsAppService = whatsapp_service_module.WhatsAppService
            
            # Initialize service and run debug test
            service = WhatsAppService(config_record=config)
            debug_result = service.debug_delivery_test(
                self.phone_number, 
                f"🔍 Debug test for message: {self.subject}"
            )
            
            # Safely log debug results
            debug_data = {
                'timestamp': fields.Datetime.now().isoformat(),
                'message_id': self.id,
                'debug_summary': debug_result.get('debug', {}).get('steps', []) if debug_result.get('debug') else []
            }
            
            # Safely extract debug details
            safe_debug_result = {}
            try:
                if debug_result.get('debug'):
                    debug_info = debug_result['debug']
                    for key, value in debug_info.items():
                        if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                            safe_debug_result[key] = value
                        else:
                            safe_debug_result[key] = str(value)
            except Exception as e:
                _logger.warning(f"Could not serialize debug result: {str(e)}")
                safe_debug_result = {'error': 'Debug result serialization failed'}
            
            self.write({
                'api_request_data': self._safe_json_dumps(debug_data),
                'api_response_data': self._safe_json_dumps(safe_debug_result)
            })
            
            # Show results in a message
            if debug_result['success']:
                message = f"✅ Debug test successful!\n\nMessage ID: {debug_result.get('message_id')}\n\nCheck the API Request/Response Data fields for detailed debugging information."
                notification_type = 'success'
            else:
                error = debug_result.get('error', 'Unknown error')
                message = f"❌ Debug test failed: {error}\n\nCheck the API Request/Response Data fields for detailed troubleshooting information."
                notification_type = 'danger'
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'WhatsApp Delivery Debug Test',
                    'message': message,
                    'type': notification_type,
                    'sticky': True,
                }
            }
            
        except Exception as e:
            error_msg = str(e)
            _logger.error(f"Debug delivery test failed: {error_msg}")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Debug Test Error',
                    'message': f"Debug test failed: {error_msg}",
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
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
    
    def action_view_details(self):
        """Open detailed view of the message"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'WhatsApp Message Details: {self.subject}',
            'res_model': 'whatsapp.message',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('whatsapp_notify.view_whatsapp_message_form').id,
            'target': 'current',
        }