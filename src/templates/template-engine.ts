import * as fs from 'fs';
import * as path from 'path';
import { MessageTemplate } from '../types';

export class TemplateEngine {
  private templates: Map<string, MessageTemplate> = new Map();

  constructor() {
    this.loadDefaultTemplates();
  }

  private loadDefaultTemplates(): void {
    // Default templates for common use cases
    this.addTemplate({
      name: 'welcome',
      content: 'Welcome {{name}}! Thank you for joining our service.',
      variables: ['name']
    });

    this.addTemplate({
      name: 'receipt',
      content: 'Hi {{customerName}}, your receipt for order #{{orderNumber}} is attached. Total: {{amount}}. Thank you for your purchase!',
      variables: ['customerName', 'orderNumber', 'amount']
    });

    this.addTemplate({
      name: 'ebook',
      content: 'Hi {{customerName}}, your e-book "{{bookTitle}}" is ready for download. Please find the file attached.',
      variables: ['customerName', 'bookTitle']
    });

    this.addTemplate({
      name: 'order_confirmation',
      content: 'Order confirmed! Hi {{customerName}}, your order #{{orderNumber}} has been confirmed and will be processed shortly.',
      variables: ['customerName', 'orderNumber']
    });
  }

  addTemplate(template: MessageTemplate): void {
    this.templates.set(template.name, template);
  }

  renderTemplate(templateName: string, params: Record<string, string>): string {
    const template = this.templates.get(templateName);
    if (!template) {
      throw new Error(`Template '${templateName}' not found`);
    }

    let content = template.content;
    for (const variable of template.variables) {
      const value = params[variable];
      if (value === undefined) {
        throw new Error(`Missing parameter '${variable}' for template '${templateName}'`);
      }
      content = content.replace(new RegExp(`{{${variable}}}`, 'g'), value);
    }

    return content;
  }

  getTemplate(name: string): MessageTemplate | undefined {
    return this.templates.get(name);
  }

  listTemplates(): string[] {
    return Array.from(this.templates.keys());
  }

  loadTemplatesFromDirectory(dirPath: string): void {
    if (!fs.existsSync(dirPath)) {
      return;
    }

    const files = fs.readdirSync(dirPath);
    for (const file of files) {
      if (path.extname(file) === '.json') {
        try {
          const filePath = path.join(dirPath, file);
          const templateData = JSON.parse(fs.readFileSync(filePath, 'utf8'));
          this.addTemplate(templateData);
        } catch (error) {
          console.warn(`Failed to load template from ${file}:`, error);
        }
      }
    }
  }
}