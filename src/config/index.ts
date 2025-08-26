import * as dotenv from 'dotenv';
import { ProviderConfig, TwilioConfig, MetaConfig } from '../types';

dotenv.config();

export class ConfigManager {
  private static instance: ConfigManager;
  private config: ProviderConfig;

  private constructor() {
    this.config = this.loadConfig();
  }

  static getInstance(): ConfigManager {
    if (!ConfigManager.instance) {
      ConfigManager.instance = new ConfigManager();
    }
    return ConfigManager.instance;
  }

  private loadConfig(): ProviderConfig {
    const provider = (process.env.WHATSAPP_PROVIDER || 'twilio') as 'twilio' | 'meta';

    if (provider === 'twilio') {
      return {
        provider: 'twilio',
        credentials: this.loadTwilioConfig()
      };
    } else if (provider === 'meta') {
      return {
        provider: 'meta',
        credentials: this.loadMetaConfig()
      };
    }

    throw new Error(`Unsupported provider: ${provider}`);
  }

  private loadTwilioConfig(): TwilioConfig {
    const accountSid = process.env.TWILIO_ACCOUNT_SID;
    const authToken = process.env.TWILIO_AUTH_TOKEN;
    const fromNumber = process.env.TWILIO_WHATSAPP_FROM;

    if (!accountSid || !authToken || !fromNumber) {
      throw new Error('Missing required Twilio configuration. Please check TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_WHATSAPP_FROM environment variables.');
    }

    return {
      accountSid,
      authToken,
      fromNumber
    };
  }

  private loadMetaConfig(): MetaConfig {
    const accessToken = process.env.META_ACCESS_TOKEN;
    const phoneNumberId = process.env.META_PHONE_NUMBER_ID;

    if (!accessToken || !phoneNumberId) {
      throw new Error('Missing required Meta configuration. Please check META_ACCESS_TOKEN and META_PHONE_NUMBER_ID environment variables.');
    }

    return {
      accessToken,
      phoneNumberId
    };
  }

  getConfig(): ProviderConfig {
    return this.config;
  }

  updateConfig(newConfig: Partial<ProviderConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  isConfigured(): boolean {
    try {
      this.loadConfig();
      return true;
    } catch {
      return false;
    }
  }
}