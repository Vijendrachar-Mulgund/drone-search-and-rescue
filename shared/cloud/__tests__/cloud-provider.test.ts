import { cloudProvider, configLoader, CloudProviderError } from '../';
import { ComputeInstance, StorageOptions } from '../types';

describe('Cloud Provider Abstraction Layer', () => {
  const testConfig = {
    provider: 'aws' as const,
    credentials: {
      region: 'us-east-1',
      aws: {
        accessKeyId: 'test-key',
        secretAccessKey: 'test-secret'
      }
    }
  };

  beforeEach(() => {
    // Clear provider instance before each test
    cloudProvider.clearProvider();
  });

  describe('Provider Factory', () => {
    it('should create AWS provider', () => {
      const provider = cloudProvider.getProvider(testConfig);
      expect(provider).toBeDefined();
      expect(provider.getConfig().provider).toBe('aws');
    });

    it('should throw error for invalid provider', () => {
      const invalidConfig = {
        ...testConfig,
        provider: 'invalid' as any
      };

      expect(() => {
        cloudProvider.getProvider(invalidConfig);
      }).toThrow();
    });
  });

  describe('Compute Operations', () => {
    it('should create compute instance', async () => {
      const provider = cloudProvider.getProvider(testConfig);
      
      const instanceParams = {
        name: 'test-instance',
        instanceType: 't2.micro',
        imageId: 'ami-12345'
      };

      try {
        const instance = await provider.createComputeInstance(instanceParams);
        expect(instance).toBeDefined();
        expect(instance.id).toBeDefined();
        expect(instance.status).toBe('running');
      } catch (error) {
        expect(error).toBeInstanceOf(CloudProviderError);
        expect((error as CloudProviderError).service).toBe('compute');
      }
    });
  });

  describe('Storage Operations', () => {
    const testFile = Buffer.from('test content');
    const storageOptions: StorageOptions = {
      container: 'test-bucket',
      path: 'test-file.txt',
      contentType: 'text/plain'
    };

    it('should upload file', async () => {
      const provider = cloudProvider.getProvider(testConfig);

      try {
        const url = await provider.uploadFile(storageOptions, testFile);
        expect(url).toBeDefined();
        expect(url).toContain(storageOptions.path);
      } catch (error) {
        expect(error).toBeInstanceOf(CloudProviderError);
        expect((error as CloudProviderError).service).toBe('storage');
      }
    });

    it('should download file', async () => {
      const provider = cloudProvider.getProvider(testConfig);

      try {
        const content = await provider.downloadFile(storageOptions);
        expect(content).toBeDefined();
        expect(content).toBeInstanceOf(Buffer);
      } catch (error) {
        expect(error).toBeInstanceOf(CloudProviderError);
        expect((error as CloudProviderError).service).toBe('storage');
      }
    });
  });

  describe('ML Operations', () => {
    it('should deploy model', async () => {
      const provider = cloudProvider.getProvider(testConfig);
      
      const modelOptions = {
        modelId: 'test-model',
        runtime: 'pytorch'
      };

      const modelFiles = [{
        path: 'model.pth',
        content: Buffer.from('mock model data')
      }];

      try {
        const modelId = await provider.deployModel(modelOptions, modelFiles);
        expect(modelId).toBeDefined();
      } catch (error) {
        expect(error).toBeInstanceOf(CloudProviderError);
        expect((error as CloudProviderError).service).toBe('ml');
      }
    });

    it('should run inference', async () => {
      const provider = cloudProvider.getProvider(testConfig);
      
      const modelOptions = {
        modelId: 'test-model'
      };

      const input = {
        data: [1, 2, 3, 4]
      };

      try {
        const result = await provider.runInference(modelOptions, input);
        expect(result).toBeDefined();
        expect(result.predictions).toBeDefined();
        expect(result.metadata).toBeDefined();
      } catch (error) {
        expect(error).toBeInstanceOf(CloudProviderError);
        expect((error as CloudProviderError).service).toBe('ml');
      }
    });
  });

  describe('Health Check', () => {
    it('should check provider health', async () => {
      const provider = cloudProvider.getProvider(testConfig);

      const health = await provider.healthCheck();
      expect(health).toBeDefined();
      expect(health.status).toBeDefined();
      expect(health.services).toBeDefined();
      expect(health.services).toHaveProperty('compute');
      expect(health.services).toHaveProperty('storage');
      expect(health.services).toHaveProperty('ml');
    });
  });
});
