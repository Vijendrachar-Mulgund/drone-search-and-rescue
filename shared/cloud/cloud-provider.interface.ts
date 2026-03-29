import { ComputeInstance, StorageOptions, MLModelOptions, MLInferenceResult, CloudConfig } from './types';

export interface ICloudProvider {
  // Compute Services
  createComputeInstance(options: {
    name: string;
    instanceType: string;
    imageId: string;
    userData?: string;
  }): Promise<ComputeInstance>;

  getComputeInstance(instanceId: string): Promise<ComputeInstance>;
  
  terminateInstance(instanceId: string): Promise<void>;
  
  // Storage Services
  uploadFile(
    options: StorageOptions,
    data: Buffer
  ): Promise<string>;
  
  downloadFile(
    options: StorageOptions
  ): Promise<Buffer>;
  
  deleteFile(
    options: StorageOptions
  ): Promise<void>;
  
  // ML Services
  deployModel(
    options: MLModelOptions,
    modelFiles: {
      path: string;
      content: Buffer;
    }[]
  ): Promise<string>;
  
  runInference(
    options: MLModelOptions,
    input: any
  ): Promise<MLInferenceResult>;
  
  // Configuration
  getConfig(): CloudConfig;
  
  // Health Check
  healthCheck(): Promise<{
    status: 'healthy' | 'unhealthy';
    services: {
      compute: boolean;
      storage: boolean;
      ml: boolean;
    };
  }>;
}

export abstract class BaseCloudProvider implements ICloudProvider {
  protected config: CloudConfig;

  constructor(config: CloudConfig) {
    this.config = config;
  }

  abstract createComputeInstance(options: {
    name: string;
    instanceType: string;
    imageId: string;
    userData?: string;
  }): Promise<ComputeInstance>;

  abstract getComputeInstance(instanceId: string): Promise<ComputeInstance>;
  
  abstract terminateInstance(instanceId: string): Promise<void>;
  
  abstract uploadFile(options: StorageOptions, data: Buffer): Promise<string>;
  
  abstract downloadFile(options: StorageOptions): Promise<Buffer>;
  
  abstract deleteFile(options: StorageOptions): Promise<void>;
  
  abstract deployModel(
    options: MLModelOptions,
    modelFiles: { path: string; content: Buffer; }[]
  ): Promise<string>;
  
  abstract runInference(options: MLModelOptions, input: any): Promise<MLInferenceResult>;
  
  getConfig(): CloudConfig {
    return this.config;
  }

  abstract healthCheck(): Promise<{
    status: 'healthy' | 'unhealthy';
    services: {
      compute: boolean;
      storage: boolean;
      ml: boolean;
    };
  }>;
}
