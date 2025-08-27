export interface WhatsAppMessage {
  to: string;
  body?: string;
  templateName?: string;
  templateParams?: Record<string, string>;
}

export interface WhatsAppAttachment {
  filename: string;
  filePath: string;
  contentType?: string;
}

export interface WhatsAppMessageWithAttachment extends WhatsAppMessage {
  attachments?: WhatsAppAttachment[];
}

export interface MessageTemplate {
  name: string;
  content: string;
  variables: string[];
}

export interface ProviderConfig {
  provider: 'twilio' | 'meta';
  credentials: TwilioConfig | MetaConfig;
}

export interface TwilioConfig {
  accountSid: string;
  authToken: string;
  fromNumber: string;
}

export interface MetaConfig {
  accessToken: string;
  phoneNumberId: string;
}

export interface SendMessageResult {
  success: boolean;
  messageId?: string;
  error?: string;
  providedResponse?: any;
}

export interface WhatsAppProvider {
  sendMessage(message: WhatsAppMessage): Promise<SendMessageResult>;
  sendMessageWithAttachment(message: WhatsAppMessageWithAttachment): Promise<SendMessageResult>;
}

export enum MessageType {
  TEXT = 'text',
  RECEIPT = 'receipt',
  EBOOK = 'ebook',
  GENERAL = 'general'
}