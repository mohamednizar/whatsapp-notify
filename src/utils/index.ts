import * as fs from 'fs';
import * as path from 'path';
import * as mime from 'mime-types';

export class FileUtils {
  static validateFile(filePath: string): { exists: boolean; size: number; mimeType: string } {
    if (!fs.existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    const stats = fs.statSync(filePath);
    const mimeType = mime.lookup(filePath) || 'application/octet-stream';

    return {
      exists: true,
      size: stats.size,
      mimeType
    };
  }

  static isValidAttachmentType(filePath: string): boolean {
    const validExtensions = ['.pdf', '.epub', '.txt', '.doc', '.docx', '.jpg', '.jpeg', '.png'];
    const ext = path.extname(filePath).toLowerCase();
    return validExtensions.includes(ext);
  }

  static getFileSize(filePath: string): number {
    const stats = fs.statSync(filePath);
    return stats.size;
  }

  static validateFileSize(filePath: string, maxSizeBytes: number = 16 * 1024 * 1024): boolean {
    const fileSize = this.getFileSize(filePath);
    return fileSize <= maxSizeBytes;
  }

  static async readFileAsBase64(filePath: string): Promise<string> {
    const buffer = fs.readFileSync(filePath);
    return buffer.toString('base64');
  }
}

export class Logger {
  private static logLevel: string = process.env.LOG_LEVEL || 'info';

  static info(message: string, ...args: any[]): void {
    if (this.shouldLog('info')) {
      console.log(`[INFO] ${new Date().toISOString()} - ${message}`, ...args);
    }
  }

  static warn(message: string, ...args: any[]): void {
    if (this.shouldLog('warn')) {
      console.warn(`[WARN] ${new Date().toISOString()} - ${message}`, ...args);
    }
  }

  static error(message: string, ...args: any[]): void {
    if (this.shouldLog('error')) {
      console.error(`[ERROR] ${new Date().toISOString()} - ${message}`, ...args);
    }
  }

  static debug(message: string, ...args: any[]): void {
    if (this.shouldLog('debug')) {
      console.debug(`[DEBUG] ${new Date().toISOString()} - ${message}`, ...args);
    }
  }

  private static shouldLog(level: string): boolean {
    const levels = ['error', 'warn', 'info', 'debug'];
    const currentLevelIndex = levels.indexOf(this.logLevel);
    const messageLevelIndex = levels.indexOf(level);
    return messageLevelIndex <= currentLevelIndex;
  }
}

export function validatePhoneNumber(phoneNumber: string): boolean {
  // Basic WhatsApp phone number validation
  // Should start with + and contain only digits
  const phoneRegex = /^\+[1-9]\d{1,14}$/;
  return phoneRegex.test(phoneNumber);
}

export function formatPhoneNumber(phoneNumber: string): string {
  // Ensure phone number starts with whatsapp: prefix for Twilio
  if (phoneNumber.startsWith('whatsapp:')) {
    return phoneNumber;
  }
  
  if (!phoneNumber.startsWith('+')) {
    throw new Error('Phone number must start with + (country code)');
  }
  
  return `whatsapp:${phoneNumber}`;
}