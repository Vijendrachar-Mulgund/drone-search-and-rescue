import { 
  ComputeManagementClient,
  VirtualMachine,
  VirtualMachineInstanceView
} from '@azure/arm-compute';
import { 
  BlobServiceClient,
  BlockBlobClient
} from '@azure/storage-blob';
import {
  AzureMLWorkspaceClient,
  Model,
  OnlineEndpoint
} from '@azure/ai-ml';
import { DefaultAzureCredential } from '@azure/identity';

import { BaseCloudProvider } from './cloud-provider.interface';
import { 
  ComputeInstance, 
  StorageOptions, 
  MLModelOptions, 
  MLInferenceResult,
  CloudConfig 
} from './types';

export class AzureProvider extends BaseCloudProvider {
  private computeClient: ComputeManagementClient;
  private blobServiceClient: BlobServiceClient;
  private mlClient: AzureMLWorkspaceClient;
  private resourceGroup: string;

  constructor(config: CloudConfig) {
    super(config);
    if (!config.credentials.azure) {
      throw new Error('Azure credentials not provided');
    }

    const credential = new DefaultAzureCredential();
    
    this.resourceGroup = 'dsar-resource-group'; // Could be configurable
    this.computeClient = new ComputeManagementClient(credential, config.credentials.azure.subscriptionId);
    this.blobServiceClient = BlobServiceClient.fromConnectionString(config.credentials.azure.storageConnectionString);
    this.mlClient = new AzureMLWorkspaceClient(credential, config.credentials.azure.subscriptionId);
  }

  private mapAzureVMToComputeInstance(vm: VirtualMachine, instanceView?: VirtualMachineInstanceView): ComputeInstance {
    let status: 'running' | 'stopped' | 'terminated' = 'terminated';
    
    if (instanceView?.statuses) {
      const powerState = instanceView.statuses.find(s => s.code?.startsWith('PowerState/'));
      if (powerState?.code?.includes('running')) status = 'running';
      else if (powerState?.code?.includes('stopped')) status = 'stopped';
    }

    return {
      id: vm.name || '',
      status,
      publicIp: vm.networkProfile?.networkInterfaces?.[0]?.id, // Would need additional call to get actual IP
      privateIp: undefined // Would need additional call to get actual IP
    };
  }

  async createComputeInstance(options: {
    name: string;
    instanceType: string;
    imageId: string;
    userData?: string;
  }): Promise<ComputeInstance> {
    try {
      const vmParameters = {
        location: this.config.credentials.region,
        hardwareProfile: {
          vmSize: options.instanceType
        },
        storageProfile: {
          imageReference: {
            id: options.imageId
          }
        },
        userData: options.userData ? Buffer.from(options.userData).toString('base64') : undefined
      };

      const vm = await this.computeClient.virtualMachines.beginCreateOrUpdate(
        this.resourceGroup,
        options.name,
        vmParameters
      );

      const result = await vm.pollUntilDone();
      const instanceView = await this.computeClient.virtualMachines.instanceView(
        this.resourceGroup,
        options.name
      );

      return this.mapAzureVMToComputeInstance(result, instanceView);
    } catch (error) {
      throw new Error(`Failed to create compute instance: ${error}`);
    }
  }

  async getComputeInstance(instanceId: string): Promise<ComputeInstance> {
    try {
      const vm = await this.computeClient.virtualMachines.get(
        this.resourceGroup,
        instanceId
      );
      const instanceView = await this.computeClient.virtualMachines.instanceView(
        this.resourceGroup,
        instanceId
      );
      return this.mapAzureVMToComputeInstance(vm, instanceView);
    } catch (error) {
      throw new Error(`Failed to get compute instance: ${error}`);
    }
  }

  async terminateInstance(instanceId: string): Promise<void> {
    try {
      await this.computeClient.virtualMachines.beginDelete(
        this.resourceGroup,
        instanceId
      ).pollUntilDone();
    } catch (error) {
      throw new Error(`Failed to terminate instance: ${error}`);
    }
  }

