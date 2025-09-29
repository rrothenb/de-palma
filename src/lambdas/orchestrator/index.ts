import { Context } from 'aws-lambda';
import { LambdaClient, InvokeCommand } from '@aws-sdk/client-lambda';
import { ClaudeClient } from '@/lib/claude';
import { MemoryService } from '@/lib/memory';
import { OrchestratorEvent, Task, EmailSenderEvent, TaskAssignment } from '@/types';
import { v4 as uuidv4 } from 'uuid';

const lambdaClient = new LambdaClient({ region: process.env.AWS_REGION || 'us-east-1' });
const claudeClient = new ClaudeClient(process.env.CLAUDE_API_KEY!);
const memoryService = new MemoryService(
  process.env.AWS_REGION || 'us-east-1',
  process.env.DYNAMODB_TABLE_MEMORY!
);

export const handler = async (event: OrchestratorEvent, context: Context) => {
  console.log('Orchestrator triggered:', JSON.stringify(event, null, 2));

  try {
    switch (event.type) {
      case 'email_received':
        return await handleEmailReceived(event);
      case 'manual_task':
        return await handleManualTask(event);
      case 'health_check':
        return await handleHealthCheck();
      default:
        throw new Error(`Unknown event type: ${event.type}`);
    }
  } catch (error) {
    console.error('Orchestrator error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Internal server error' }),
    };
  }
};

async function handleEmailReceived(event: OrchestratorEvent): Promise<any> {
  const { email, taskRequest, message } = event.data;

  console.log(`Processing task request: ${taskRequest.description}`);

  // Build memory context
  const memoryContext = await memoryService.buildMemoryContext();

  // Create task object
  const task: Task = {
    id: uuidv4(),
    description: taskRequest.description,
    deadline: taskRequest.deadline,
    skillsRequired: taskRequest.skillsRequired,
    priority: taskRequest.priority || 'medium',
    status: 'pending',
    requestedBy: email.from,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  // Store task in memory
  await memoryService.storeActiveTask(task);

  // Get team data from Google Sheets (via MCP)
  const teamData = await getTeamDataFromSheets();

  // Get task assignment recommendation from scheduler
  const schedulerRecommendation = await getSchedulerRecommendation(task, teamData);

  // Generate assignment decision with Claude
  const assignmentDecision = await claudeClient.generateAssignment(
    task.description,
    teamData,
    schedulerRecommendation,
    memoryContext
  );

  // Update task with assignment
  task.assignedTo = assignmentDecision.assignee;
  task.status = 'assigned';
  task.updatedAt = new Date().toISOString();

  await memoryService.storeActiveTask(task);

  // Store assignment decision
  await memoryService.storeDecision({
    taskId: task.id,
    assignedTo: assignmentDecision.assignee,
    rationale: assignmentDecision.rationale,
    timestamp: new Date().toISOString(),
    confidence: schedulerRecommendation.assignment?.confidence || 0.8,
  });

  // Send assignment email
  const assigneeEmail = findTeamMemberEmail(assignmentDecision.assignee, teamData);
  if (assigneeEmail) {
    await sendAssignmentEmail({
      assignee: assignmentDecision.assignee,
      assigneeEmail,
      ccEmails: [email.from], // CC the requester
      subject: assignmentDecision.emailSubject,
      body: assignmentDecision.emailBody,
      taskId: task.id,
    });
  }

  return {
    statusCode: 200,
    body: JSON.stringify({
      message: 'Task assigned successfully',
      task: task,
      assignment: assignmentDecision,
    }),
  };
}

async function handleManualTask(event: OrchestratorEvent): Promise<any> {
  // Similar to handleEmailReceived but for manual task submissions
  return {
    statusCode: 200,
    body: JSON.stringify({ message: 'Manual task handling not implemented yet' }),
  };
}

async function handleHealthCheck(): Promise<any> {
  const memoryStats = await memoryService.getMemoryStats();

  return {
    statusCode: 200,
    body: JSON.stringify({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      memory: memoryStats,
      environment: process.env.ENVIRONMENT,
    }),
  };
}

async function getTeamDataFromSheets(): Promise<any> {
  // This would use the Google Sheets MCP server
  // For now, return mock data
  return [
    {
      name: 'Alex',
      email: 'alex@team.com',
      skills: ['backend', 'api', 'docs'],
      currentWorkload: 30,
      availability: 'available',
    },
    {
      name: 'Sarah',
      email: 'sarah@team.com',
      skills: ['mobile', 'frontend', 'api'],
      currentWorkload: 45,
      availability: 'available',
    },
  ];
}

async function getSchedulerRecommendation(task: Task, teamData: any): Promise<any> {
  // This would call the custom task-scheduler MCP server
  // For now, return mock recommendation
  return {
    assignment: {
      assignee: teamData[0].name, // Simple: pick first available person
      confidence: 0.85,
      rationale: 'Best skill match and lowest workload',
    },
    alternatives: [
      {
        assignee: teamData[1]?.name,
        confidence: 0.65,
        rationale: 'Has some relevant skills but higher workload',
      },
    ],
  };
}

function findTeamMemberEmail(name: string, teamData: any[]): string | undefined {
  const member = teamData.find(m => m.name === name);
  return member?.email;
}

async function sendAssignmentEmail(params: {
  assignee: string;
  assigneeEmail: string;
  ccEmails: string[];
  subject: string;
  body: string;
  taskId: string;
}): Promise<void> {
  const functionName = process.env.EMAIL_SENDER_FUNCTION_NAME ||
    `depalma-email-sender-${process.env.ENVIRONMENT || 'dev'}`;

  const emailEvent: EmailSenderEvent = {
    type: 'assignment_email',
    emailData: {
      to: [params.assigneeEmail, ...params.ccEmails],
      subject: params.subject,
      body: params.body,
    },
    taskId: params.taskId,
  };

  const command = new InvokeCommand({
    FunctionName: functionName,
    InvocationType: 'Event', // Asynchronous
    Payload: JSON.stringify(emailEvent),
  });

  try {
    await lambdaClient.send(command);
    console.log(`Assignment email queued for ${params.assignee}`);
  } catch (error) {
    console.error('Failed to queue assignment email:', error);
    throw error;
  }
}

// Health check handler (separate export for API Gateway)
export const healthHandler = async () => {
  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      service: 'de-palma-orchestrator',
    }),
  };
};