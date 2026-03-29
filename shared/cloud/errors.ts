import { CloudProvider } from './types';

export type CloudService = 'compute' | 'storage' | 'ml';

export class CloudProviderError extends Error {
  constructor(
    message: string,
    public readonly provider: CloudProvider,
    public readonly service: CloudService,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'CloudProviderError';

    // Maintain proper stack trace
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, CloudProviderError);
    }
  }

  static fromError(
    error: Error,
    provider: CloudProvider,
    service: CloudService
  ): CloudProviderError {
    return new CloudProviderError(
      `${provider.toUpperCase()} ${service} error: ${error.message}`,
      provider,
      service,
      error
    );
  }
}

export class ConfigurationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigurationError';

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ConfigurationError);
    }
  }
}

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ValidationError);
    }
  }
}

// Helper function to wrap provider operations with error handling
export async function wrapProviderOperation<T>(
  operation: () => Promise<T>,
  provider: CloudProvider,
  service: CloudService
): Promise<T> {
  try {
    return await operation();
  } catch (error) {
    if (error instanceof CloudProviderError) {
      throw error;
    }
    throw CloudProviderError.fromError(error as Error, provider, service);
  }
}
