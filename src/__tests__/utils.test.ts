import { validatePhoneNumber, formatPhoneNumber, FileUtils } from '../utils';
import * as fs from 'fs';
import * as path from 'path';

describe('Utils', () => {
  describe('validatePhoneNumber', () => {
    it('should validate correct phone numbers', () => {
      expect(validatePhoneNumber('+1234567890')).toBe(true);
      expect(validatePhoneNumber('+447911123456')).toBe(true);
      expect(validatePhoneNumber('+5511999887766')).toBe(true);
    });

    it('should reject invalid phone numbers', () => {
      expect(validatePhoneNumber('1234567890')).toBe(false);  // Missing +
      expect(validatePhoneNumber('+0123456789')).toBe(false); // Starts with 0
      expect(validatePhoneNumber('+')).toBe(false);           // Just +
      expect(validatePhoneNumber('+abc123')).toBe(false);     // Contains letters
      expect(validatePhoneNumber('')).toBe(false);            // Empty
    });
  });

  describe('formatPhoneNumber', () => {
    it('should format phone numbers with whatsapp prefix', () => {
      expect(formatPhoneNumber('+1234567890')).toBe('whatsapp:+1234567890');
      expect(formatPhoneNumber('+447911123456')).toBe('whatsapp:+447911123456');
    });

    it('should not double-prefix already formatted numbers', () => {
      expect(formatPhoneNumber('whatsapp:+1234567890')).toBe('whatsapp:+1234567890');
    });

    it('should throw error for numbers without country code', () => {
      expect(() => formatPhoneNumber('1234567890')).toThrow('Phone number must start with + (country code)');
    });
  });

  describe('FileUtils', () => {
    const testDir = '/tmp/whatsapp-notify-tests';
    const testFile = path.join(testDir, 'test.pdf');

    beforeAll(() => {
      // Create test directory and file
      if (!fs.existsSync(testDir)) {
        fs.mkdirSync(testDir, { recursive: true });
      }
      fs.writeFileSync(testFile, 'dummy pdf content');
    });

    afterAll(() => {
      // Clean up test files
      if (fs.existsSync(testFile)) {
        fs.unlinkSync(testFile);
      }
      if (fs.existsSync(testDir)) {
        fs.rmdirSync(testDir);
      }
    });

    describe('validateFile', () => {
      it('should validate existing file', () => {
        const result = FileUtils.validateFile(testFile);
        expect(result.exists).toBe(true);
        expect(result.size).toBeGreaterThan(0);
        expect(result.mimeType).toBe('application/pdf');
      });

      it('should throw error for non-existent file', () => {
        expect(() => {
          FileUtils.validateFile('/path/to/nonexistent/file.pdf');
        }).toThrow('File not found');
      });
    });

    describe('isValidAttachmentType', () => {
      it('should validate allowed file types', () => {
        expect(FileUtils.isValidAttachmentType('test.pdf')).toBe(true);
        expect(FileUtils.isValidAttachmentType('test.epub')).toBe(true);
        expect(FileUtils.isValidAttachmentType('test.jpg')).toBe(true);
        expect(FileUtils.isValidAttachmentType('test.png')).toBe(true);
        expect(FileUtils.isValidAttachmentType('test.doc')).toBe(true);
      });

      it('should reject invalid file types', () => {
        expect(FileUtils.isValidAttachmentType('test.exe')).toBe(false);
        expect(FileUtils.isValidAttachmentType('test.zip')).toBe(false);
        expect(FileUtils.isValidAttachmentType('test')).toBe(false);
      });
    });

    describe('getFileSize', () => {
      it('should return correct file size', () => {
        const size = FileUtils.getFileSize(testFile);
        expect(size).toBe(fs.statSync(testFile).size);
      });
    });

    describe('validateFileSize', () => {
      it('should validate file size within limits', () => {
        const isValid = FileUtils.validateFileSize(testFile, 1024 * 1024); // 1MB limit
        expect(isValid).toBe(true);
      });

      it('should reject files exceeding size limit', () => {
        const isValid = FileUtils.validateFileSize(testFile, 1); // 1 byte limit
        expect(isValid).toBe(false);
      });
    });
  });
});