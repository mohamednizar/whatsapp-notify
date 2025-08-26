# -*- coding: utf-8 -*-

import requests
import json
import logging
import os
import tempfile
import base64
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)

class WhatsAppService:
    """
    WhatsApp service for Odoo integration
    Provides methods to send messages using Twilio or Meta APIs
    """
    
    def __init__(self, config_record=None):
        """Initialize the service with configuration"""
        self.config_record = config_record
        self.provider = config_record.provider if config_record else None
        self.test_mode = config_record.test_mode if config_record else False
        
    def _get_credentials(self):
        """Get credentials from config record"""
        if not self.config_record:
            raise UserError("No configuration provided")
        return self.config_record.get_credentials_dict()
    
    def test_connection(self):
        """Test the connection to the WhatsApp provider"""
        try:
            if self.provider == 'twilio':
                return self._test_twilio_connection()
            elif self.provider == 'meta':
                return self._test_meta_connection()
            else:
                return {'success': False, 'error': f'Unsupported provider: {self.provider}'}
        except Exception as e:
            _logger.error(f"Connection test failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _test_twilio_connection(self):
        """Test Twilio connection"""
        credentials = self._get_credentials()
        
        # Test by making a request to Twilio's API
        url = f"https://api.twilio.com/2010-04-01/Accounts/{credentials['account_sid']}.json"
        
        try:
            response = requests.get(
                url,
                auth=(credentials['account_sid'], credentials['auth_token']),
                timeout=10
            )
            
            if response.status_code == 200:
                return {'success': True}
            else:
                return {'success': False, 'error': f'Twilio API returned status {response.status_code}'}
                
        except requests.RequestException as e:
            return {'success': False, 'error': f'Connection failed: {str(e)}'}
    
    def _test_meta_connection(self):
        """Test Meta connection"""
        credentials = self._get_credentials()
        
        # Test by making a request to Meta's API
        url = f"https://graph.facebook.com/v18.0/{credentials['phone_number_id']}"
        headers = {
            'Authorization': f"Bearer {credentials['access_token']}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return {'success': True}
            else:
                return {'success': False, 'error': f'Meta API returned status {response.status_code}'}
                
        except requests.RequestException as e:
            return {'success': False, 'error': f'Connection failed: {str(e)}'}
    
    def send_message(self, phone_number, message):
        """Send a simple text message"""
        if self.test_mode:
            _logger.info(f"TEST MODE: Would send message to {phone_number}: {message}")
            return {'success': True, 'message_id': 'test_message_id'}
        
        try:
            if self.provider == 'twilio':
                return self._send_twilio_message(phone_number, message)
            elif self.provider == 'meta':
                return self._send_meta_message(phone_number, message)
            else:
                raise UserError(f'Unsupported provider: {self.provider}')
        except Exception as e:
            _logger.error(f"Error sending message: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _send_twilio_message(self, phone_number, message):
        """Send message via Twilio"""
        credentials = self._get_credentials()
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{credentials['account_sid']}/Messages.json"
        
        data = {
            'From': credentials['from_number'],
            'To': f"whatsapp:{phone_number}",
            'Body': message
        }
        
        response = requests.post(
            url,
            data=data,
            auth=(credentials['account_sid'], credentials['auth_token']),
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            return {'success': True, 'message_id': result.get('sid')}
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('message', f'HTTP {response.status_code}')
            return {'success': False, 'error': error_msg}
    
    def _send_meta_message(self, phone_number, message):
        """Send message via Meta API"""
        credentials = self._get_credentials()
        
        url = f"https://graph.facebook.com/v18.0/{credentials['phone_number_id']}/messages"
        
        headers = {
            'Authorization': f"Bearer {credentials['access_token']}",
            'Content-Type': 'application/json'
        }
        
        data = {
            'messaging_product': 'whatsapp',
            'to': phone_number.replace('+', '').replace(' ', ''),
            'type': 'text',
            'text': {'body': message}
        }
        
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id')
            return {'success': True, 'message_id': message_id}
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
            return {'success': False, 'error': error_msg}
    
    def send_templated_message(self, phone_number, template_name, variables):
        """Send a templated message"""
        # Get template from Odoo
        template_model = self.config_record.env['whatsapp.template']
        template = template_model.search([('name', '=', template_name)], limit=1)
        
        if not template:
            return {'success': False, 'error': f'Template "{template_name}" not found'}
        
        try:
            rendered_content = template.render_template(variables)
            return self.send_message(phone_number, rendered_content)
        except Exception as e:
            _logger.error(f"Error sending templated message: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def send_message_with_files(self, phone_number, message, file_paths):
        """Send a message with file attachments"""
        if self.test_mode:
            _logger.info(f"TEST MODE: Would send message with files to {phone_number}: {message}, files: {file_paths}")
            return {'success': True, 'message_id': 'test_message_with_files_id'}
        
        try:
            # Send the text message first
            text_result = self.send_message(phone_number, message)
            if not text_result.get('success'):
                return text_result
            
            # Then send attachments
            for file_path in file_paths:
                if os.path.exists(file_path):
                    file_result = self._send_file(phone_number, file_path)
                    if not file_result.get('success'):
                        _logger.warning(f"Failed to send file {file_path}: {file_result.get('error')}")
            
            return text_result
            
        except Exception as e:
            _logger.error(f"Error sending message with files: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _send_file(self, phone_number, file_path):
        """Send a file attachment"""
        try:
            if self.provider == 'twilio':
                return self._send_twilio_file(phone_number, file_path)
            elif self.provider == 'meta':
                return self._send_meta_file(phone_number, file_path)
            else:
                raise UserError(f'Unsupported provider: {self.provider}')
        except Exception as e:
            _logger.error(f"Error sending file: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _send_twilio_file(self, phone_number, file_path):
        """Send file via Twilio (requires publicly accessible URL)"""
        # For Twilio, we need to upload the file to a publicly accessible location
        # This is a simplified implementation - in production you'd want to use
        # a proper file hosting service or Twilio's media upload API
        return {'success': False, 'error': 'File upload not implemented for Twilio in this version'}
    
    def _send_meta_file(self, phone_number, file_path):
        """Send file via Meta API"""
        credentials = self._get_credentials()
        
        # First, upload the file to Meta
        upload_url = f"https://graph.facebook.com/v18.0/{credentials['phone_number_id']}/media"
        
        headers = {
            'Authorization': f"Bearer {credentials['access_token']}"
        }
        
        with open(file_path, 'rb') as file:
            files = {
                'file': file,
                'type': 'document',
                'messaging_product': 'whatsapp'
            }
            
            upload_response = requests.post(upload_url, headers=headers, files=files, timeout=60)
        
        if upload_response.status_code != 200:
            return {'success': False, 'error': f'File upload failed: {upload_response.text}'}
        
        upload_result = upload_response.json()
        media_id = upload_result.get('id')
        
        if not media_id:
            return {'success': False, 'error': 'No media ID returned from upload'}
        
        # Then send the message with the uploaded media
        send_url = f"https://graph.facebook.com/v18.0/{credentials['phone_number_id']}/messages"
        
        send_headers = {
            'Authorization': f"Bearer {credentials['access_token']}",
            'Content-Type': 'application/json'
        }
        
        send_data = {
            'messaging_product': 'whatsapp',
            'to': phone_number.replace('+', '').replace(' ', ''),
            'type': 'document',
            'document': {'id': media_id}
        }
        
        send_response = requests.post(send_url, headers=send_headers, json=send_data, timeout=30)
        
        if send_response.status_code == 200:
            result = send_response.json()
            message_id = result.get('messages', [{}])[0].get('id')
            return {'success': True, 'message_id': message_id}
        else:
            error_data = send_response.json() if send_response.text else {}
            error_msg = error_data.get('error', {}).get('message', f'HTTP {send_response.status_code}')
            return {'success': False, 'error': error_msg}
    
    def send_receipt(self, phone_number, customer_name, order_id, amount, file_path):
        """Send a receipt with PDF attachment"""
        variables = {
            'customer_name': customer_name,
            'order_id': order_id,
            'amount': amount
        }
        
        # Send templated message first
        result = self.send_templated_message(phone_number, 'receipt', variables)
        
        # Then send the file if message was successful
        if result.get('success') and file_path and os.path.exists(file_path):
            file_result = self._send_file(phone_number, file_path)
            if not file_result.get('success'):
                _logger.warning(f"Receipt text sent but file failed: {file_result.get('error')}")
        
        return result
    
    def send_ebook(self, phone_number, book_title, author, file_path):
        """Send an e-book with file attachment"""
        variables = {
            'book_title': book_title,
            'author': author
        }
        
        # Send templated message first
        result = self.send_templated_message(phone_number, 'ebook', variables)
        
        # Then send the file if message was successful
        if result.get('success') and file_path and os.path.exists(file_path):
            file_result = self._send_file(phone_number, file_path)
            if not file_result.get('success'):
                _logger.warning(f"E-book text sent but file failed: {file_result.get('error')}")
        
        return result