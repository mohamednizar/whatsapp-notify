import * as http from 'http';
import * as url from 'url';
import * as querystring from 'querystring';
import { WhatsAppNotificationService } from './services/whatsapp-service';
import { Logger } from './utils';

const service = new WhatsAppNotificationService();
const PORT = process.env.PORT || 3000;

interface RequestBody {
  to?: string;
  message?: string;
  template?: string;
  templateParams?: Record<string, string>;
  customerName?: string;
  orderNumber?: string;
  amount?: string;
  bookTitle?: string;
  filePath?: string;
}

async function parseRequestBody(req: http.IncomingMessage): Promise<RequestBody> {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      try {
        const contentType = req.headers['content-type'] || '';
        if (contentType.includes('application/json')) {
          resolve(JSON.parse(body));
        } else if (contentType.includes('application/x-www-form-urlencoded')) {
          resolve(querystring.parse(body) as any);
        } else {
          resolve({});
        }
      } catch (error) {
        reject(error);
      }
    });
  });
}

function sendResponse(res: http.ServerResponse, statusCode: number, data: any): void {
  res.writeHead(statusCode, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(data));
}

const server = http.createServer(async (req, res) => {
  const parsedUrl = url.parse(req.url || '', true);
  const path = parsedUrl.pathname;
  const method = req.method;

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  try {
    // Health check endpoint
    if (path === '/health' && method === 'GET') {
      const health = await service.healthCheck();
      sendResponse(res, health.healthy ? 200 : 503, health);
      return;
    }

    // List templates endpoint
    if (path === '/templates' && method === 'GET') {
      const templates = service.getAvailableTemplates();
      sendResponse(res, 200, { templates });
      return;
    }

    // Send message endpoint
    if (path === '/send-message' && method === 'POST') {
      const body = await parseRequestBody(req);
      
      if (!body.to || !body.message) {
        sendResponse(res, 400, { error: 'Missing required fields: to, message' });
        return;
      }

      const result = await service.sendMessage(body.to, body.message);
      sendResponse(res, result.success ? 200 : 400, result);
      return;
    }

    // Send templated message endpoint
    if (path === '/send-template' && method === 'POST') {
      const body = await parseRequestBody(req);
      
      if (!body.to || !body.template) {
        sendResponse(res, 400, { error: 'Missing required fields: to, template' });
        return;
      }

      const templateParams = body.templateParams || {};
      const result = await service.sendTemplatedMessage(body.to, body.template, templateParams);
      sendResponse(res, result.success ? 200 : 400, result);
      return;
    }

    // Send receipt endpoint
    if (path === '/send-receipt' && method === 'POST') {
      const body = await parseRequestBody(req);
      
      if (!body.to || !body.customerName || !body.orderNumber || !body.amount || !body.filePath) {
        sendResponse(res, 400, { 
          error: 'Missing required fields: to, customerName, orderNumber, amount, filePath' 
        });
        return;
      }

      const result = await service.sendReceipt(
        body.to,
        body.customerName,
        body.orderNumber,
        body.amount,
        body.filePath
      );
      sendResponse(res, result.success ? 200 : 400, result);
      return;
    }

    // Send e-book endpoint
    if (path === '/send-ebook' && method === 'POST') {
      const body = await parseRequestBody(req);
      
      if (!body.to || !body.customerName || !body.bookTitle || !body.filePath) {
        sendResponse(res, 400, { 
          error: 'Missing required fields: to, customerName, bookTitle, filePath' 
        });
        return;
      }

      const result = await service.sendEbook(
        body.to,
        body.customerName,
        body.bookTitle,
        body.filePath
      );
      sendResponse(res, result.success ? 200 : 400, result);
      return;
    }

    // API documentation endpoint
    if (path === '/' && method === 'GET') {
      const documentation = {
        name: 'WhatsApp Notify API',
        version: '1.0.0',
        description: 'REST API for sending WhatsApp messages and attachments',
        endpoints: {
          'GET /': 'This documentation',
          'GET /health': 'Service health check',
          'GET /templates': 'List available message templates',
          'POST /send-message': 'Send a simple text message',
          'POST /send-template': 'Send a templated message',
          'POST /send-receipt': 'Send a receipt with PDF attachment',
          'POST /send-ebook': 'Send an e-book with file attachment'
        },
        examples: {
          'send-message': {
            to: '+1234567890',
            message: 'Hello from WhatsApp!'
          },
          'send-template': {
            to: '+1234567890',
            template: 'welcome',
            templateParams: { name: 'John Doe' }
          },
          'send-receipt': {
            to: '+1234567890',
            customerName: 'John Doe',
            orderNumber: '12345',
            amount: '$99.99',
            filePath: '/path/to/receipt.pdf'
          },
          'send-ebook': {
            to: '+1234567890',
            customerName: 'John Doe',
            bookTitle: 'My Great Book',
            filePath: '/path/to/book.pdf'
          }
        }
      };
      sendResponse(res, 200, documentation);
      return;
    }

    // 404 for unknown routes
    sendResponse(res, 404, { error: 'Route not found' });
  } catch (error) {
    Logger.error('Server error:', error);
    sendResponse(res, 500, { 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

if (require.main === module) {
  server.listen(PORT, () => {
    Logger.info(`WhatsApp Notify server running on port ${PORT}`);
    Logger.info(`Visit http://localhost:${PORT} for API documentation`);
  });
}

export default server;