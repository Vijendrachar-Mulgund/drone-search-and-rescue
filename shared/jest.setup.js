// Mock environment variables
process.env = {
  ...process.env,
  CLOUD_PROVIDER: 'aws',
  CLOUD_REGION: 'us-east-1',
  AWS_ACCESS_KEY_ID: 'test-key',
  AWS_SECRET_ACCESS_KEY: 'test-secret',
  AZURE_TENANT_ID: 'test-tenant',
  AZURE_CLIENT_ID: 'test-client',
  AZURE_CLIENT_SECRET: 'test-secret',
  AZURE_SUBSCRIPTION_ID: 'test-subscription',
  AZURE_STORAGE_CONNECTION_STRING: 'test-connection-string'
};

// Increase test timeout for cloud operations
jest.setTimeout(30000);

// Global error handler
process.on('unhandledRejection', (error) => {
  console.error('Unhandled Promise Rejection:', error);
});
