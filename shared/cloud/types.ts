export type CloudProvider = 'aws' | 'azure';

export interface CloudConfig {
  provider: CloudProvider;
  credentials: {
    region: string;
    aws?: {
      accessKeyId: string;
      secretAccessKey: string;
    };
    azure?: {
      tenantId: string;
      clientId: string;
      clientSecret: string;
      subscriptionId: string;
      storageConnectionString: string;
    };
  };
}

export interface ComputeInstance {
  id: string;
  status: 'running' | 'stopped' | 'terminated';
  publicIp?: string;
  privateIp?: string;
}

export interface StorageOptions {
  container: string;
  path: string;
  contentType?: string;
}

export interface MLModelOptions {
  modelId: string;
  version?: string;
  runtime?: string;
}

export interface MLInferenceResult {
  predictions: any;
  metadata: {
    latency: number;
    modelVersion: string;
  };
}
