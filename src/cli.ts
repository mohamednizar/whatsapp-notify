#!/usr/bin/env node

import * as yargs from 'yargs';
import * as path from 'path';
import { WhatsAppNotificationService } from './services/whatsapp-service';
import { Logger } from './utils';

const service = new WhatsAppNotificationService();

yargs
  .scriptName('whatsapp-notify')
  .usage('$0 <cmd> [args]')
  .command(
    'send-message <to> <message>',
    'Send a simple text message',
    (yargs) => {
      return yargs
        .positional('to', {
          type: 'string',
          describe: 'Recipient phone number (with country code, e.g., +1234567890)',
          demandOption: true
        })
        .positional('message', {
          type: 'string',
          describe: 'Message content',
          demandOption: true
        });
    },
    async (argv) => {
      try {
        const result = await service.sendMessage(argv.to, argv.message);
        if (result.success) {
          console.log(`✅ Message sent successfully! ID: ${result.messageId}`);
        } else {
          console.error(`❌ Failed to send message: ${result.error}`);
          process.exit(1);
        }
      } catch (error) {
        console.error('❌ Error:', error);
        process.exit(1);
      }
    }
  )
  .command(
    'send-template <to> <template> [params..]',
    'Send a templated message',
    (yargs) => {
      return yargs
        .positional('to', {
          type: 'string',
          describe: 'Recipient phone number (with country code)',
          demandOption: true
        })
        .positional('template', {
          type: 'string',
          describe: 'Template name',
          demandOption: true
        })
        .positional('params', {
          type: 'string',
          describe: 'Template parameters in format key=value',
          array: true
        });
    },
    async (argv) => {
      try {
        // Parse parameters
        const templateParams: Record<string, string> = {};
        if (argv.params) {
          for (const param of argv.params) {
            const [key, value] = param.split('=');
            if (key && value) {
              templateParams[key] = value;
            }
          }
        }

        const result = await service.sendTemplatedMessage(argv.to, argv.template, templateParams);
        if (result.success) {
          console.log(`✅ Templated message sent successfully! ID: ${result.messageId}`);
        } else {
          console.error(`❌ Failed to send templated message: ${result.error}`);
          process.exit(1);
        }
      } catch (error) {
        console.error('❌ Error:', error);
        process.exit(1);
      }
    }
  )
  .command(
    'send-receipt <to> <customerName> <orderNumber> <amount> <receiptFile>',
    'Send a receipt with PDF attachment',
    (yargs) => {
      return yargs
        .positional('to', {
          type: 'string',
          describe: 'Recipient phone number (with country code)',
          demandOption: true
        })
        .positional('customerName', {
          type: 'string',
          describe: 'Customer name',
          demandOption: true
        })
        .positional('orderNumber', {
          type: 'string',
          describe: 'Order number',
          demandOption: true
        })
        .positional('amount', {
          type: 'string',
          describe: 'Order amount',
          demandOption: true
        })
        .positional('receiptFile', {
          type: 'string',
          describe: 'Path to receipt PDF file',
          demandOption: true
        });
    },
    async (argv) => {
      try {
        const result = await service.sendReceipt(
          argv.to,
          argv.customerName,
          argv.orderNumber,
          argv.amount,
          path.resolve(argv.receiptFile)
        );
        
        if (result.success) {
          console.log(`✅ Receipt sent successfully! ID: ${result.messageId}`);
        } else {
          console.error(`❌ Failed to send receipt: ${result.error}`);
          process.exit(1);
        }
      } catch (error) {
        console.error('❌ Error:', error);
        process.exit(1);
      }
    }
  )
  .command(
    'send-ebook <to> <customerName> <bookTitle> <ebookFile>',
    'Send an e-book with EPUB/PDF attachment',
    (yargs) => {
      return yargs
        .positional('to', {
          type: 'string',
          describe: 'Recipient phone number (with country code)',
          demandOption: true
        })
        .positional('customerName', {
          type: 'string',
          describe: 'Customer name',
          demandOption: true
        })
        .positional('bookTitle', {
          type: 'string',
          describe: 'Book title',
          demandOption: true
        })
        .positional('ebookFile', {
          type: 'string',
          describe: 'Path to e-book file (PDF or EPUB)',
          demandOption: true
        });
    },
    async (argv) => {
      try {
        const result = await service.sendEbook(
          argv.to,
          argv.customerName,
          argv.bookTitle,
          path.resolve(argv.ebookFile)
        );
        
        if (result.success) {
          console.log(`✅ E-book sent successfully! ID: ${result.messageId}`);
        } else {
          console.error(`❌ Failed to send e-book: ${result.error}`);
          process.exit(1);
        }
      } catch (error) {
        console.error('❌ Error:', error);
        process.exit(1);
      }
    }
  )
  .command(
    'list-templates',
    'List available message templates',
    {},
    async () => {
      try {
        const templates = service.getAvailableTemplates();
        console.log('📄 Available templates:');
        templates.forEach(template => {
          console.log(`  - ${template}`);
        });
      } catch (error) {
        console.error('❌ Error:', error);
        process.exit(1);
      }
    }
  )
  .command(
    'health-check',
    'Check service health and configuration',
    {},
    async () => {
      try {
        const health = await service.healthCheck();
        if (health.healthy) {
          console.log(`✅ Service is healthy (Provider: ${health.provider})`);
        } else {
          console.log(`❌ Service is unhealthy (Provider: ${health.provider})`);
          if (health.error) {
            console.log(`   Error: ${health.error}`);
          }
          process.exit(1);
        }
      } catch (error) {
        console.error('❌ Error:', error);
        process.exit(1);
      }
    }
  )
  .option('verbose', {
    alias: 'v',
    type: 'boolean',
    description: 'Run with verbose logging',
    default: false
  })
  .middleware((argv) => {
    if (argv.verbose) {
      process.env.LOG_LEVEL = 'debug';
    }
  })
  .help()
  .demandCommand(1, 'You need at least one command before moving on')
  .example('$0 send-message "+1234567890" "Hello from WhatsApp!"', 'Send a simple message')
  .example('$0 send-template "+1234567890" welcome name="John Doe"', 'Send a templated message')
  .example('$0 send-receipt "+1234567890" "John Doe" "12345" "$99.99" "./receipt.pdf"', 'Send a receipt')
  .example('$0 send-ebook "+1234567890" "John Doe" "My Great Book" "./book.pdf"', 'Send an e-book')
  .epilog('For more information, visit https://github.com/ht2cloud/whatsapp-notify')
  .argv;