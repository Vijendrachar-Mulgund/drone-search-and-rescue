import { CloudConfig, CloudProvider } from './types';

export class ConfigLoader {
  private static instance: ConfigLoader;
  private config?: CloudConfig;

  private constructor() {}

  static getInstance(): ConfigLoader {
    if (!ConfigLoader.instance) {
      ConfigLoader.instance = new ConfigLoader();
    }
    return ConfigLoader.instance;
  }

  loadConfig(provider?: CloudProvider): CloudConfig {
    // If config is already loaded and no specific provider is requested, return cached config
    if (this.config && !provider) {
      return this.config;
    }

    // Load from environment variables
    const envProvider = (provider || process.env.CLOUD_PROVIDER || 'aws').toLowerCase() as CloudProvider;
    const region = process.env.CLOUD_REGION || 'us-east-1';

    let credentials: CloudConfig['credentials'] = {
      region,
    };

    switch (envProvider) {
      case 'aws':
        credentials.aws = {
          accessKeyId: this.getRequiredEnv('AWS_ACCESS_KEY_ID'),
          secretAccessKey: this.getRequiredEnv('AWS_SECRET_ACCESS_KEY'),
        };
        break;

      case 'azure':
        credentials.azure = {
          tenantId: this.getRequiredEnv('AZURE_TENANT_ID'),
          clientId: this.getRequiredEnv('AZURE_CLIENT_ID'),
          clientSecret: this.getRequiredEnv('AZURE_CLIENT_SECRET'),
          subscriptionId: this.getRequiredEnv('AZURE_SUBSCRIPTION_ID'),
          storageConnectionString: this.getRequiredEnv('AZURE_STORAGE_CONNECTION_STRING'),
        };
        break;

      default:
        throw new Error(`Unsupported cloud provider: ${envProvider}`);
    }

    this.config = {
      provider: envProvider,
      credentials,
    };

    return this.config;
  }

  private getRequiredEnv(name: string): string {
    const value = process.env[name];
    if (!value) {
      throw new Error(`Required environment variable ${name} is not set`);
    }
    return value;
  }

  // Helper method to generate example .env file content
  static generateEnvExample(): string {
    return `# Cloud Provider Configuration
# Specify the cloud provider to use (aws or azure)
CLOUD_PROVIDER=aws
CLOUD_REGION=us-east-1

# AWS Credentials
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key

# Azure Credentials
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_STORAGE_CONNECTION_STRING=your-storage-connection-string
`;
  }
}

// Export a default instance
export const configLoader = ConfigLoader.getInstance();

// Example usage:
/*
// Load default provider from environment
const config = configLoader.loadConfig();

// Or specify a provider
const awsConfig = configLoader.loadConfig('aws');
const azureConfig = configLoader.loadConfig('azure');
*/
