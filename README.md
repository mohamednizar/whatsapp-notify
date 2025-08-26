# WhatsApp Notify

A comprehensive WhatsApp messaging integration service for sending templated messages and file attachments through the WhatsApp Business API.

## Features

- 📱 **WhatsApp Business API Integration** - Support for Twilio WhatsApp API and Meta WhatsApp Business API
- 🔌 **Multiple Providers** - Extensible provider architecture supporting Twilio and Meta APIs
- 📝 **Templated Messages** - Built-in template engine with customizable message templates
- 📎 **File Attachments** - Send receipts, e-books, and other documents (PDF, EPUB, images)
- 🛠️ **Service Abstraction** - Clean API with methods like `sendMessage`, `sendReceipt`, `sendEbook`
- ⚙️ **Configuration Management** - Environment-based configuration for provider credentials
- 🧪 **CLI Interface** - Command-line tools for testing and integration
- 🌐 **REST API Server** - HTTP endpoints for web service integration
- ✅ **Error Handling** - Comprehensive error handling and validation
- 🧪 **Full Test Coverage** - Complete test suite with Jest

## Installation

```bash
npm install @ht2cloud/whatsapp-notify
```

## Quick Start

### 1. Configuration

Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

#### Option A: Using Twilio WhatsApp API

Edit `.env` with your Twilio credentials:

```env
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

#### Option B: Using Meta WhatsApp Business API

Edit `.env` with your Meta credentials:

```env
WHATSAPP_PROVIDER=meta
META_ACCESS_TOKEN=your_meta_access_token_here
META_PHONE_NUMBER_ID=your_phone_number_id_here
```

### 2. Basic Usage

```javascript
const WhatsAppNotificationService = require('@ht2cloud/whatsapp-notify');

const service = new WhatsAppNotificationService();

// Send a simple message
const result = await service.sendMessage('+1234567890', 'Hello from WhatsApp!');

// Send a templated message
const templateResult = await service.sendTemplatedMessage(
  '+1234567890',
  'welcome',
  { name: 'John Doe' }
);

// Send a receipt with PDF attachment
const receiptResult = await service.sendReceipt(
  '+1234567890',
  'Jane Smith',
  'ORDER-123',
  '$99.99',
  './receipt.pdf'
);

// Send an e-book
const ebookResult = await service.sendEbook(
  '+1234567890',
  'Alice Johnson',
  'The Great Adventure',
  './book.pdf'
);
```

## API Reference

### WhatsAppNotificationService

#### Methods

##### `sendMessage(to: string, body: string): Promise<SendMessageResult>`
Send a simple text message.

##### `sendTemplatedMessage(to: string, templateName: string, templateParams: Record<string, string>): Promise<SendMessageResult>`
Send a message using a predefined template.

##### `sendReceipt(to: string, customerName: string, orderNumber: string, amount: string, receiptFilePath: string): Promise<SendMessageResult>`
Send a receipt with PDF attachment.

##### `sendEbook(to: string, customerName: string, bookTitle: string, ebookFilePath: string): Promise<SendMessageResult>`
Send an e-book with PDF or EPUB attachment.

##### `sendMessageWithFiles(to: string, body: string, attachments: WhatsAppAttachment[]): Promise<SendMessageResult>`
Send a message with custom file attachments.

##### `getAvailableTemplates(): string[]`
Get list of available message templates.

##### `addTemplate(name: string, content: string, variables: string[]): void`
Add a custom message template.

##### `healthCheck(): Promise<{healthy: boolean, provider: string, error?: string}>`
Check service health and configuration.

## CLI Usage

The package includes a comprehensive CLI for testing and integration:

```bash
# Send a simple message
npm run cli send-message "+1234567890" "Hello from WhatsApp!"

# Send a templated message
npm run cli send-template "+1234567890" welcome name="John Doe"

# Send a receipt
npm run cli send-receipt "+1234567890" "Jane Smith" "ORDER-123" "$99.99" "./receipt.pdf"

# Send an e-book
npm run cli send-ebook "+1234567890" "Alice Johnson" "My Great Book" "./book.pdf"

# List available templates
npm run cli list-templates

