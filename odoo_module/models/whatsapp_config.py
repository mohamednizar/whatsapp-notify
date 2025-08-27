# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

PROVIDER_CHOICES = [
    ('twilio', 'Twilio WhatsApp API'),
    ('meta', 'Meta WhatsApp Business API'),
]

class WhatsAppConfig(models.Model):
    _name = 'whatsapp.config'
    _description = 'WhatsApp Provider Configuration'
    _rec_name = 'name'

    name = fields.Char(
        string='Configuration Name',
        required=True,
        help='Name for this WhatsApp configuration'
    )
    
    provider = fields.Selection(
        PROVIDER_CHOICES,
        string='Provider',
        required=True,
        default='twilio',
        help='WhatsApp API provider to use'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this configuration is active'
    )
    
    is_default = fields.Boolean(
        string='Default Configuration',
        default=False,
        help='Use this as the default configuration'
    )
    
    # Twilio Configuration
    twilio_account_sid = fields.Char(
        string='Twilio Account SID',
        help='Your Twilio Account SID'
    )
    
    twilio_auth_token = fields.Char(
        string='Twilio Auth Token',
        help='Your Twilio Auth Token'
    )
    
    twilio_whatsapp_from = fields.Char(
        string='Twilio WhatsApp From Number',
        default='whatsapp:+14155238886',
        help='Twilio WhatsApp sender number (format: whatsapp:+1234567890)'
    )
    
    # Meta Configuration
    meta_access_token = fields.Char(
        string='Meta Access Token',
        help='Meta WhatsApp Business API access token'
    )
    
    meta_phone_number_id = fields.Char(
        string='Meta Phone Number ID',
        help='Meta WhatsApp Business phone number ID'
    )
    
    # Additional settings
    test_mode = fields.Boolean(
        string='Test Mode',
        default=False,
        help='Enable test mode (logs messages without sending)'
    )
    
    @api.constrains('is_default')
    def _check_single_default(self):
        """Ensure only one configuration is marked as default"""
        for record in self:
            if record.is_default:
                other_defaults = self.search([
                    ('id', '!=', record.id),
                    ('is_default', '=', True)
                ])
                if other_defaults:
                    other_defaults.write({'is_default': False})
    
    @api.constrains('provider', 'twilio_account_sid', 'twilio_auth_token', 'meta_access_token', 'meta_phone_number_id')
    def _check_provider_credentials(self):
        """Validate required credentials for each provider"""
        for record in self:
            if record.provider == 'twilio':
                if not record.twilio_account_sid or not record.twilio_auth_token:
                    raise ValidationError(
                        "Twilio provider requires Account SID and Auth Token"
                    )
            elif record.provider == 'meta':
                if not record.meta_access_token or not record.meta_phone_number_id:
                    raise ValidationError(
                        "Meta provider requires Access Token and Phone Number ID"
                    )
    
    @api.model
    def get_default_config(self):
        """Get the default configuration"""
        default_config = self.search([('is_default', '=', True), ('active', '=', True)], limit=1)
        if not default_config:
            # If no default is set, get the first active configuration
            default_config = self.search([('active', '=', True)], limit=1)
        return default_config
    
    def get_credentials_dict(self):
        """Get credentials as a dictionary for the service"""
        self.ensure_one()
        if self.provider == 'twilio':
            return {
                'account_sid': self.twilio_account_sid,
                'auth_token': self.twilio_auth_token,
                'from_number': self.twilio_whatsapp_from,
            }
        elif self.provider == 'meta':
            return {
                'access_token': self.meta_access_token,
                'phone_number_id': self.meta_phone_number_id,
            }
        return {}
    
    def test_connection(self):
        """Test the WhatsApp provider connection"""
        self.ensure_one()
        try:
            # Import the WhatsApp service
            from ..services.whatsapp_service import WhatsAppService
            
            service = WhatsAppService(config_record=self)
            result = service.test_connection()
            
            if result.get('success'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Connection Test Successful',
                        'message': 'WhatsApp provider connection is working correctly.',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(f"Connection test failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            _logger.error(f"WhatsApp connection test failed: {str(e)}")
            raise UserError(f"Connection test failed: {str(e)}")