  async uploadFile(options: StorageOptions, data: Buffer): Promise<string> {
    try {
      const containerClient = this.blobServiceClient.getContainerClient(options.container);
      const blockBlobClient = containerClient.getBlockBlobClient(options.path);
      
      await blockBlobClient.upload(data, data.length, {
        blobHTTPHeaders: {
          blobContentType: options.contentType
        }
      });

      return blockBlobClient.url;
    } catch (error) {
      throw new Error(`Failed to upload file: ${error}`);
    }
  }

  async downloadFile(options: StorageOptions): Promise<Buffer> {
    try {
      const containerClient = this.blobServiceClient.getContainerClient(options.container);
      const blockBlobClient = containerClient.getBlockBlobClient(options.path);
      
      const downloadResponse = await blockBlobClient.download(0);
      const chunks: Buffer[] = [];
      
      // @ts-ignore - Azure SDK types don't match exactly with Node streams
      for await (const chunk of downloadResponse.readableStreamBody) {
        chunks.push(Buffer.from(chunk));
      }
      
      return Buffer.concat(chunks);
    } catch (error) {
      throw new Error(`Failed to download file: ${error}`);
    }
  }

  async deleteFile(options: StorageOptions): Promise<void> {
    try {
      const containerClient = this.blobServiceClient.getContainerClient(options.container);
      const blockBlobClient = containerClient.getBlockBlobClient(options.path);
      await blockBlobClient.delete();
    } catch (error) {
      throw new Error(`Failed to delete file: ${error}`);
    }
  }

  async deployModel(
    options: MLModelOptions,
    modelFiles: { path: string; content: Buffer; }[]
  ): Promise<string> {
    try {
      // Upload model files to blob storage
      const modelArtifacts = await Promise.all(
        modelFiles.map(file => 
          this.uploadFile({
            container: 'model-artifacts',
            path: `${options.modelId}/${file.path}`
          }, file.content)
        )
      );

      // Create Azure ML model
      const model = await this.mlClient.models.createOrUpdate(
        this.resourceGroup,
        options.modelId,
        {
          modelUri: modelArtifacts[0], // Using first artifact as primary model file
          framework: options.runtime || 'pytorch',
          version: options.version || '1.0'
        }
      );

      // Deploy model to online endpoint
      const endpoint = await this.mlClient.onlineEndpoints.beginCreateOrUpdate(
        this.resourceGroup,
        `${options.modelId}-endpoint`,
        {
          authMode: 'key',
          properties: {
            model: model.id
          }
        }
      ).pollUntilDone();

      return endpoint.id || options.modelId;
    } catch (error) {
      throw new Error(`Failed to deploy model: ${error}`);
    }
  }

  async runInference(options: MLModelOptions, input: any): Promise<MLInferenceResult> {
    try {
      const startTime = Date.now();
      
      const endpoint = await this.mlClient.onlineEndpoints.get(
        this.resourceGroup,
        `${options.modelId}-endpoint`
      );

      const response = await fetch(endpoint.scoringUri!, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${endpoint.authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(input)
      });

      if (!response.ok) {
        throw new Error(`Inference failed with status ${response.status}`);
      }

      const predictions = await response.json();
      const latency = Date.now() - startTime;

      return {
        predictions,
        metadata: {
          latency,
          modelVersion: options.version || 'latest'
        }
      };
    } catch (error) {
      throw new Error(`Failed to run inference: ${error}`);
    }
  }

  async healthCheck(): Promise<{
    status: 'healthy' | 'unhealthy';
    services: {
      compute: boolean;
      storage: boolean;
      ml: boolean;
    };
  }> {
    const services = {
      compute: false,
      storage: false,
      ml: false
    };

    try {
      // Check Compute
      await this.computeClient.virtualMachines.list(this.resourceGroup);
      services.compute = true;
    } catch {}

    try {
      // Check Storage
      await this.blobServiceClient.getProperties();
      services.storage = true;
    } catch {}

    try {
      // Check ML
      await this.mlClient.models.list(this.resourceGroup);
      services.ml = true;
    } catch {}

    return {
      status: Object.values(services).every(s => s) ? 'healthy' : 'unhealthy',
      services
    };
  }
}
