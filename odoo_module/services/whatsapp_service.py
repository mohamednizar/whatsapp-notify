# -*- coding: utf-8 -*-

import requests
import json
import logging
import os
import re
from datetime import datetime
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

    def validate_phone_number(self, phone_number):
        """
        Validate and normalize WhatsApp phone number
        Returns normalized number and validation details
        """
        debug_info = {
            'original_number': phone_number,
            'validation_steps': []
        }
        
        if not phone_number:
            debug_info['validation_steps'].append('❌ Empty phone number')
            return {'valid': False, 'debug': debug_info, 'error': 'Phone number is required'}
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', str(phone_number).strip())
        debug_info['validation_steps'].append(f'🔧 Cleaned number: {cleaned}')
        
        # Ensure it starts with +
        if not cleaned.startswith('+'):
            if len(cleaned) > 10:  # Likely international number without +
                cleaned = '+' + cleaned
                debug_info['validation_steps'].append(f'➕ Added + prefix: {cleaned}')
            else:
                debug_info['validation_steps'].append('❌ Number too short and no country code')
                return {'valid': False, 'debug': debug_info, 'error': 'Phone number must include country code (e.g., +1234567890)'}
        
        # Check length (international format should be 7-15 digits after +)
        digits_only = re.sub(r'[^\d]', '', cleaned)
        if len(digits_only) < 7:
            debug_info['validation_steps'].append(f'❌ Too short: {len(digits_only)} digits')
            return {'valid': False, 'debug': debug_info, 'error': f'Phone number too short: {len(digits_only)} digits (minimum 7)'}
        
        if len(digits_only) > 15:
            debug_info['validation_steps'].append(f'❌ Too long: {len(digits_only)} digits')
            return {'valid': False, 'debug': debug_info, 'error': f'Phone number too long: {len(digits_only)} digits (maximum 15)'}
        
        debug_info['validation_steps'].append(f'✅ Valid length: {len(digits_only)} digits')
        
        # Format for different providers
        provider_formats = {}
        if self.provider == 'twilio':
            provider_formats['twilio'] = f'whatsapp:{cleaned}'
        elif self.provider == 'meta':
            provider_formats['meta'] = digits_only  # Meta wants digits only
        
        debug_info['validation_steps'].append(f'📱 Provider formats: {provider_formats}')
        
        return {
            'valid': True,
            'normalized': cleaned,
            'digits_only': digits_only,
            'provider_formats': provider_formats,
            'debug': debug_info
        }

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

    def debug_delivery_test(self, phone_number, test_message="🧪 WhatsApp delivery test from Odoo"):
        """
        Comprehensive test to debug delivery issues
        Returns detailed information about the entire delivery process
        """
        debug_results = {
            'timestamp': datetime.now().isoformat(),
            'provider': self.provider,
            'test_mode': self.test_mode,
            'steps': []
        }
        
        try:
            # Step 1: Configuration validation
            debug_results['steps'].append('🔧 Validating configuration...')
            if not self.config_record:
                debug_results['steps'].append('❌ No configuration record found')
                return {'success': False, 'error': 'No configuration', 'debug': debug_results}
            
            # Step 2: Credentials check
            debug_results['steps'].append('🔑 Checking credentials...')
            try:
                credentials = self._get_credentials()
                debug_results['steps'].append('✅ Credentials loaded successfully')
            except Exception as e:
                debug_results['steps'].append(f'❌ Credentials error: {str(e)}')
                return {'success': False, 'error': f'Credentials error: {str(e)}', 'debug': debug_results}
            
            # Step 3: Connection test
            debug_results['steps'].append('🌐 Testing provider connection...')
            connection_result = self.test_connection()
            if connection_result['success']:
                debug_results['steps'].append('✅ Provider connection successful')
            else:
                debug_results['steps'].append(f'❌ Provider connection failed: {connection_result["error"]}')
                return {'success': False, 'error': f'Connection failed: {connection_result["error"]}', 'debug': debug_results}
            
            # Step 4: Phone number validation
            debug_results['steps'].append(f'📱 Validating phone number: {phone_number}')
            phone_validation = self.validate_phone_number(phone_number)
            if phone_validation['valid']:
                debug_results['steps'].append(f'✅ Phone number valid: {phone_validation["normalized"]}')
                debug_results['phone_validation'] = phone_validation
            else:
                debug_results['steps'].append(f'❌ Invalid phone number: {phone_validation["error"]}')
                return {'success': False, 'error': f'Invalid phone: {phone_validation["error"]}', 'debug': debug_results}
            
            # Step 5: Send test message
            debug_results['steps'].append('📤 Sending test message...')
            send_result = self.send_message(phone_number, test_message)
            
            if send_result.get('success'):
                debug_results['steps'].append(f'✅ Message sent successfully')
                debug_results['steps'].append(f'   Message ID: {send_result.get("message_id")}')
                debug_results['send_result'] = send_result
                
                # Step 6: Analysis and recommendations
                debug_results['steps'].append('🔍 Analyzing result...')
                recommendations = self._analyze_delivery_debug(send_result, phone_validation)
                debug_results['recommendations'] = recommendations
                debug_results['steps'].extend(recommendations)
                
                return {'success': True, 'message_id': send_result.get('message_id'), 'debug': debug_results}
            else:
                debug_results['steps'].append(f'❌ Message send failed: {send_result.get("error")}')
                debug_results['send_result'] = send_result
                
                # Failure analysis
                failure_analysis = self._analyze_delivery_failure(send_result)
                debug_results['failure_analysis'] = failure_analysis
                debug_results['steps'].extend(failure_analysis)
                
                return {'success': False, 'error': send_result.get('error'), 'debug': debug_results}
                
        except Exception as e:
            error_msg = str(e)
            debug_results['steps'].append(f'❌ Unexpected error: {error_msg}')
            _logger.error(f"Debug delivery test failed: {error_msg}")
            return {'success': False, 'error': error_msg, 'debug': debug_results}

    def _analyze_delivery_debug(self, send_result, phone_validation):
        """Analyze successful send for potential delivery issues"""
        recommendations = []
        
        recommendations.append('✅ Message was successfully accepted by the API')
        
        # Provider-specific analysis
        if self.provider == 'twilio':
            status = send_result.get('status', 'unknown')
            if status in ['accepted', 'queued']:
                recommendations.append('📋 Message is queued for delivery by Twilio')
                recommendations.append('⏱️  Delivery usually takes 1-10 seconds')
            elif status == 'sent':
                recommendations.append('🚀 Message has been sent to WhatsApp servers')
            elif status in ['failed', 'undelivered']:
                recommendations.append('⚠️  Warning: Twilio reports delivery issues')
                
        elif self.provider == 'meta':
            recommendations.append('📋 Message accepted by Meta WhatsApp Business API')
            recommendations.append('⏱️  Delivery status updates may take 1-30 seconds')
        
        # Phone number analysis
        digits = phone_validation['digits_only']
        if len(digits) == 10:
            recommendations.append('📱 10-digit number detected - ensure country code is correct')
        
        # General recommendations
        recommendations.extend([
            '🔍 Common delivery failure reasons:',
            '   • Number not registered on WhatsApp',
            '   • Contact has blocked your business number',
            '   • Phone is turned off or has no internet',
            '   • WhatsApp servers experiencing issues',
            '💡 To confirm delivery:',
            '   • Check your WhatsApp Business dashboard',
            '   • Verify number is active on WhatsApp',
            '   • Test with a known working number first'
        ])
        
        return recommendations

    def _analyze_delivery_failure(self, send_result):
        """Analyze failed send for troubleshooting"""
        analysis = []
        
        error_msg = send_result.get('error', '').lower()
        error_code = send_result.get('error_code')
        status_code = send_result.get('status_code', 0)
        
        analysis.append('❌ Message delivery failed - analyzing cause:')
        
        # Common error patterns
        if status_code == 401:
            analysis.extend([
                '🔑 Authentication Error (401):',
                '   • Check your API credentials',
                '   • Verify access token is not expired',
                '   • Ensure account has WhatsApp permissions'
            ])
        elif status_code == 403:
            analysis.extend([
                '🚫 Permission Error (403):',
                '   • Account may not have WhatsApp messaging permissions',
                '   • Phone number may not be verified',
                '   • Check billing and account status'
            ])
        elif status_code == 429:
            analysis.extend([
                '⏰ Rate Limit Error (429):',
                '   • Too many messages sent recently',
                '   • Wait and try again later',
                '   • Consider upgrading your API plan'
            ])
        elif 'invalid' in error_msg and 'phone' in error_msg:
            analysis.extend([
                '📱 Invalid Phone Number:',
                '   • Ensure number includes country code',
                '   • Format: +1234567890',
                '   • Number must be registered on WhatsApp'
            ])
        elif 'not on whatsapp' in error_msg:
            analysis.extend([
                '📵 Number Not on WhatsApp:',
                '   • Recipient has not registered for WhatsApp',
                '   • Ask recipient to install and activate WhatsApp',
                '   • Verify the phone number is correct'
            ])
        elif 'blocked' in error_msg:
            analysis.extend([
                '🚫 Contact Blocked:',
                '   • Recipient has blocked your business number',
                '   • Contact must unblock to receive messages',
                '   • Check WhatsApp Business dashboard for blocks'
            ])
        elif status_code >= 500:
            analysis.extend([
                '🔧 Server Error (5xx):',
                '   • WhatsApp/Provider servers are having issues',
                '   • Try again in a few minutes',
                '   • Check provider status page'
            ])
        else:
            analysis.extend([
                '❓ Unknown Error:',
                '   • Check API documentation for error details',
                '   • Verify all configuration settings',
                '   • Contact provider support if issue persists'
            ])
        
        return analysis

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
        """Send a simple text message with comprehensive debugging"""
        debug_info = {
            'provider': self.provider,
            'test_mode': self.test_mode,
            'phone_validation': None,
            'api_request': None,
            'api_response': None,
            'final_result': None
        }
        
        # Validate phone number first
        phone_validation = self.validate_phone_number(phone_number)
        debug_info['phone_validation'] = phone_validation
        
        if not phone_validation['valid']:
            _logger.error(f"❌ Invalid phone number: {phone_validation['error']}")
            _logger.debug(f"Phone validation debug: {json.dumps(phone_validation['debug'], indent=2)}")
            return {
                'success': False, 
                'error': phone_validation['error'],
                'debug_info': debug_info
            }
        
        _logger.info(f"✅ Phone number validated: {phone_validation['normalized']}")
        
        if self.test_mode:
            _logger.info(f"🧪 TEST MODE: Would send message to {phone_number}: {message}")
            debug_info['final_result'] = {'success': True, 'message_id': 'test_message_id', 'test_mode': True}
            return {'success': True, 'message_id': 'test_message_id', 'debug_info': debug_info}
            
        try:
            if self.provider == 'twilio':
                result = self._send_twilio_message_debug(phone_validation, message, debug_info)
            elif self.provider == 'meta':
                result = self._send_meta_message_debug(phone_validation, message, debug_info)
            else:
                error_msg = f'Unsupported provider: {self.provider}'
                _logger.error(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg, 'debug_info': debug_info}
                
            debug_info['final_result'] = result
            return result
            
        except Exception as e:
            error_msg = str(e)
            _logger.error(f"❌ Exception sending message: {error_msg}")
            debug_info['exception'] = error_msg
            return {'success': False, 'error': error_msg, 'debug_info': debug_info}

    def _send_twilio_message_debug(self, phone_validation, message, debug_info):
        """Send message via Twilio with detailed debugging"""
        _logger.info("🔵 Sending via Twilio API...")
        
        credentials = self._get_credentials()
        twilio_number = phone_validation['provider_formats']['twilio']
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{credentials['account_sid']}/Messages.json"
        data = {
            'From': credentials['from_number'],
            'To': twilio_number,
            'Body': message
        }
        
        debug_info['api_request'] = {
            'url': url,
            'method': 'POST',
            'data': data,
            'auth_user': credentials['account_sid']
        }
        
        _logger.info(f"📤 Twilio API Request:")
        _logger.info(f"   URL: {url}")
        _logger.info(f"   From: {data['From']}")
        _logger.info(f"   To: {data['To']}")
        _logger.info(f"   Body: {data['Body'][:100]}...")
        
        try:
            response = requests.post(
                url, 
                data=data,
                auth=(credentials['account_sid'], credentials['auth_token']),
                timeout=30
            )
            
            # Log full response for debugging
            debug_info['api_response'] = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.text
            }
            
            _logger.info(f"📥 Twilio API Response:")
            _logger.info(f"   Status: {response.status_code}")
            _logger.info(f"   Response: {response.text}")
            
            if response.status_code == 201:
                result = response.json()
                message_id = result.get('sid')
                message_status = result.get('status', 'unknown')
                
                _logger.info(f"✅ Twilio Success:")
                _logger.info(f"   Message ID: {message_id}")
                _logger.info(f"   Status: {message_status}")
                _logger.info(f"   Price: {result.get('price', 'N/A')}")
                
                # Check for any warning signs in the response
                if message_status in ['failed', 'undelivered']:
                    _logger.warning(f"⚠️ Twilio message status indicates potential delivery issue: {message_status}")
                
                return {
                    'success': True, 
                    'message_id': message_id,
                    'status': message_status,
                    'provider_response': result,
                    'debug_info': debug_info
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('message', f'HTTP {response.status_code}')
                error_code = error_data.get('code')
                
                _logger.error(f"❌ Twilio Error:")
                _logger.error(f"   Status: {response.status_code}")
                _logger.error(f"   Error: {error_msg}")
                _logger.error(f"   Code: {error_code}")
                
                return {
                    'success': False, 
                    'error': error_msg,
                    'error_code': error_code,
                    'status_code': response.status_code,
                    'provider_response': error_data,
                    'debug_info': debug_info
                }
                
        except requests.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            _logger.error(f"❌ Twilio Network Error: {error_msg}")
            debug_info['network_error'] = error_msg
            return {'success': False, 'error': error_msg, 'debug_info': debug_info}

    def _send_meta_message_debug(self, phone_validation, message, debug_info):
        """Send message via Meta API with detailed debugging"""
        _logger.info("🟢 Sending via Meta API...")
        
        credentials = self._get_credentials()
        meta_number = phone_validation['provider_formats']['meta']
        
        url = f"https://graph.facebook.com/{self.META_API_VERSION}/{credentials['phone_number_id']}/messages"
        headers = {
            'Authorization': f"Bearer {credentials['access_token']}",
            'Content-Type': 'application/json'
        }
        data = {
            'messaging_product': 'whatsapp',
            'to': meta_number,
            'type': 'text',
            'text': {'body': message}
        }
        
        debug_info['api_request'] = {
            'url': url,
            'method': 'POST',
            'headers': {k: v for k, v in headers.items() if k != 'Authorization'},
            'headers_note': 'Authorization header hidden for security',
            'data': data
        }
        
        _logger.info(f"📤 Meta API Request:")
        _logger.info(f"   URL: {url}")
        _logger.info(f"   To: {data['to']}")
        _logger.info(f"   Message: {data['text']['body'][:100]}...")
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            # Log full response for debugging
            debug_info['api_response'] = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.text
            }
            
            _logger.info(f"📥 Meta API Response:")
            _logger.info(f"   Status: {response.status_code}")
            _logger.info(f"   Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                messages = result.get('messages', [])
                
                if messages:
                    message_id = messages[0].get('id')
                    message_status = messages[0].get('message_status', 'sent')
                    
                    _logger.info(f"✅ Meta Success:")
                    _logger.info(f"   Message ID: {message_id}")
                    _logger.info(f"   Status: {message_status}")
                    
                    # Check for any error indicators in the response
                    errors = result.get('error')
                    if errors:
                        _logger.warning(f"⚠️ Meta API returned errors: {errors}")
                    
                    return {
                        'success': True, 
                        'message_id': message_id,
                        'status': message_status,
                        'provider_response': result,
                        'debug_info': debug_info
                    }
                else:
                    _logger.error(f"❌ Meta API returned no messages in response")
                    return {
                        'success': False, 
                        'error': 'No messages returned in API response',
                        'provider_response': result,
                        'debug_info': debug_info
                    }
            else:
                error_data = response.json() if response.text else {}
                error_info = error_data.get('error', {})
                error_msg = error_info.get('message', f'HTTP {response.status_code}')
                error_code = error_info.get('code')
                error_type = error_info.get('type')
                
                _logger.error(f"❌ Meta API Error:")
                _logger.error(f"   Status: {response.status_code}")
                _logger.error(f"   Error: {error_msg}")
                _logger.error(f"   Code: {error_code}")
                _logger.error(f"   Type: {error_type}")
                
                return {
                    'success': False, 
                    'error': error_msg,
                    'error_code': error_code,
                    'error_type': error_type,
                    'status_code': response.status_code,
                    'provider_response': error_data,
                    'debug_info': debug_info
                }
                
        except requests.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            _logger.error(f"❌ Meta Network Error: {error_msg}")
            debug_info['network_error'] = error_msg
            return {'success': False, 'error': error_msg, 'debug_info': debug_info}

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
