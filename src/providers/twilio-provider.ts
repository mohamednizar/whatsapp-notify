import twilio from 'twilio';
import * as fs from 'fs';
import { 
  WhatsAppProvider, 
  WhatsAppMessage, 
  WhatsAppMessageWithAttachment, 
  SendMessageResult, 
  TwilioConfig 
} from '../types';
import { Logger, FileUtils, formatPhoneNumber } from '../utils';

export class TwilioWhatsAppProvider implements WhatsAppProvider {
  private client: twilio.Twilio;
  private config: TwilioConfig;

  constructor(config: TwilioConfig) {
    this.config = config;
    this.client = twilio(config.accountSid, config.authToken);
  }

  async sendMessage(message: WhatsAppMessage): Promise<SendMessageResult> {
    try {
      Logger.info(`Sending WhatsApp message to ${message.to}`);

      const formattedTo = formatPhoneNumber(message.to);
      const body = message.body || '';

      const twilioMessage = await this.client.messages.create({
        from: this.config.fromNumber,
        to: formattedTo,
        body: body
      });

      Logger.info(`Message sent successfully with SID: ${twilioMessage.sid}`);

      return {
        success: true,
        messageId: twilioMessage.sid,
        providedResponse: twilioMessage
      };
    } catch (error) {
      Logger.error('Failed to send WhatsApp message:', error);
      
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  async sendMessageWithAttachment(message: WhatsAppMessageWithAttachment): Promise<SendMessageResult> {
    try {
      Logger.info(`Sending WhatsApp message with attachments to ${message.to}`);

      const formattedTo = formatPhoneNumber(message.to);
      const body = message.body || '';

      if (!message.attachments || message.attachments.length === 0) {
        return this.sendMessage(message);
      }

      // For Twilio, we need to send media URLs
      // In a production environment, you'd typically upload files to a CDN/storage service first
      // For this implementation, we'll demonstrate with local file handling
      const mediaUrls: string[] = [];

      for (const attachment of message.attachments) {
        // Validate file
        FileUtils.validateFile(attachment.filePath);
        
        if (!FileUtils.isValidAttachmentType(attachment.filePath)) {
          throw new Error(`Invalid file type for ${attachment.filename}`);
        }

        if (!FileUtils.validateFileSize(attachment.filePath)) {
          throw new Error(`File size too large for ${attachment.filename}`);
        }

        // In a real implementation, you would upload the file to a publicly accessible URL
        // For now, we'll log that the attachment would be processed
        Logger.info(`Processing attachment: ${attachment.filename} (${attachment.filePath})`);
        
        // For demonstration, we'll include a placeholder URL
        // In production, replace this with actual file upload logic
        mediaUrls.push(`https://your-cdn.com/files/${attachment.filename}`);
      }

      const twilioMessage = await this.client.messages.create({
        from: this.config.fromNumber,
        to: formattedTo,
        body: body,
        // Note: In production, these would be actual URLs to uploaded files
        mediaUrl: mediaUrls
      });

      Logger.info(`Message with attachments sent successfully with SID: ${twilioMessage.sid}`);

      return {
        success: true,
        messageId: twilioMessage.sid,
        providedResponse: twilioMessage
      };
    } catch (error) {
      Logger.error('Failed to send WhatsApp message with attachments:', error);
      
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  // Helper method to upload file to a storage service (placeholder)
  private async uploadFileToStorage(filePath: string, filename: string): Promise<string> {
    // This is a placeholder for actual file upload implementation
    // In production, you would use services like AWS S3, Google Cloud Storage, etc.
    Logger.info(`Uploading file ${filename} to storage...`);
    
    // Return a mock URL for demonstration
    return `https://your-storage-service.com/uploads/${filename}`;
  }

  // Health check method
  async validateConfiguration(): Promise<boolean> {
    try {
      // Try to get account info to validate credentials
      await this.client.api.accounts(this.config.accountSid).fetch();
      return true;
    } catch (error) {
      Logger.error('Twilio configuration validation failed:', error);
      return false;
    }
  }
}