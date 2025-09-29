# De Palma Project

> "I'm not just a dispatcher. I'm the heart and soul of this operation!"  
> — Louie De Palma, Taxi

## What This Is

De Palma is an AI-powered task assignment system that mimics a human team member. Like Louie De Palma from Taxi, it's opinionated, efficient, and handles the grunt work of assigning tasks to the right people at the right time.

### Core Philosophy

- **Task assignment optimization** - not general coordination, focused on "who does what when"
- **Human-like team member** - communicates naturally, remembers context like a person would
- **Attention-based memory** - remembers what's relevant: things about itself, its skills, recent events
- **Extensible via MCP** - add new tools and skills as needed
- **Serverless AWS deployment** - scalable, low maintenance

## Technical Architecture

### Stack
- **Language**: TypeScript (except skill servers)
- **LLM**: Claude (via Anthropic API)
- **Deployment**: AWS Serverless (Lambda, API Gateway, DynamoDB, SES)
- **Integration Protocol**: MCP (Model Context Protocol)

### MVP Integrations

**Email (AWS SES)**
- Primary communication channel
- Receive task requests, send assignments

**Google Sheets (Tool MCP Server)**
- Team member data (names, skills, availability, workload)
- Task tracking and status
- Configuration data

**Task Scheduling (Skill MCP Server - Python)**
- Uses Google OR-Tools for optimization
- Constraint-based task assignment
- Considers: skills required, current workload, dependencies, deadlines

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   AWS Lambda                     │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │           De Palma Core                  │  │
│  │         (TypeScript/Claude)              │  │
│  └──────┬──────────────────────────────┬────┘  │
│         │                              │        │
│  ┌──────▼────────┐    ┌───────────────▼─────┐ │
│  │  Tool MCP     │    │   Skill MCP         │ │
│  │  Servers      │    │   Servers           │ │
│  │  (TypeScript) │    │   (Python)          │ │
│  └──────┬────────┘    └──────────┬──────────┘ │
│         │                        │             │
└─────────┼────────────────────────┼─────────────┘
          │                        │
    ┌─────▼─────┐           ┌──────▼──────┐
    │  Google   │           │  OR-Tools   │
    │  Sheets   │           │  Scheduler  │
    └───────────┘           └─────────────┘
          
    ┌─────────────────────┐
    │   AWS SES (Email)   │
    └─────────────────────┘
          
    ┌─────────────────────┐
    │   DynamoDB          │
    │   (State/Memory)    │
    └─────────────────────┘
```

## MCP Server Architecture

### Tool Servers vs. Skill Servers

**Tool Servers** (TypeScript)
- Interface with external systems (Google Sheets, Email, Calendar)
- CRUD operations, data retrieval
- Examples: sheets_tool, email_tool, calendar_tool

**Skill Servers** (Python or TypeScript)
- Specialized computational logic
- Complex algorithms, optimization
- Examples: task_scheduler_skill (Python/OR-Tools)

Both use MCP protocol, but skills encapsulate domain expertise while tools provide system access.

## Human-Like Memory System

### Attention-Inspired Memory

De Palma maintains context similar to how humans remember:

**High Attention (Always Available)**
1. **Self-referential**: Anything about De Palma's role, capabilities, limitations
2. **Skills & Responsibilities**: What De Palma can and should do
3. **Recent Context**: Last ~20 messages across all channels (sliding window)

**Medium Attention (Retrievable)**
4. **People Context**: Names, roles, skills, preferences mentioned recently
5. **Active Tasks**: Tasks currently being worked on or assigned
6. **Recent Decisions**: Assignment rationale from last 7 days

**Low Attention (Archived)**
7. **Historical Tasks**: Completed tasks (retrievable but not in active memory)
8. **Old Conversations**: Archived after 30 days unless referenced

### Implementation Strategy

```typescript
interface MemoryContext {
  // Always included in prompt
  self: {
    role: string;
    capabilities: string[];
    personality: string;
  };
  
  // Sliding window
  recentMessages: Message[]; // Last 20 messages
  
  // Active task state
  activeTasks: Task[];
  
  // People currently relevant
  activePeople: Person[];
  
