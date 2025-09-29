import { SESEvent, Context, SESEventRecord } from 'aws-lambda';
import { LambdaClient, InvokeCommand } from '@aws-sdk/client-lambda';
import { SESService } from '@/lib/ses';
import { MemoryService } from '@/lib/memory';
import { Message, OrchestratorEvent } from '@/types';

const lambdaClient = new LambdaClient({ region: process.env.AWS_REGION || 'us-east-1' });
const memoryService = new MemoryService(
  process.env.AWS_REGION || 'us-east-1',
  process.env.DYNAMODB_TABLE_MEMORY!
);

export const handler = async (event: SESEvent, context: Context) => {
  console.log('Email receiver triggered:', JSON.stringify(event, null, 2));

  try {
    for (const record of event.Records) {
      await processEmailRecord(record);
    }

    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Emails processed successfully' }),
    };
  } catch (error) {
    console.error('Error processing emails:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Failed to process emails' }),
    };
  }
};

async function processEmailRecord(record: SESEventRecord): Promise<void> {
  const emailData = SESService.parseEmailEvent(record);

  console.log(`Processing email from ${emailData.from}: ${emailData.subject}`);

  // Create message object for memory
  const message: Message = {
    id: emailData.messageId,
    from: emailData.from,
    to: emailData.to[0], // Primary recipient (should be louie@depalma.work)
    subject: emailData.subject,
    body: '', // SES doesn't provide body in the event, would need S3 retrieval for full email
    timestamp: emailData.timestamp,
    type: 'incoming',
  };

  // Store message in memory
  await memoryService.storeMessage(message);

  // Extract task request from email
  const taskRequest = SESService.extractTaskRequest(emailData.subject, '');

  // Prepare orchestrator event
  const orchestratorEvent: OrchestratorEvent = {
    type: 'email_received',
    data: {
      email: emailData,
      taskRequest,
      message,
    },
    source: 'email-receiver',
  };

  // Invoke orchestrator asynchronously
  await invokeOrchestrator(orchestratorEvent);
}

async function invokeOrchestrator(event: OrchestratorEvent): Promise<void> {
  const functionName = process.env.ORCHESTRATOR_FUNCTION_NAME ||
    `depalma-orchestrator-${process.env.ENVIRONMENT || 'dev'}`;

  const command = new InvokeCommand({
    FunctionName: functionName,
    InvocationType: 'Event', // Asynchronous invocation
    Payload: JSON.stringify(event),
  });

  try {
    await lambdaClient.send(command);
    console.log('Orchestrator invoked successfully');
  } catch (error) {
    console.error('Failed to invoke orchestrator:', error);
    throw error;
  }
}