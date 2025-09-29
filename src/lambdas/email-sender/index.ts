import { Context } from 'aws-lambda';
import { SESService } from '@/lib/ses';
import { MemoryService } from '@/lib/memory';
import { EmailSenderEvent, Message } from '@/types';
import { v4 as uuidv4 } from 'uuid';

const sesService = new SESService(
  process.env.AWS_REGION || 'us-east-1',
  process.env.EMAIL_DOMAIN!
);

const memoryService = new MemoryService(
  process.env.AWS_REGION || 'us-east-1',
  process.env.DYNAMODB_TABLE_MEMORY!
);

export const handler = async (event: EmailSenderEvent, context: Context) => {
  console.log('Email sender triggered:', JSON.stringify(event, null, 2));

  try {
    switch (event.type) {
      case 'assignment_email':
        return await sendAssignmentEmail(event);
      case 'notification_email':
        return await sendNotificationEmail(event);
      default:
        throw new Error(`Unknown email type: ${event.type}`);
    }
  } catch (error) {
    console.error('Email sender error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Failed to send email' }),
    };
  }
};

async function sendAssignmentEmail(event: EmailSenderEvent): Promise<any> {
  const { emailData, taskId } = event;

  try {
    // Extract assignee from the first email address (assuming first is assignee, rest are CC)
    const assigneeEmail = emailData.to[0];
    const ccEmails = emailData.to.slice(1);

    // Send the email
    await sesService.sendAssignmentEmail(
      'Unknown', // We don't have the name in this context
      assigneeEmail,
      ccEmails,
      emailData.subject,
      emailData.body,
      taskId
    );

    // Store sent email in memory for context
    const sentMessage: Message = {
      id: uuidv4(),
      from: `louie@${process.env.EMAIL_DOMAIN}`,
      to: assigneeEmail,
      subject: emailData.subject,
      body: emailData.body,
      timestamp: new Date().toISOString(),
      type: 'outgoing',
    };

    await memoryService.storeMessage(sentMessage);

    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Assignment email sent successfully',
        taskId: taskId,
        recipients: emailData.to,
      }),
    };
  } catch (error) {
    console.error('Failed to send assignment email:', error);
    throw error;
  }
}

async function sendNotificationEmail(event: EmailSenderEvent): Promise<any> {
  const { emailData } = event;

  try {
    // Send notification email
    await sesService.sendNotificationEmail(
      emailData.to,
      emailData.subject,
      emailData.body
    );

    // Store sent email in memory
    const sentMessage: Message = {
      id: uuidv4(),
      from: `louie@${process.env.EMAIL_DOMAIN}`,
      to: emailData.to[0],
      subject: emailData.subject,
      body: emailData.body,
      timestamp: new Date().toISOString(),
      type: 'outgoing',
    };

    await memoryService.storeMessage(sentMessage);

    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Notification email sent successfully',
        recipients: emailData.to,
      }),
    };
  } catch (error) {
    console.error('Failed to send notification email:', error);
    throw error;
  }
}