import { 
  WhatsAppProvider, 
  WhatsAppMessage, 
  WhatsAppMessageWithAttachment, 
  SendMessageResult, 
  MessageType,
  WhatsAppAttachment,
  TwilioConfig 
} from '../types';
import { TwilioWhatsAppProvider } from '../providers/twilio-provider';
import { TemplateEngine } from '../templates/template-engine';
import { ConfigManager } from '../config';
import { Logger, validatePhoneNumber } from '../utils';

export class WhatsAppNotificationService {
  private provider: WhatsAppProvider | null = null;
  private templateEngine: TemplateEngine;
  private configManager: ConfigManager | null = null;
  private configError: string | null = null;

  constructor() {
    this.templateEngine = new TemplateEngine();
    try {
      this.configManager = ConfigManager.getInstance();
      this.provider = this.initializeProvider();
    } catch (error) {
      this.configError = error instanceof Error ? error.message : 'Configuration error';
      Logger.warn('Service initialized without valid configuration:', this.configError);
    }
  }

  private initializeProvider(): WhatsAppProvider {
    if (!this.configManager) {
      throw new Error('Configuration manager not initialized');
    }
    
    const config = this.configManager.getConfig();
    
    switch (config.provider) {
      case 'twilio':
        return new TwilioWhatsAppProvider(config.credentials as TwilioConfig);
      case 'meta':
        throw new Error('Meta provider not yet implemented');
      default:
        throw new Error(`Unsupported provider: ${config.provider}`);
    }
  }

  private ensureConfigured(): void {
    if (this.configError || !this.provider) {
      throw new Error(`Service not properly configured: ${this.configError || 'Unknown configuration error'}`);
    }
  }

  /**
   * Send a simple text message
   */
  async sendMessage(to: string, body: string): Promise<SendMessageResult> {
    this.ensureConfigured();
    
    if (!validatePhoneNumber(to)) {
      return {
        success: false,
        error: 'Invalid phone number format. Must include country code (e.g., +1234567890)'
      };
    }

    const message: WhatsAppMessage = { to, body };
    
    Logger.info(`Sending message to ${to}: ${body.substring(0, 50)}...`);
    return this.provider!.sendMessage(message);
  }

  /**
   * Send a templated message
   */
  async sendTemplatedMessage(
    to: string, 
    templateName: string, 
    templateParams: Record<string, string>
  ): Promise<SendMessageResult> {
    try {
      this.ensureConfigured();
      
      if (!validatePhoneNumber(to)) {
        return {
          success: false,
          error: 'Invalid phone number format. Must include country code (e.g., +1234567890)'
        };
      }

      const body = this.templateEngine.renderTemplate(templateName, templateParams);
      const message: WhatsAppMessage = { to, body, templateName, templateParams };
      
      Logger.info(`Sending templated message (${templateName}) to ${to}`);
      return this.provider!.sendMessage(message);
    } catch (error) {
      Logger.error('Failed to send templated message:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to render template'
      };
    }
  }

  /**
   * Send a receipt with PDF attachment
   */
  async sendReceipt(
    to: string, 
    customerName: string, 
    orderNumber: string, 
    amount: string, 
    receiptFilePath: string
  ): Promise<SendMessageResult> {
    try {
      this.ensureConfigured();
      
      if (!validatePhoneNumber(to)) {
        return {
          success: false,
          error: 'Invalid phone number format. Must include country code (e.g., +1234567890)'
        };
      }

      const body = this.templateEngine.renderTemplate('receipt', {
        customerName,
        orderNumber,
        amount
      });

      const attachment: WhatsAppAttachment = {
        filename: `receipt_${orderNumber}.pdf`,
        filePath: receiptFilePath,
        contentType: 'application/pdf'
      };

      const message: WhatsAppMessageWithAttachment = {
        to,
        body,
        attachments: [attachment],
        templateName: 'receipt',
        templateParams: { customerName, orderNumber, amount }
      };

      Logger.info(`Sending receipt to ${to} for order ${orderNumber}`);
      return this.provider!.sendMessageWithAttachment(message);
    } catch (error) {
      Logger.error('Failed to send receipt:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to send receipt'
      };
    }
  }

  /**
   * Send an e-book with EPUB/PDF attachment
   */
  async sendEbook(
    to: string, 
    customerName: string, 
    bookTitle: string, 
    ebookFilePath: string
  ): Promise<SendMessageResult> {
    try {
      this.ensureConfigured();
      
      if (!validatePhoneNumber(to)) {
        return {
          success: false,
          error: 'Invalid phone number format. Must include country code (e.g., +1234567890)'
        };
      }

      const body = this.templateEngine.renderTemplate('ebook', {
        customerName,
        bookTitle
      });

      const fileExtension = ebookFilePath.split('.').pop()?.toLowerCase();
      const contentType = fileExtension === 'epub' ? 'application/epub+zip' : 'application/pdf';

      const attachment: WhatsAppAttachment = {
        filename: `${bookTitle.replace(/[^a-zA-Z0-9]/g, '_')}.${fileExtension}`,
        filePath: ebookFilePath,
        contentType
      };

      const message: WhatsAppMessageWithAttachment = {
        to,
        body,
        attachments: [attachment],
        templateName: 'ebook',
        templateParams: { customerName, bookTitle }
      };

      Logger.info(`Sending e-book "${bookTitle}" to ${to}`);
      return this.provider!.sendMessageWithAttachment(message);
    } catch (error) {
      Logger.error('Failed to send e-book:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to send e-book'
      };
    }
  }

  /**
   * Send a message with custom attachments
   */
  async sendMessageWithFiles(
    to: string, 
    body: string, 
    attachments: WhatsAppAttachment[]
  ): Promise<SendMessageResult> {
    this.ensureConfigured();
    
    if (!validatePhoneNumber(to)) {
      return {
        success: false,
        error: 'Invalid phone number format. Must include country code (e.g., +1234567890)'
      };
    }

    const message: WhatsAppMessageWithAttachment = {
      to,
      body,
      attachments
    };

    Logger.info(`Sending message with ${attachments.length} attachments to ${to}`);
    return this.provider!.sendMessageWithAttachment(message);
  }

  /**
   * Get available message templates
   */
  getAvailableTemplates(): string[] {
    return this.templateEngine.listTemplates();
  }

  /**
   * Add a custom template
   */
  addTemplate(name: string, content: string, variables: string[]): void {
    this.templateEngine.addTemplate({ name, content, variables });
  }

  /**
   * Health check for the service
   */
  async healthCheck(): Promise<{ healthy: boolean; provider: string; error?: string }> {
    try {
      if (this.configError || !this.configManager) {
        return {
          healthy: false,
          provider: 'unknown',
          error: this.configError || 'Configuration not loaded'
        };
      }
      
      const config = this.configManager.getConfig();
      
      // Check if provider supports health check
      if (this.provider && 'validateConfiguration' in this.provider) {
        const isValid = await (this.provider as any).validateConfiguration();
        return {
          healthy: isValid,
          provider: config.provider
        };
      }

      return {
        healthy: true,
        provider: config.provider
      };
    } catch (error) {
      return {
        healthy: false,
        provider: 'unknown',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}