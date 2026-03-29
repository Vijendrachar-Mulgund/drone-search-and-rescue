import { 
  EC2Client, 
  RunInstancesCommand,
  DescribeInstancesCommand,
  TerminateInstancesCommand,
  Instance as EC2Instance
} from '@aws-sdk/client-ec2';
import { 
  S3Client, 
  PutObjectCommand, 
  GetObjectCommand,
  DeleteObjectCommand
} from '@aws-sdk/client-s3';
import {
  SageMakerClient,
  CreateModelCommand,
  InvokeEndpointCommand
} from '@aws-sdk/client-sagemaker';

import { BaseCloudProvider } from './cloud-provider.interface';
import { 
  ComputeInstance, 
  StorageOptions, 
  MLModelOptions, 
  MLInferenceResult,
  CloudConfig 
} from './types';

export class AWSProvider extends BaseCloudProvider {
  private ec2Client: EC2Client;
  private s3Client: S3Client;
  private sagemakerClient: SageMakerClient;

  constructor(config: CloudConfig) {
    super(config);
    if (!config.credentials.aws) {
      throw new Error('AWS credentials not provided');
    }

    const awsConfig = {
      region: config.credentials.region,
      credentials: {
        accessKeyId: config.credentials.aws.accessKeyId,
        secretAccessKey: config.credentials.aws.secretAccessKey
      }
    };

    this.ec2Client = new EC2Client(awsConfig);
    this.s3Client = new S3Client(awsConfig);
    this.sagemakerClient = new SageMakerClient(awsConfig);
  }

  private mapEC2InstanceToComputeInstance(instance: EC2Instance): ComputeInstance {
    return {
      id: instance.InstanceId || '',
      status: this.mapEC2Status(instance.State?.Name),
      publicIp: instance.PublicIpAddress,
      privateIp: instance.PrivateIpAddress
    };
  }

  private mapEC2Status(status?: string): 'running' | 'stopped' | 'terminated' {
    switch (status) {
      case 'running':
        return 'running';
      case 'stopped':
        return 'stopped';
      default:
        return 'terminated';
    }
  }

  async createComputeInstance(options: {
    name: string;
    instanceType: string;
    imageId: string;
    userData?: string;
  }): Promise<ComputeInstance> {
    const command = new RunInstancesCommand({
      ImageId: options.imageId,
      InstanceType: options.instanceType,
      MinCount: 1,
      MaxCount: 1,
      UserData: options.userData ? Buffer.from(options.userData).toString('base64') : undefined,
      TagSpecifications: [{
        ResourceType: 'instance',
        Tags: [{ Key: 'Name', Value: options.name }]
      }]
    });

    try {
      const response = await this.ec2Client.send(command);
      if (!response.Instances || response.Instances.length === 0) {
        throw new Error('Failed to create EC2 instance');
      }
      return this.mapEC2InstanceToComputeInstance(response.Instances[0]);
    } catch (error) {
      throw new Error(`Failed to create compute instance: ${error}`);
    }
  }

  async getComputeInstance(instanceId: string): Promise<ComputeInstance> {
    const command = new DescribeInstancesCommand({
      InstanceIds: [instanceId]
    });

    try {
      const response = await this.ec2Client.send(command);
      const instance = response.Reservations?.[0]?.Instances?.[0];
      if (!instance) {
        throw new Error(`Instance ${instanceId} not found`);
      }
      return this.mapEC2InstanceToComputeInstance(instance);
    } catch (error) {
      throw new Error(`Failed to get compute instance: ${error}`);
    }
  }

  async terminateInstance(instanceId: string): Promise<void> {
    const command = new TerminateInstancesCommand({
      InstanceIds: [instanceId]
    });

    try {
      await this.ec2Client.send(command);
    } catch (error) {
      throw new Error(`Failed to terminate instance: ${error}`);
    }
  }

  async uploadFile(options: StorageOptions, data: Buffer): Promise<string> {
    const command = new PutObjectCommand({
      Bucket: options.container,
      Key: options.path,
      Body: data,
      ContentType: options.contentType
    });

    try {
      await this.s3Client.send(command);
      return `s3://${options.container}/${options.path}`;
    } catch (error) {
      throw new Error(`Failed to upload file: ${error}`);
    }
  }

  async downloadFile(options: StorageOptions): Promise<Buffer> {
    const command = new GetObjectCommand({
      Bucket: options.container,
      Key: options.path
    });

    try {
      const response = await this.s3Client.send(command);
      if (!response.Body) {
        throw new Error('No data received');
      }
      const streamResponse = response.Body as any;
      return Buffer.concat(await streamResponse.toArray());
    } catch (error) {
      throw new Error(`Failed to download file: ${error}`);
    }
  }

  async deleteFile(options: StorageOptions): Promise<void> {
    const command = new DeleteObjectCommand({
      Bucket: options.container,
      Key: options.path
    });

    try {
      await this.s3Client.send(command);
    } catch (error) {
      throw new Error(`Failed to delete file: ${error}`);
    }
  }

  async deployModel(
    options: MLModelOptions,
    modelFiles: { path: string; content: Buffer; }[]
  ): Promise<string> {
    // Upload model files to S3
    const modelArtifacts = await Promise.all(
      modelFiles.map(file => 
        this.uploadFile({
          container: 'model-artifacts',
          path: `${options.modelId}/${file.path}`
        }, file.content)
      )
    );

    const command = new CreateModelCommand({
      ModelName: options.modelId,
      PrimaryContainer: {
        Image: this.getModelImage(options.runtime || 'pytorch'),
        ModelDataUrl: modelArtifacts[0] // Using first artifact as primary model file
      }
    });

    try {
      const response = await this.sagemakerClient.send(command);
      return response.ModelArn || options.modelId;
    } catch (error) {
      throw new Error(`Failed to deploy model: ${error}`);
    }
  }

  async runInference(options: MLModelOptions, input: any): Promise<MLInferenceResult> {
    const command = new InvokeEndpointCommand({
      EndpointName: options.modelId,
      Body: Buffer.from(JSON.stringify(input))
    });

    try {
      const startTime = Date.now();
      const response = await this.sagemakerClient.send(command);
      const latency = Date.now() - startTime;

      if (!response.Body) {
        throw new Error('No prediction received');
      }

      const predictions = JSON.parse(Buffer.from(response.Body as any).toString());
      
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

  private getModelImage(runtime: string): string {
    // Map of supported runtimes to their ECR image URIs
    const runtimeMap: Record<string, string> = {
      'pytorch': '763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-inference:1.8.1-cpu-py36-ubuntu18.04',
      'tensorflow': '763104351884.dkr.ecr.us-east-1.amazonaws.com/tensorflow-inference:2.5.1-cpu-py37-ubuntu18.04',
      'sklearn': '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3'
    };

    return runtimeMap[runtime] || runtimeMap['pytorch'];
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
      // Check EC2
      await this.ec2Client.send(new DescribeInstancesCommand({}));
      services.compute = true;
    } catch {}

    try {
      // Check S3
      await this.s3Client.send(new GetObjectCommand({
        Bucket: 'test-bucket',
        Key: 'test-file'
      }));
      services.storage = true;
    } catch {}

    try {
      // Check SageMaker
      await this.sagemakerClient.send(new CreateModelCommand({
        ModelName: 'test-model'
      }));
      services.ml = true;
    } catch {}

    return {
      status: Object.values(services).every(s => s) ? 'healthy' : 'unhealthy',
      services
    };
  }
}
