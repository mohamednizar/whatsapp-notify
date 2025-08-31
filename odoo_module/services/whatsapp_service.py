# -*- coding: utf-8 -*-

import requests
import json
import logging
import os
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class WhatsAppService:
    """
    WhatsApp service for Odoo integration
    Provides methods to send messages using Twilio or Meta APIs
    """

    META_API_VERSION = "v22.0"  # ✅ Upgraded to Meta API v22.0

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
        url = f"https://graph.facebook.com/{self.META_API_VERSION}/{credentials['phone_number_id']}"
        headers = {'Authorization': f"Bearer {credentials['access_token']}"}
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
        response = requests.post(url, data=data,
                                 auth=(credentials['account_sid'], credentials['auth_token']),
                                 timeout=30)
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
        url = f"https://graph.facebook.com/{self.META_API_VERSION}/{credentials['phone_number_id']}/messages"
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
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id')
            return {'success': True, 'message_id': message_id}
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
            return {'success': False, 'error': error_msg}

    def _send_meta_file(self, phone_number, file_path):
        """Send file via Meta API"""
        credentials = self._get_credentials()
        # Upload file first
        upload_url = f"https://graph.facebook.com/{self.META_API_VERSION}/{credentials['phone_number_id']}/media"
        headers = {'Authorization': f"Bearer {credentials['access_token']}"}
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
        # Send media message
        send_url = f"https://graph.facebook.com/{self.META_API_VERSION}/{credentials['phone_number_id']}/messages"
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
