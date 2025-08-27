import axios, { AxiosResponse } from 'axios';
import { 
  WhatsAppProvider, 
  WhatsAppMessage, 
  WhatsAppMessageWithAttachment, 
  SendMessageResult, 
  MetaConfig 
} from '../types';
import { Logger, FileUtils, formatPhoneNumber } from '../utils';

interface MetaMessageRequest {
  messaging_product: 'whatsapp';
  to: string;
  type: 'text' | 'template' | 'document' | 'image';
  text?: {
    body: string;
  };
  template?: {
    name: string;
    language: {
      code: string;
    };
    components?: Array<Record<string, unknown>>;
  };
  document?: {
    link: string;
    filename: string;
  };
  image?: {
    link: string;
  };
}

interface MetaMessageResponse {
  messaging_product: string;
  contacts: Array<{
    input: string;
    wa_id: string;
  }>;
  messages: Array<{
    id: string;
  }>;
}

export class MetaWhatsAppProvider implements WhatsAppProvider {
  private config: MetaConfig;
  private baseUrl: string = 'https://graph.facebook.com/v18.0';

  constructor(config: MetaConfig) {
    this.config = config;
  }

  async sendMessage(message: WhatsAppMessage): Promise<SendMessageResult> {
    try {
      Logger.info(`Sending WhatsApp message via Meta API to ${message.to}`);

      const formattedTo = formatPhoneNumber(message.to);
      const body = message.body || '';

      const requestData: MetaMessageRequest = {
        messaging_product: 'whatsapp',
        to: formattedTo,
        type: 'text',
        text: {
          body: body
        }
      };

      const response = await this.makeApiCall(requestData);

      Logger.info(`Message sent successfully with ID: ${response.data.messages[0].id}`);

      return {
        success: true,
        messageId: response.data.messages[0].id,
        providedResponse: response.data
      };
    } catch (error) {
      Logger.error('Failed to send WhatsApp message via Meta API:', error);
      
      return {
        success: false,
        error: this.extractErrorMessage(error)
      };
    }
  }

  async sendMessageWithAttachment(message: WhatsAppMessageWithAttachment): Promise<SendMessageResult> {
    try {
      Logger.info(`Sending WhatsApp message with attachments via Meta API to ${message.to}`);

      const formattedTo = formatPhoneNumber(message.to);
      const body = message.body || '';

      if (!message.attachments || message.attachments.length === 0) {
        return this.sendMessage(message);
      }

      // For Meta API, we can only send one attachment per message
      // If multiple attachments, we'll send the text message first, then attachments
      let primaryResult: SendMessageResult;

      if (body) {
        primaryResult = await this.sendMessage({ to: message.to, body });
        if (!primaryResult.success) {
          return primaryResult;
        }
      }

      // Send attachments
      const attachmentResults: SendMessageResult[] = [];
      
      for (const attachment of message.attachments) {
        // Validate file
        FileUtils.validateFile(attachment.filePath);
        
        if (!FileUtils.isValidAttachmentType(attachment.filePath)) {
          throw new Error(`Invalid file type for ${attachment.filename}`);
        }

        if (!FileUtils.validateFileSize(attachment.filePath)) {
          throw new Error(`File size too large for ${attachment.filename}`);
        }

        // For Meta API, we need to upload the file first or provide a publicly accessible URL
        // In a real implementation, you would upload the file to your server/CDN
        Logger.info(`Processing attachment: ${attachment.filename} (${attachment.filePath})`);
        
        const attachmentResult = await this.sendAttachment(formattedTo, attachment.filePath, attachment.filename);
        attachmentResults.push(attachmentResult);

        if (!attachmentResult.success) {
          break; // Stop on first failure
        }
      }

      // Return the result of the last attachment or the text message if no attachments succeeded
      const lastResult = attachmentResults.length > 0 ? attachmentResults[attachmentResults.length - 1] : primaryResult!;

      return lastResult;
    } catch (error) {
      Logger.error('Failed to send WhatsApp message with attachments via Meta API:', error);
      
      return {
        success: false,
        error: this.extractErrorMessage(error)
      };
    }
  }

  private async sendAttachment(to: string, filePath: string, filename: string): Promise<SendMessageResult> {
    try {
      // Determine file type
      const fileExtension = filePath.toLowerCase().split('.').pop();
      const isImage = ['jpg', 'jpeg', 'png'].includes(fileExtension || '');
      
      // In a production environment, you would upload the file to a publicly accessible URL
      // For this implementation, we'll use a placeholder URL
      const mediaUrl = await this.uploadFileToStorage(filePath, filename);

      const requestData: MetaMessageRequest = {
        messaging_product: 'whatsapp',
        to: to,
        type: isImage ? 'image' : 'document'
      };

      if (isImage) {
        requestData.image = {
          link: mediaUrl
        };
      } else {
        requestData.document = {
          link: mediaUrl,
          filename: filename
        };
      }

      const response = await this.makeApiCall(requestData);

      Logger.info(`Attachment sent successfully with ID: ${response.data.messages[0].id}`);

      return {
        success: true,
        messageId: response.data.messages[0].id,
        providedResponse: response.data
      };
    } catch (error) {
      Logger.error('Failed to send attachment via Meta API:', error);
      
      return {
        success: false,
        error: this.extractErrorMessage(error)
      };
    }
  }

  private async makeApiCall(requestData: MetaMessageRequest): Promise<AxiosResponse<MetaMessageResponse>> {
    const url = `${this.baseUrl}/${this.config.phoneNumberId}/messages`;
    
    return await axios.post(url, requestData, {
      headers: {
        'Authorization': `Bearer ${this.config.accessToken}`,
        'Content-Type': 'application/json'
      }
    });
  }

  // Helper method to upload file to a storage service (placeholder)
  private async uploadFileToStorage(filePath: string, filename: string): Promise<string> {
    // This is a placeholder for actual file upload implementation
    // In production, you would use services like AWS S3, Google Cloud Storage, etc.
    // The file needs to be publicly accessible for Meta API to download it
    Logger.info(`Uploading file ${filename} to storage for Meta API...`);
    
    // Return a mock URL for demonstration
    // In production, implement actual file upload and return the public URL
    return `https://your-storage-service.com/uploads/${filename}`;
  }

  private extractErrorMessage(error: unknown): string {
    if (axios.isAxiosError(error)) {
      if (error.response?.data?.error?.message) {
        return error.response.data.error.message;
      }
      if (error.response?.statusText) {
        return `HTTP ${error.response.status}: ${error.response.statusText}`;
      }
    }
    
    return error instanceof Error ? error.message : 'Unknown error occurred';
  }

  // Health check method
  async validateConfiguration(): Promise<boolean> {
    try {
      // Test the configuration by making a simple API call to verify credentials
      const testUrl = `${this.baseUrl}/${this.config.phoneNumberId}`;
      
      await axios.get(testUrl, {
        headers: {
          'Authorization': `Bearer ${this.config.accessToken}`
        }
      });
      
      return true;
    } catch (error) {
      Logger.error('Meta API configuration validation failed:', error);
      return false;
    }
  }
}