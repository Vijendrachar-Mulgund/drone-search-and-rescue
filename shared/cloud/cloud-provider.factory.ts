import { CloudConfig } from './types';
import { ICloudProvider } from './cloud-provider.interface';
import { AWSProvider } from './aws-provider';
import { AzureProvider } from './azure-provider';

export class CloudProviderFactory {
  private static instance: CloudProviderFactory;
  private currentProvider?: ICloudProvider;

  private constructor() {}

  static getInstance(): CloudProviderFactory {
    if (!CloudProviderFactory.instance) {
      CloudProviderFactory.instance = new CloudProviderFactory();
    }
    return CloudProviderFactory.instance;
  }

  getProvider(config: CloudConfig): ICloudProvider {
    if (this.currentProvider) {
      return this.currentProvider;
    }

    switch (config.provider) {
      case 'aws':
        if (!config.credentials.aws) {
          throw new Error('AWS credentials not provided');
        }
        this.currentProvider = new AWSProvider(config);
        break;
      case 'azure':
        if (!config.credentials.azure) {
          throw new Error('Azure credentials not provided');
        }
        this.currentProvider = new AzureProvider(config);
        break;
      default:
        throw new Error(`Unsupported cloud provider: ${config.provider}`);
    }

    return this.currentProvider;
  }

  clearProvider(): void {
    this.currentProvider = undefined;
  }
}

// Export a default instance
export const cloudProvider = CloudProviderFactory.getInstance();

// Example usage:
/*
const config: CloudConfig = {
  provider: 'aws',
  credentials: {
    region: 'us-east-1',
    aws: {
      accessKeyId: 'your-access-key',
      secretAccessKey: 'your-secret-key'
    }
  }
};

// Get AWS provider
const awsProvider = cloudProvider.getProvider(config);

// Switch to Azure
const azureConfig: CloudConfig = {
  provider: 'azure',
  credentials: {
    region: 'eastus',
    azure: {
      tenantId: 'your-tenant-id',
      clientId: 'your-client-id',
      clientSecret: 'your-client-secret',
      subscriptionId: 'your-subscription-id',
      storageConnectionString: 'your-storage-connection-string'
    }
  }
};

// Clear existing provider
cloudProvider.clearProvider();

// Get Azure provider
const azureProvider = cloudProvider.getProvider(azureConfig);
*/
