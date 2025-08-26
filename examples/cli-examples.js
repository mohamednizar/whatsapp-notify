#!/usr/bin/env node

/**
 * Example usage of the WhatsApp Notify CLI
 * 
 * Make sure to set up your environment variables first:
 * - Copy .env.example to .env
 * - Fill in your Twilio credentials
 */

const { execSync } = require('child_process');

const PHONE_NUMBER = '+1234567890'; // Replace with your test phone number

console.log('🚀 WhatsApp Notify CLI Examples\n');

try {
  // Example 1: Send a simple message
  console.log('📱 Example 1: Sending a simple message...');
  execSync(`npm run cli send-message "${PHONE_NUMBER}" "Hello from WhatsApp Notify! 🎉"`, { stdio: 'inherit' });
  console.log('');

  // Example 2: Send a templated welcome message
  console.log('📝 Example 2: Sending a templated welcome message...');
  execSync(`npm run cli send-template "${PHONE_NUMBER}" welcome name="John Doe"`, { stdio: 'inherit' });
  console.log('');

  // Example 3: List available templates
  console.log('📄 Example 3: Listing available templates...');
  execSync('npm run cli list-templates', { stdio: 'inherit' });
  console.log('');

  // Example 4: Health check
  console.log('🏥 Example 4: Checking service health...');
  execSync('npm run cli health-check', { stdio: 'inherit' });
  console.log('');

  // Example 5: Send receipt (commented out as it requires a PDF file)
  console.log('📧 Example 5: Send receipt (requires PDF file - commented out)');
  console.log(`// npm run cli send-receipt "${PHONE_NUMBER}" "Jane Smith" "ORDER-123" "$99.99" "./examples/sample-receipt.pdf"`);
  console.log('');

  // Example 6: Send e-book (commented out as it requires an e-book file)
  console.log('📚 Example 6: Send e-book (requires PDF/EPUB file - commented out)');
  console.log(`// npm run cli send-ebook "${PHONE_NUMBER}" "John Doe" "The Great Adventure" "./examples/sample-book.pdf"`);
  console.log('');

  console.log('✅ All examples completed successfully!');
  console.log('💡 To test file attachments, create sample PDF files and uncomment the last two examples.');
  
} catch (error) {
  console.error('❌ Error running examples:', error.message);
  console.log('\n💡 Make sure to:');
  console.log('1. Copy .env.example to .env');
  console.log('2. Add your Twilio credentials to .env');
  console.log('3. Replace the phone number with your own');
  process.exit(1);
}