import { TemplateEngine } from '../templates/template-engine';

describe('TemplateEngine', () => {
  let templateEngine: TemplateEngine;

  beforeEach(() => {
    templateEngine = new TemplateEngine();
  });

  describe('renderTemplate', () => {
    it('should render a simple template with parameters', () => {
      const result = templateEngine.renderTemplate('welcome', { name: 'John Doe' });
      expect(result).toBe('Welcome John Doe! Thank you for joining our service.');
    });

    it('should render receipt template with all parameters', () => {
      const params = {
        customerName: 'Jane Smith',
        orderNumber: '12345',
        amount: '$99.99'
      };
      
      const result = templateEngine.renderTemplate('receipt', params);
      expect(result).toBe('Hi Jane Smith, your receipt for order #12345 is attached. Total: $99.99. Thank you for your purchase!');
    });

    it('should render ebook template with parameters', () => {
      const params = {
        customerName: 'Alice Johnson',
        bookTitle: 'The Great Adventure'
      };
      
      const result = templateEngine.renderTemplate('ebook', params);
      expect(result).toBe('Hi Alice Johnson, your e-book "The Great Adventure" is ready for download. Please find the file attached.');
    });

    it('should throw error for non-existent template', () => {
      expect(() => {
        templateEngine.renderTemplate('nonexistent', {});
      }).toThrow('Template \'nonexistent\' not found');
    });

    it('should throw error for missing parameters', () => {
      expect(() => {
        templateEngine.renderTemplate('welcome', {});
      }).toThrow('Missing parameter \'name\' for template \'welcome\'');
    });
  });

  describe('addTemplate', () => {
    it('should add a custom template', () => {
      const customTemplate = {
        name: 'custom',
        content: 'Hello {{user}}, your order {{order}} is ready!',
        variables: ['user', 'order']
      };

      templateEngine.addTemplate(customTemplate);
      
      const result = templateEngine.renderTemplate('custom', { user: 'Bob', order: '67890' });
      expect(result).toBe('Hello Bob, your order 67890 is ready!');
    });
  });

  describe('listTemplates', () => {
    it('should return list of available templates', () => {
      const templates = templateEngine.listTemplates();
      expect(templates).toContain('welcome');
      expect(templates).toContain('receipt');
      expect(templates).toContain('ebook');
      expect(templates).toContain('order_confirmation');
    });
  });

  describe('getTemplate', () => {
    it('should return template object for existing template', () => {
      const template = templateEngine.getTemplate('welcome');
      expect(template).toBeDefined();
      expect(template?.name).toBe('welcome');
      expect(template?.variables).toContain('name');
    });

    it('should return undefined for non-existent template', () => {
      const template = templateEngine.getTemplate('nonexistent');
      expect(template).toBeUndefined();
    });
  });
});