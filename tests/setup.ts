/**
 * Jest test setup
 * Runs before each test file
 */

// Mock AWS SDK clients
jest.mock('@aws-sdk/client-dynamodb');
jest.mock('@aws-sdk/client-ses');
jest.mock('@aws-sdk/client-lambda');
jest.mock('@aws-sdk/lib-dynamodb');

// Mock Anthropic SDK
jest.mock('@anthropic-ai/sdk');

// Set up test environment variables
process.env.NODE_ENV = 'test';
process.env.ENVIRONMENT = 'test';
process.env.CLAUDE_API_KEY = 'test-claude-key';
process.env.GOOGLE_SHEETS_ID = 'test-sheets-id';
process.env.EMAIL_DOMAIN = 'test.depalma.work';
process.env.DYNAMODB_TABLE_MEMORY = 'test-memory-table';
process.env.DYNAMODB_TABLE_STATE = 'test-state-table';
process.env.AWS_REGION = 'us-east-1';

// Extend Jest matchers if needed
// import './custom-matchers';

// Global test utilities
global.createMockSESEvent = (from: string, subject: string, to: string[] = ['louie@test.depalma.work']) => ({
  Records: [
    {
      eventSource: 'aws:ses',
      eventVersion: '1.0',
      ses: {
        mail: {
          messageId: 'test-message-id',
          source: from,
          destination: to,
          commonHeaders: {
            subject: subject,
            from: [from],
            to: to,
          },
        },
        receipt: {
          timestamp: new Date().toISOString(),
          recipients: to,
        },
      },
    },
  ],
});

global.createMockTeamData = () => [
  {
    name: 'Alice',
    email: 'alice@test.com',
    skills: ['backend', 'api', 'python'],
    currentWorkload: 25,
    availability: 'available',
  },
  {
    name: 'Bob',
    email: 'bob@test.com',
    skills: ['frontend', 'react', 'typescript'],
    currentWorkload: 35,
    availability: 'available',
  },
  {
    name: 'Charlie',
    email: 'charlie@test.com',
    skills: ['devops', 'aws', 'docker'],
    currentWorkload: 40,
    availability: 'busy',
  },
];

// Console spy to reduce noise in tests
const originalConsole = console;
beforeEach(() => {
  global.console = {
    ...originalConsole,
    log: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
  };
});

afterEach(() => {
  global.console = originalConsole;
  jest.clearAllMocks();
});