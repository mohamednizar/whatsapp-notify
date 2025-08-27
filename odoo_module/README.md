# WhatsApp Notify - Odoo Module

## Overview

This Odoo module provides comprehensive WhatsApp messaging integration for Odoo CE 17.0, enabling businesses to send professional WhatsApp messages directly from their Odoo system.

## Features

### 🔌 **Multi-Provider Support**
- **Twilio WhatsApp API** integration
- **Meta WhatsApp Business API** integration  
- Easy provider switching via configuration

### 📝 **Template System**
- Pre-built templates for common use cases
- Custom template creation with variable substitution
- Template preview functionality
- JSON-based variable definitions

### 📱 **Message Types**
- Simple text messages
- Template-based messages
- Receipt delivery with PDF attachments
- E-book distribution with file attachments
- Custom messages with multiple file attachments

### 🎯 **Odoo Integration**
- **Contact Integration**: Send messages directly from contact records
- **Message Logging**: Complete message history and tracking
- **Status Tracking**: Real-time message status updates (sent, delivered, read, failed)
- **Wizard Interfaces**: User-friendly message composition wizards
- **Security Groups**: Role-based access control for WhatsApp functionality

### 🛡️ **Security & Permissions**
- **WhatsApp Manager**: Full access to configuration and messages
- **WhatsApp User**: Can send messages but cannot modify configuration
- **Record Rules**: Proper access control for sensitive data

## Installation

### 1. Dependencies
Ensure these Python packages are installed:
```bash
pip install requests python-dotenv
```

### 2. Module Installation
1. Copy the `odoo_module` folder to your Odoo addons directory
2. Rename it to `whatsapp_notify` 
3. Update your Odoo apps list
4. Install the "WhatsApp Notify Integration" module

### 3. Configuration

#### Option A: Twilio WhatsApp API
1. Go to **WhatsApp → Configuration → Providers**
2. Create a new configuration:
   - **Name**: "Production Twilio"
   - **Provider**: Twilio WhatsApp API
   - **Account SID**: Your Twilio Account SID
   - **Auth Token**: Your Twilio Auth Token
   - **From Number**: Your Twilio WhatsApp number (e.g., `whatsapp:+14155238886`)
3. Set as **Default Configuration**
4. Click **Test Connection** to verify

#### Option B: Meta WhatsApp Business API
1. Go to **WhatsApp → Configuration → Providers**
2. Create a new configuration:
   - **Name**: "Production Meta"
   - **Provider**: Meta WhatsApp Business API  
   - **Access Token**: Your Meta permanent access token
   - **Phone Number ID**: Your WhatsApp Business phone number ID
3. Set as **Default Configuration**
4. Click **Test Connection** to verify

## Usage

### Sending Messages from Contacts
1. Open any contact record with a mobile number
2. Click **Send WhatsApp** for a simple message
3. Click **Send Template** for template-based messages
4. Use the **WhatsApp Messages** smart button to view message history

### Using Message Wizards
- **WhatsApp → Messages → Send Message**: Send custom text messages
- **WhatsApp → Messages → Send Template**: Send template-based messages

### Managing Templates
- **WhatsApp → Configuration → Templates**: Create and manage message templates
- Use variables like `{{name}}`, `{{order_id}}`, `{{amount}}` in your templates
- Preview templates before sending

### Viewing Message History
- **WhatsApp → Messages → All Messages**: View all sent messages
- Filter by status, message type, or date
- Retry failed messages

## Template Examples

### Welcome Message
```
Hello {{name}}! Welcome to our service. We're excited to have you on board!
```

### Order Confirmation
```
Hi {{customer_name}}, your order {{order_id}} for {{amount}} has been confirmed. Expected delivery: {{delivery_date}}.
```

### Receipt Delivery
```
Hi {{customer_name}}, your receipt for order {{order_id}} ({{amount}}) is attached. Thank you for your business!
```

## API Integration

The module provides Python methods that can be called from other Odoo modules:

```python
# Send a simple message
message = self.env['whatsapp.message'].create_from_partner(
    partner_id=partner.id,
    message_type='text',
    content='Hello from Odoo!'
)
message.action_send_message()

# Send a templated message
message = self.env['whatsapp.message'].create_from_partner(
    partner_id=partner.id,
    message_type='template',
    template_name='welcome',
    template_vars={'name': partner.name}
)
message.action_send_message()
```

## Configuration Examples

### Environment Variables (Optional)
You can also set configuration via environment variables:

```bash
# For Twilio
export WHATSAPP_PROVIDER=twilio
export TWILIO_ACCOUNT_SID=your_account_sid
export TWILIO_AUTH_TOKEN=your_auth_token
export TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# For Meta
export WHATSAPP_PROVIDER=meta
export META_ACCESS_TOKEN=your_access_token
export META_PHONE_NUMBER_ID=your_phone_number_id
```

## Troubleshooting

### Common Issues

1. **Messages not sending**
   - Check provider configuration
   - Verify credentials using "Test Connection"
   - Ensure phone numbers include country code (e.g., +1234567890)

2. **File attachments failing**
   - Meta API: Files are uploaded directly to Meta
   - Twilio: Requires publicly accessible file URLs (not yet implemented)
   - Check file size limits (usually 16MB for Meta)

3. **Template variables not working**
   - Ensure template variables are valid JSON
   - Check that all required variables are provided
   - Use the preview function to test templates

### Log Files
Check Odoo logs for detailed error messages:
```bash
tail -f /var/log/odoo/odoo.log | grep whatsapp
```

## Support

For issues and questions:
1. Check the Odoo logs for error details
2. Verify your WhatsApp provider setup
3. Test with the demo data provided
4. Review the original TypeScript implementation at: https://github.com/ht2cloud/whatsapp-notify

## License

This module is licensed under LGPL-3, same as Odoo CE.

## Credits

Based on the WhatsApp Notify integration library by ht2cloud.
Adapted for Odoo CE 17.0 integration.