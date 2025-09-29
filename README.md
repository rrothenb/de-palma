# De Palma 🚕

> *"I'm not just a dispatcher. I'm the heart and soul of this operation!"*
> — Louie De Palma, Taxi

AI-powered task assignment system that mimics a human team member. Like Louie De Palma from Taxi, it's opinionated, efficient, and handles the grunt work of assigning tasks to the right people at the right time.

## 🎯 What This Is

De Palma is a **serverless AWS application** that automatically assigns tasks to your team members based on:

- **Skills matching** - Matches required skills with team capabilities
- **Workload balancing** - Considers current workload and availability
- **Optimization** - Uses Google OR-Tools for optimal assignments
- **Human-like memory** - Remembers context like a real team member
- **Email integration** - Communicates naturally via email

## 🏗️ Architecture

```
Email Request → SES → Lambda → Louie (Claude) → Assignment Email
                        ↓
                   Google Sheets (team data)
                        ↓
                   OR-Tools (optimization)
                        ↓
                   DynamoDB (memory)
```

**Tech Stack:**
- **Runtime**: Node.js 18+ with TypeScript
- **Infrastructure**: AWS Serverless (SAM)
- **AI**: Anthropic Claude
- **Optimization**: Python + Google OR-Tools (MCP Server)
- **Data**: Google Sheets + DynamoDB
- **Communication**: AWS SES

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.8+
- AWS CLI configured
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)

### Setup

```bash
# Clone and setup
git clone <your-repo>
cd de-palma

# Run setup script
./scripts/setup-dev.sh

# Configure environment
cp .env.example .env
# Edit .env with your values

# Deploy to development
./scripts/deploy.sh dev
```

### Required Environment Variables

```bash
CLAUDE_API_KEY=your_anthropic_api_key
GOOGLE_SHEETS_ID=your_google_sheets_id
EMAIL_DOMAIN=your-domain.com
```

## 📧 How It Works

### 1. Send Task Request
```
To: louie@your-domain.com
Subject: Need API documentation

We need the REST API endpoints documented by Friday.
Requires someone familiar with the authentication system.
```

### 2. Louie Processes & Assigns
- Extracts task requirements (skills, deadline, priority)
- Queries Google Sheets for team data
- Uses OR-Tools for optimal assignment
- Applies Louie's personality and judgment

### 3. Assignment Email Sent
```
To: alex@team.com
Cc: requester@team.com
Subject: Task Assignment - API Documentation

Alex,

You're on the API docs. Due Friday.

Why you? You wrote the endpoints, you document 'em.
Plus Sarah's swamped with the mobile release.

Questions? You know where to find me.

- Louie
```

## 📊 Google Sheets Setup

Create a Google Sheet with these tabs:

### Team Members
| Name | Email | Skills | Current_Workload | Availability |
|------|-------|--------|------------------|--------------|
| Alex | alex@team.com | backend,api,docs | 30 | available |
| Sarah | sarah@team.com | mobile,frontend,ui | 45 | available |

### Tasks (auto-updated)
| Task_ID | Description | Assigned_To | Status | Deadline | Skills_Required |
|---------|-------------|-------------|---------|----------|-----------------|
| T001 | API docs | Alex | assigned | 2025-03-15 | backend,docs |

## 🧠 Memory System

De Palma maintains human-like memory:

**High Attention** (always available):
- Self-awareness (role, capabilities)
- Recent messages (last 20)
- Active tasks
- Current team context

**Medium Attention** (retrievable):
- Assignment decisions (last 7 days)
- Team member details
- Task history

**Low Attention** (archived):
- Completed tasks
- Old conversations

## 🛠️ Development

### Local Development
```bash
# Start development server
npm run dev

# Run tests
npm test

# Lint code
npm run lint

# Build
npm run build
```

### Project Structure
```
de-palma/
├── src/
│   ├── lambdas/           # AWS Lambda functions
│   │   ├── email-receiver/    # SES event handler
│   │   ├── orchestrator/      # Core Louie logic
│   │   └── email-sender/      # Email sending
│   ├── lib/               # Shared utilities
│   │   ├── claude/            # Anthropic integration
│   │   ├── memory/            # DynamoDB memory
│   │   ├── ses/               # Email utilities
│   │   └── types/             # TypeScript types
│   └── mcp-servers/       # Model Context Protocol servers
│       └── task-scheduler/    # Python OR-Tools optimizer
├── tests/                 # Test files
├── scripts/               # Deployment scripts
└── template.yaml          # SAM infrastructure
```

### Testing
```bash
# Unit tests
npm test

# Integration tests
npm run test:integration

# Test with mock data
npm run test:mock
```

## 🚀 Deployment

### Development
```bash
./scripts/deploy.sh dev
```

### Production
```bash
./scripts/deploy.sh prod
```

### Post-Deployment Setup

1. **Configure SES**: Verify your email domain
2. **Setup Google Sheets**: Create sheets with team data
3. **Test Health**: Visit `https://api-url/health`
4. **Send Test Email**: Email `louie@your-domain.com`

## 📈 Monitoring

- **CloudWatch**: Lambda logs and metrics
- **Health Check**: `GET /health` endpoint
- **Memory Stats**: Built-in memory statistics
- **Assignment History**: Tracked in Google Sheets

## 🔧 Configuration

### Environment Variables
See `.env.example` for all configuration options.

### Louie's Personality
Customize Louie's communication style by updating the personality prompts in `src/lib/claude/index.ts`.

### Assignment Logic
Modify optimization constraints in `src/mcp-servers/task-scheduler/scheduler.py`.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `npm test`
5. Commit: `git commit -m "Add feature"`
6. Push: `git push origin feature-name`
7. Create Pull Request

## 📜 License

MIT License - see [LICENSE](LICENSE) file.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/de-palma/issues)
- **Documentation**: See [CLAUDE.md](CLAUDE.md) for detailed architecture
- **Health Check**: `https://your-api-url/health`

---

*"Listen up! I assign the tasks around here, and I do it better than any algorithm. Why? Because I know people. I know who can handle what, when they can handle it, and most importantly, I know how to get results."* — Louie De Palma