  // Recent assignment decisions
  recentDecisions: Decision[];
}
```

Memory is stored in DynamoDB and assembled into Claude's context for each interaction.

## Personality: Louie De Palma

**Character Traits** (from Taxi):
- Gruff but effective
- Opinionated and direct
- Takes his job seriously
- Protective of his domain
- Gets results despite personality quirks
- No-nonsense communicator

**Communication Style**:
- Direct, efficient language
- Minimal pleasantries
- States assignments clearly
- Explains reasoning briefly when needed
- Signs emails as "Louie De Palma" initially, "Louie" in follow-ups

**Example Tone**:
```
Subject: Task Assignment - API Documentation

Alex,

You're on the API docs. Due Friday.

Why you? You wrote the endpoints, you document 'em. 
Plus Sarah's swamped with the mobile release.

Questions? You know where to find me.

- Louie
```

## MVP Use Case: Email-Based Task Assignment

### Workflow

1. **Request arrives via email**
   ```
   To: louie@depalma.work
   Subject: Need someone for API documentation
   
   We need the API endpoints documented by Friday for the client demo.
   Needs someone who understands the authentication flow.
   ```

2. **De Palma processes**
   - Extracts: task (API docs), deadline (Friday), requirements (auth knowledge)
   - Queries Google Sheets for team data
   - Calls task_scheduler_skill with constraints
   - Gets optimal assignment

3. **De Palma assigns**
   ```
   To: alex@team.com
   Cc: requestor@team.com
   Subject: Task Assignment - API Documentation
   
   Alex,
   
   You're on the API docs. Due Friday.
   
   Why you? You wrote the endpoints, you document 'em.
   Plus Sarah's swamped with the mobile release.
   
   Questions? You know where to find me.
   
   - Louie
   ```

4. **Updates Google Sheets**
   - Marks task assigned
   - Updates Alex's workload
   - Logs assignment rationale

## Google Sheets Schema

### Team Members Sheet
```
| Name  | Email           | Skills              | Current_Workload | Availability |
|-------|-----------------|---------------------|------------------|--------------|
| Alex  | alex@team.com   | backend,api,docs    | 30               | available    |
| Sarah | sarah@team.com  | mobile,frontend,api | 45               | available    |
```

### Tasks Sheet
```
| Task_ID | Description    | Assigned_To | Status    | Deadline   | Skills_Required |
|---------|----------------|-------------|-----------|------------|-----------------|
| T001    | API docs       | Alex        | assigned  | 2025-03-15 | backend,docs    |
```

### Assignment History Sheet
```
| Timestamp  | Task_ID | Assigned_To | Rationale                                    |
|------------|---------|-------------|----------------------------------------------|
| 2025-03-10 | T001    | Alex        | Best match: wrote endpoints, lower workload  |
```

## Task Scheduling Skill (Python/OR-Tools)

### Input
```json
{
  "task": {
    "id": "T001",
    "description": "API documentation",
    "deadline": "2025-03-15",
    "estimated_hours": 8,
    "skills_required": ["backend", "docs"]
  },
  "team": [
    {
      "name": "Alex",
      "skills": ["backend", "api", "docs"],
      "current_workload": 30,
      "availability": "available"
    },
    {
      "name": "Sarah",
      "skills": ["mobile", "frontend", "api"],
      "current_workload": 45,
      "availability": "available"
    }
  ]
}
```

### Output
```json
{
  "assignment": {
    "assignee": "Alex",
    "confidence": 0.92,
    "rationale": "Best skill match (backend+docs), lower workload (30 vs 45), available"
  },
  "alternatives": [
    {
      "assignee": "Sarah",
      "confidence": 0.65,
      "rationale": "Has API experience but mobile-focused, already high workload"
    }
  ]
}
```

### OR-Tools Constraints
- Skill matching score
- Workload balancing
- Deadline feasibility
- Availability status
- Historical performance (future)

## AWS Serverless Architecture

### Lambda Functions

**email-receiver** (TypeScript)
- Triggered by SES
- Parses incoming email
- Extracts task request
- Invokes orchestrator

**orchestrator** (TypeScript)
- Core De Palma logic
- Claude integration
- Coordinates MCP servers
- Memory management

**email-sender** (TypeScript)
- Sends assignment emails via SES
- Templates for different message types

### API Gateway
- Webhook endpoints for tools
- Health checks
- Manual task submission (future web UI)

### DynamoDB Tables

**Memory**
- Recent messages (TTL: 30 days)
- Active tasks
- People context
- Decision history

**State**
- Task assignments
- Team member status
- Configuration

### S3 (Optional)
- Email attachments
- Logs and audit trail

## Development Priorities

### Phase 1: Core Email Loop
1. ✅ Initialize TypeScript serverless project (AWS CDK or Serverless Framework)
2. ✅ Email receiver Lambda (SES integration)
3. ✅ Basic Claude integration
4. ✅ Email sender Lambda
5. ✅ DynamoDB schema and basic memory

### Phase 2: Task Assignment
6. ✅ Google Sheets tool MCP server (TypeScript)
7. ✅ Task scheduler skill MCP server (Python/OR-Tools)
8. ✅ Orchestration logic to coordinate tools/skills
9. ✅ Assignment workflow end-to-end

### Phase 3: Polish
10. ✅ Louie personality prompts
11. ✅ Attention-based memory implementation
12. ✅ Error handling and logging
13. ✅ Testing and validation

## Configuration

### Environment Variables
```bash
CLAUDE_API_KEY=sk-...
GOOGLE_SHEETS_ID=1abc...
EMAIL_DOMAIN=depalma.work
AWS_REGION=us-east-1
DYNAMODB_TABLE_MEMORY=depalma-memory
DYNAMODB_TABLE_STATE=depalma-state
```

### Deployment
```bash
npm run deploy:dev    # Deploy to development
npm run deploy:prod   # Deploy to production
```

## MCP Server Development

### Tool Server Template (TypeScript)
```typescript
interface MCPToolServer {
  name: string;
  description: string;
  tools: Tool[];
  execute(toolName: string, args: any): Promise<any>;
}
```

### Skill Server Template (Python)
```python
class MCPSkillServer:
    def __init__(self):
        self.name = "task_scheduler"
        self.skills = [...]
    
    async def execute(self, skill_name: str, args: dict) -> dict:
        # Skill logic here
        pass