# Check service health
npm run cli health-check
```

## REST API Server

Start the HTTP server for web service integration:

```bash
npm start
# or for development
npm run dev
```

The server runs on port 3000 by default and provides the following endpoints:

### Endpoints

- `GET /` - API documentation
- `GET /health` - Service health check
- `GET /templates` - List available templates
- `POST /send-message` - Send a simple message
- `POST /send-template` - Send a templated message
- `POST /send-receipt` - Send a receipt with attachment
- `POST /send-ebook` - Send an e-book with attachment

### Example API Requests

```bash
# Send a simple message
curl -X POST http://localhost:3000/send-message \
  -H "Content-Type: application/json" \
  -d '{"to": "+1234567890", "message": "Hello from API!"}'

# Send a templated message
curl -X POST http://localhost:3000/send-template \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+1234567890",
    "template": "welcome",
    "templateParams": {"name": "John Doe"}
  }'
```

## Built-in Templates

The service comes with several built-in templates:

- **welcome** - Welcome new users
- **receipt** - Order receipts with attachment
- **ebook** - E-book delivery messages
- **order_confirmation** - Order confirmation messages

You can also load custom templates from the `templates/` directory or add them programmatically.

## Supported File Types

For attachments, the following file types are supported:

- **Documents**: PDF, DOC, DOCX, TXT, EPUB
- **Images**: JPG, JPEG, PNG

Maximum file size: 16MB (configurable)

## Provider Support

The service supports multiple WhatsApp Business API providers:

### Twilio WhatsApp API ✅

A reliable third-party provider with simple integration:

```env
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token  
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

**Features:**
- Easy setup and integration
- Robust messaging capabilities
- File attachment support via media URLs
- Comprehensive error reporting

### Meta WhatsApp Business API ✅

Direct integration with Meta's official WhatsApp Business API:

```env
WHATSAPP_PROVIDER=meta
META_ACCESS_TOKEN=your_meta_access_token
META_PHONE_NUMBER_ID=your_phone_number_id
```

**Features:**
- Direct connection to WhatsApp Business Platform
- Lower costs for high-volume messaging
- Advanced template support
- Rich media and document sharing

### Provider Selection

Switch between providers by setting the `WHATSAPP_PROVIDER` environment variable:

```env
# Use Twilio (default)
WHATSAPP_PROVIDER=twilio

# Use Meta WhatsApp Business API
WHATSAPP_PROVIDER=meta
```

The architecture is designed to be extensible for additional providers.

## Error Handling

The service provides comprehensive error handling:

```javascript
const result = await service.sendMessage('+1234567890', 'Hello!');

if (result.success) {
  console.log('Message sent! ID:', result.messageId);
} else {
  console.error('Failed to send message:', result.error);
}
```

## Development

### Setup

```bash
git clone https://github.com/ht2cloud/whatsapp-notify.git
cd whatsapp-notify
npm install
```

### Build

```bash
npm run build
```

### Test

```bash
npm test
npm run test:watch  # Watch mode
```

### Lint

```bash
npm run lint
npm run lint:fix
```

## Examples

Check out the `examples/` directory for:

- **CLI Examples** (`examples/cli-examples.js`) - Demonstrates CLI usage
- **API Examples** (`examples/api-examples.js`) - Shows programmatic usage
- **Custom Templates** (`templates/`) - Sample template definitions

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `WHATSAPP_PROVIDER` | Provider to use (`twilio` or `meta`) | No | `twilio` |
| **Twilio Configuration** | | | |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | Yes (if using Twilio) | - |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | Yes (if using Twilio) | - |
| `TWILIO_WHATSAPP_FROM` | Twilio WhatsApp number | Yes (if using Twilio) | - |
| **Meta Configuration** | | | |
| `META_ACCESS_TOKEN` | Meta Access Token | Yes (if using Meta) | - |
| `META_PHONE_NUMBER_ID` | Meta Phone Number ID | Yes (if using Meta) | - |
| **General Configuration** | | | |
| `NODE_ENV` | Environment | No | `development` |
| `LOG_LEVEL` | Logging level | No | `info` |
| `PORT` | Server port | No | `3000` |

## License

MIT

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues and questions:

- 🐛 [Report bugs](https://github.com/ht2cloud/whatsapp-notify/issues)
- 💬 [Discussions](https://github.com/ht2cloud/whatsapp-notify/discussions)
- 📧 [Email support](mailto:support@ht2cloud.com)

---

Built with ❤️ by [ht2cloud](https://github.com/ht2cloud)