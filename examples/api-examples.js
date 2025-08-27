const WhatsAppNotificationService = require('../dist/index.js').default;

/**
 * Example usage of the WhatsApp Notification Service programmatically
 */

async function runExamples() {
  console.log('🚀 WhatsApp Notify API Examples\n');

  try {
    // Initialize the service
    const service = new WhatsAppNotificationService();

    // Example 1: Check service health
    console.log('🏥 Example 1: Checking service health...');
    const health = await service.healthCheck();
    console.log('Health status:', health);
    console.log('');

    // Example 2: List available templates
    console.log('📄 Example 2: Listing available templates...');
    const templates = service.getAvailableTemplates();
    console.log('Available templates:', templates);
    console.log('');

    // Example 3: Add a custom template
    console.log('📝 Example 3: Adding a custom template...');
    service.addTemplate(
      'custom_greeting',
      'Hello {{name}}, welcome to our service! Your account ID is {{accountId}}.',
      ['name', 'accountId']
    );
    console.log('Custom template added successfully');
    console.log('Updated templates:', service.getAvailableTemplates());
    console.log('');

    // Example 4: Send a simple message (commented out to avoid sending actual messages)
    console.log('📱 Example 4: Send a simple message (commented out)');
    console.log('// const result1 = await service.sendMessage("+1234567890", "Hello from Node.js!");');
    console.log('// console.log("Message result:", result1);');
    console.log('');

    // Example 5: Send a templated message (commented out)
    console.log('📝 Example 5: Send a templated message (commented out)');
    console.log('// const result2 = await service.sendTemplatedMessage(');
    console.log('//   "+1234567890",');
    console.log('//   "welcome",');
    console.log('//   { name: "Alice Johnson" }');
    console.log('// );');
    console.log('// console.log("Templated message result:", result2);');
    console.log('');

    // Example 6: Send receipt (commented out as it requires a PDF file)
    console.log('📧 Example 6: Send receipt (commented out - requires PDF file)');
    console.log('// const result3 = await service.sendReceipt(');
    console.log('//   "+1234567890",');
    console.log('//   "Bob Smith",');
    console.log('//   "ORDER-456",');
    console.log('//   "$149.99",');
    console.log('//   "./examples/sample-receipt.pdf"');
    console.log('// );');
    console.log('// console.log("Receipt result:", result3);');
    console.log('');

    // Example 7: Send e-book (commented out as it requires an e-book file)
    console.log('📚 Example 7: Send e-book (commented out - requires PDF/EPUB file)');
    console.log('// const result4 = await service.sendEbook(');
    console.log('//   "+1234567890",');
    console.log('//   "Carol White",');
    console.log('//   "JavaScript Mastery",');
    console.log('//   "./examples/sample-book.pdf"');
    console.log('// );');
    console.log('// console.log("E-book result:", result4);');
    console.log('');

    console.log('✅ All examples completed successfully!');
    console.log('💡 To test actual message sending, uncomment the examples and provide valid credentials.');

  } catch (error) {
    console.error('❌ Error:', error.message);
    console.log('\n💡 Make sure to:');
    console.log('1. Build the project with: npm run build');
    console.log('2. Copy .env.example to .env');
    console.log('3. Add your Twilio credentials to .env');
    process.exit(1);
  }
}

// Only run if this file is executed directly
if (require.main === module) {
  runExamples();
}

module.exports = { runExamples };