```

## Extensibility

Add new capabilities by creating MCP servers:

**Potential Tools**:
- Slack tool (team communication)
- Calendar tool (availability checking)
- GitHub tool (code task tracking)

**Potential Skills**:
- Workload predictor (ML-based task duration estimation)
- Skill matcher (better team-to-task matching)
- Priority ranker (intelligent task prioritization)

## Open Questions

- Email address: `louie@depalma.work` for production, configurable for different deployments
- How to handle conflicting task requests (priority rules?)
- What if no one has the required skills? (escalation logic)
- Should De Palma decline tasks outside his domain? (boundary setting)
- Monitoring and observability strategy (CloudWatch? Custom dashboards?)

## Testing Strategy

### Unit Tests
- Individual Lambda functions
- MCP server logic
- Memory management

### Integration Tests
- Email → Assignment → Email flow
- Google Sheets updates
- OR-Tools scheduling

### E2E Tests
- Full workflow with mock email
- Verify Google Sheets updates
- Confirm assignment email sent

## Getting Started

When beginning development:

1. **Initialize serverless TypeScript project**
   - Use AWS CDK or Serverless Framework
   - Set up TypeScript with proper tooling
   - Configure AWS credentials

2. **Create basic email receiver**
   - SES integration
   - Parse email body
   - Log to CloudWatch

3. **Add Claude integration**
   - API client
   - Basic prompting
   - Test with simple responses

4. **Build Google Sheets tool MCP**
   - Read team members
   - Read/write tasks
   - Update assignment history

5. **Implement task scheduler skill**
   - Python OR-Tools setup
   - Basic constraint solving
   - Return assignment recommendation

6. **Connect everything in orchestrator**
   - Coordinate MCP servers
   - Memory assembly
   - Assignment workflow

Start simple: hardcode test data, manual deployments, basic logic. Add sophistication after the core loop works.