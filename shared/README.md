# DSAR Cloud Provider Abstraction Layer

This package provides a cloud provider abstraction layer for the Drone Search and Rescue (DSAR) project, allowing seamless switching between AWS and Azure cloud services.

## Features

- Unified interface for cloud services
- Support for AWS and Azure providers
- Easy configuration management
- Type-safe implementations
- Health check capabilities

## Supported Services

### Compute
- AWS EC2 / Azure Virtual Machines
- Instance management (create, terminate, status)
- Custom configuration support

### Storage
- AWS S3 / Azure Blob Storage
- File upload/download
- Content type management

### Machine Learning
- AWS SageMaker / Azure ML
- Model deployment
- Real-time inference

## Usage

### Basic Setup

```typescript
import { cloudProvider, configLoader } from 'dsar-cloud-shared';

// Load configuration from environment variables
const config = configLoader.loadConfig();

// Get cloud provider instance
const provider = cloudProvider.getProvider(config);
```

### Switching Providers

```typescript
// Clear existing provider
cloudProvider.clearProvider();

// Load Azure configuration
const azureConfig = configLoader.loadConfig('azure');
const azureProvider = cloudProvider.getProvider(azureConfig);
```

### Example Operations

```typescript
// Create compute instance
const instance = await provider.createComputeInstance({
  name: 'dsar-compute-1',
  instanceType: 't2.medium', // or Azure equivalent
  imageId: 'ami-12345678'
});

// Upload file
const fileUrl = await provider.uploadFile({
  container: 'my-bucket',
  path: 'data/file.txt',
  contentType: 'text/plain'
}, Buffer.from('Hello World'));

// Deploy ML model
const modelId = await provider.deployModel({
  modelId: 'object-detection-v1',
  runtime: 'pytorch'
}, [
  {
    path: 'model.pth',
    content: modelBuffer
  }
]);
```

## Configuration

Create a `.env` file with your cloud credentials:

```bash
# Generate example configuration
npm run generate-env

# Copy example to .env
cp .env.example .env
```

Then edit `.env` with your credentials:

```bash
# Cloud Provider Selection
CLOUD_PROVIDER=aws  # or 'azure'
CLOUD_REGION=us-east-1

# AWS Credentials
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Azure Credentials
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_STORAGE_CONNECTION_STRING=your-storage-connection-string
```

## Health Checks

Monitor the status of cloud services:

```typescript
const health = await provider.healthCheck();
console.log('Cloud Services Status:', health);
```

## Error Handling

The abstraction layer provides consistent error handling across providers:

```typescript
try {
  await provider.createComputeInstance({...});
} catch (error) {
  if (error instanceof CloudProviderError) {
    console.error('Cloud operation failed:', error.message);
    console.error('Provider:', error.provider);
    console.error('Service:', error.service);
  }
}
```

## Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

## Contributing

1. Implement new cloud provider:
   - Create new provider class implementing `ICloudProvider`
   - Add provider to factory
   - Update configuration loader
   - Add tests

2. Add new service:
   - Update interface
   - Implement in each provider
   - Add tests
   - Update documentation

## License

MIT
