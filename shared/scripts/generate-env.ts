import { ConfigLoader } from '../cloud/config-loader';
import * as fs from 'fs';
import * as path from 'path';

const envContent = ConfigLoader.generateEnvExample();
const envPath = path.join(__dirname, '..', '.env.example');

fs.writeFileSync(envPath, envContent);
console.log(`Environment example file created at: ${envPath}`);
console.log('\nTo use this configuration:');
console.log('1. Copy .env.example to .env');
console.log('2. Fill in your cloud provider credentials');
console.log('3. Set CLOUD_PROVIDER to either "aws" or "azure"');
