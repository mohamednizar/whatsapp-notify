import { WhatsAppNotificationService } from '../services/whatsapp-service';

// Mock the dependencies
jest.mock('../config', () => ({
  ConfigManager: {
    getInstance: jest.fn(() => ({
      getConfig: jest.fn(() => ({
        provider: 'twilio',
        credentials: {
          accountSid: 'test_sid',
          authToken: 'test_token',
          fromNumber: 'whatsapp:+14155238886'
        }
      }))
    }))
  }
}));

jest.mock('../providers/twilio-provider', () => ({
  TwilioWhatsAppProvider: jest.fn(() => ({
    sendMessage: jest.fn(async () => ({
      success: true,
      messageId: 'test_message_id'
    })),
    sendMessageWithAttachment: jest.fn(async () => ({
      success: true,
      messageId: 'test_message_id'
    })),
    validateConfiguration: jest.fn(async () => true)
  }))
}));

describe('WhatsAppNotificationService', () => {
  let service: WhatsAppNotificationService;

  beforeEach(() => {
    service = new WhatsAppNotificationService();
  });

  describe('sendMessage', () => {
    it('should send a simple text message successfully', async () => {
      const result = await service.sendMessage('+1234567890', 'Hello World!');
      
      expect(result.success).toBe(true);
      expect(result.messageId).toBe('test_message_id');
    });

    it('should reject invalid phone numbers', async () => {
      const result = await service.sendMessage('invalid_phone', 'Hello World!');
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid phone number format');
    });
  });

  describe('sendTemplatedMessage', () => {
    it('should send a templated message successfully', async () => {
      const result = await service.sendTemplatedMessage(
        '+1234567890',
        'welcome',
        { name: 'John Doe' }
      );
      
      expect(result.success).toBe(true);
      expect(result.messageId).toBe('test_message_id');
    });

    it('should handle template rendering errors', async () => {
      const result = await service.sendTemplatedMessage(
        '+1234567890',
        'nonexistent',
        {}
      );
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('not found');
    });

    it('should handle missing template parameters', async () => {
      const result = await service.sendTemplatedMessage(
        '+1234567890',
        'welcome',
        {} // Missing 'name' parameter
      );
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('Missing parameter');
    });
  });

  describe('getAvailableTemplates', () => {
    it('should return list of available templates', () => {
      const templates = service.getAvailableTemplates();
      
      expect(Array.isArray(templates)).toBe(true);
      expect(templates).toContain('welcome');
      expect(templates).toContain('receipt');
      expect(templates).toContain('ebook');
      expect(templates).toContain('order_confirmation');
    });
  });

  describe('addTemplate', () => {
    it('should add a new template', () => {
      service.addTemplate('test_template', 'Hello {{name}}!', ['name']);
      
      const templates = service.getAvailableTemplates();
      expect(templates).toContain('test_template');
    });
  });

  describe('healthCheck', () => {
    it('should return healthy status', async () => {
      const health = await service.healthCheck();
      
      expect(health.healthy).toBe(true);
      expect(health.provider).toBe('twilio');
    });
  });
});