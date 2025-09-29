# De Palma - Volunteer Scheduling for CCB

> "I'm not just a dispatcher. I'm the heart and soul of this operation!"  
> — Louie De Palma, Taxi

## What This Is

De Palma is an AI-powered volunteer scheduling assistant for **CCB Lille** (and similar organizations). It automates the tedious work of matching volunteers to teaching slots, handling substitutions, and ensuring every English conversation class is covered.

### Core Use Case: CCB Lille

**CCB (Centre Culturel Britannique de Lille)** is a bilingual library that helps French people learn English through:
- Conversation classes (beginner, intermediate, advanced levels)
- Reading clubs  
- Children's story time ("heure du conte")
- Library services
- Cultural events

**Current Problem:** Volunteer scheduling is done manually with Excel spreadsheets. It's time-consuming and error-prone.

### Core Philosophy

- **Never cancel a class due to volunteer scheduling issues**
- **Minimize coordinator workload** - automate the tedious matching work
- **Natural language interface** - coordinators interact via email like talking to a person
- **Respect volunteer preferences** while ensuring coverage
- **Extensible** - start with CCB, expand to other volunteer organizations later

## Technical Architecture

### Stack
- **Language**: TypeScript (except skill servers)
- **LLM**: Claude (via Anthropic API)
- **Deployment**: AWS SAM (Serverless Application Model)
- **AWS Services**: Lambda, API Gateway, DynamoDB, SES
- **Integration Protocol**: MCP (Model Context Protocol)

### MVP Integrations

**Email (AWS SES)**
- Primary communication channel
- Receive scheduling requests from coordinators
- Send confirmations to volunteers

**Google Sheets (Tool MCP Server)**
- Volunteer data (names, skills, availability, contact info)
- Class schedule and coverage tracking
- Substitute history and preferences

**Volunteer Scheduler (Skill MCP Server - Python)**
- Uses Google OR-Tools for optimization
- Constraint-based volunteer matching
- Considers: teaching experience, availability, preferences, reliability

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

## Google Sheets Schema

### Volunteers Sheet
```
| Name     | Email              | Teaching_Level      | Languages | Availability_Days | Availability_Times | Background_Check | Preferred_Classes |
|----------|-------------------|---------------------|-----------|-------------------|-------------------|------------------|-------------------|
| Marie    | marie@email.com   | beginner,intermediate| EN,FR    | Mon,Wed,Thu       | 18:00-20:00      | Yes              | conversation     |
| Paul     | paul@email.com    | intermediate,advanced| EN,FR    | Tue,Thu,Sat       | 14:00-18:00      | Yes              | reading_club     |
| Sophie   | sophie@email.com  | beginner,kids       | EN,FR    | Mon,Wed,Fri       | 16:00-18:00      | Yes              | story_time       |
```

**Key Fields:**
- **Teaching_Level**: beginner, intermediate, advanced, kids
- **Availability_Days**: Days of week available
- **Availability_Times**: Time ranges (24h format)
- **Background_Check**: Required for children's programs
- **Preferred_Classes**: conversation, reading_club, story_time, cultural_events

### Class Schedule Sheet
```
| Class_ID | Day   | Time        | Type         | Level        | Volunteer_Assigned | Status    | Students_Expected |
|----------|-------|-------------|--------------|--------------|-------------------|-----------|------------------|
| C001     | Thu   | 18:00-19:30 | conversation | intermediate | Marie             | confirmed | 8                |
| C002     | Tue   | 14:00-15:30 | reading_club | advanced     | Paul              | confirmed | 5                |
| C003     | Wed   | 16:00-17:00 | story_time   | kids         | Sophie            | confirmed | 12               |
```

### Substitution History Sheet
```
| Date       | Original_Volunteer | Substitute | Class_ID | Reason          | Success |
|------------|-------------------|------------|----------|-----------------|---------|
| 2025-03-10 | Marie             | Jean       | C001     | illness         | yes     |
| 2025-03-05 | Paul              | Marie      | C002     | vacation        | yes     |
```

## Personality: Louie De Palma

**Character Traits** (from Taxi):
- Gruff but effective
- Opinionated and direct  
- Takes scheduling seriously
- Protective of "his" operation
- Gets results despite personality quirks
- No-nonsense communicator
- Doesn't suffer fools

**Communication Style**:
- Direct, no fluff
- States facts clearly
- Explains reasoning briefly (because it's obvious)
- Minimal pleasantries
- Expects people to show up when they say they will
- Signs emails as "Louie De Palma" initially, "Louie" in follow-ups

**Tone adapts slightly for volunteers vs. corporate:**
- Still gruff and direct
- Acknowledges it's volunteer work (not paid jobs)
- But expects reliability and follow-through
- "You said you'd be there, so be there"

**Example Tone**:
```
Subject: Thursday Class - You're On

Marie,

Thursday 18:00-19:30, intermediate conversation. 8 students.

You're doing it because you can handle intermediate and you said 
Thursdays work for you. Plus you're actually good at this.

Show up on time.

- Louie
```

**For Substitution Requests:**
```
Subject: Marie's Out - You're Covering

Jean,

Marie's sick. You're covering her Thursday 18:00 class.

I know you can do it - you subbed for her last month and the 
students didn't even complain. Intermediate level, 8 students.

Don't make me regret this.

- Louie
```

**For Capacity Checks:**
```
Subject: Can We Do Wednesday Beginners?

Yeah, we can do it.

Sophie's got Wednesday evenings open and she needs more hours anyway. 
She's good with beginners. Not great, but good enough.

Want me to set it up or what?

- Louie
```

## MVP Use Case: Email-Based Volunteer Scheduling

### Workflow 1: Regular Class Assignment

**Request arrives via email:**
```
To: louie@ccb-scheduling.org
Subject: Need volunteer for Thursday intermediate class

We need someone for the Thursday 18:00-19:30 intermediate 
conversation class. Expecting about 8 students. Would prefer 
someone who's done this level before.
```

**De Palma processes:**
- Extracts: time slot (Thu 18:00-19:30), level (intermediate), type (conversation)
- Queries Google Sheets for available volunteers
- Calls volunteer_scheduler_skill with constraints
- Gets optimal assignment

**De Palma assigns:**
```
To: marie@email.com
Cc: coordinator@ccb.com
Subject: Teaching Assignment - Thursday Intermediate Conversation

Marie,

You're scheduled for Thursday 18:00-19:30, intermediate conversation class.
Expecting 8 students.

Why you? You're available Thursday evenings, have experience with 
intermediate learners, and specifically requested conversation classes.

Let me know if you need any materials prepared.

- Louie
```

**Updates Google Sheets:**
- Marks class C001 assigned to Marie
- Logs assignment rationale
- Updates volunteer's schedule

### Workflow 2: Substitution Request

**Request:**
```
To: louie@ccb-scheduling.org
Subject: Marie is sick - need substitute for Thursday

Marie just called in sick for her Thursday 18:00-19:30 
intermediate class. Can you find someone?
```

**De Palma processes:**
- Identifies: Class C001, normal volunteer Marie unavailable
- Searches for qualified substitutes (intermediate level, Thu evening available)
- Checks substitution history for reliable backups
- Prioritizes volunteers who've successfully subbed before

**De Palma responds:**
```
To: coordinator@ccb.com
Subject: Substitute Found - Thursday Class Covered

I've found a substitute for Thursday's intermediate class:

Jean will cover Marie's spot. He has:
- Taught intermediate before (subbed 3 times this year)
- Available Thursday evenings
- Successfully covered for Marie once before

I've sent Jean the confirmation and class details.

- Louie
```

### Workflow 3: Capacity Check

**Request:**
```
To: louie@ccb-scheduling.org
Subject: Can we add another beginner class on Wednesdays?

We have 10 new students wanting beginner conversation.
Can we add a Wednesday evening class?
```

**De Palma analyzes:**
- Checks Wednesday evening volunteer availability
- Reviews beginner-qualified volunteers
- Assesses current volunteer workload
- Calculates capacity

**Response:**
```
To: coordinator@ccb.com
Subject: Wednesday Beginner Class - We Have Capacity

Good news! We can add a Wednesday beginner class.

Available volunteers:
- Sophie: Wed 18:00-20:00, beginner certified, currently teaching 1 class/week
- Amelie: Wed 19:00-21:00, beginner/intermediate, currently 2 classes/week

Recommendation: Sophie at 19:00-20:30. She's underutilized and 
specifically wants more beginner classes.

Shall I set this up?

- Louie
```

## Volunteer Scheduler Skill (Python/OR-Tools)

### Input
```json
{
  "scheduling_request": {
    "class_id": "C001",
    "day": "Thursday",
    "time": "18:00-19:30",
    "class_type": "conversation",
    "level": "intermediate",
    "students_expected": 8,
    "required_qualifications": ["intermediate"],
    "preferred_qualifications": ["experience_intermediate"]
  },
  "volunteers": [
    {
      "name": "Marie",
      "teaching_levels": ["beginner", "intermediate"],
      "availability_days": ["Mon", "Wed", "Thu"],
      "availability_times": "18:00-20:00",
      "current_weekly_hours": 3,
      "background_check": true,
      "substitute_reliability": 0.95,
      "preferred_types": ["conversation"]
    },
    {
      "name": "Paul",
      "teaching_levels": ["intermediate", "advanced"],
      "availability_days": ["Tue", "Thu", "Sat"],
      "availability_times": "14:00-18:00",
      "current_weekly_hours": 4.5,
      "background_check": true,
      "substitute_reliability": 0.88,
      "preferred_types": ["reading_club", "conversation"]
    }
  ]
}
```

### Output
```json
{
  "assignment": {
    "volunteer": "Marie",
    "confidence": 0.94,
    "rationale": "Best match: intermediate certified, Thursday evening available, prefers conversation classes, low current workload (3hrs/week)"
  },
  "alternatives": [
    {
      "volunteer": "Paul",
      "confidence": 0.72,
      "rationale": "Qualified for intermediate but time slot (18:00) is outside preferred availability (14:00-18:00)"
    }
  ],
  "warnings": []
}
```

### OR-Tools Constraints

**Hard Constraints (must satisfy):**
- Volunteer has required teaching level certification
- Volunteer is available on specified day
- Volunteer's time availability overlaps with class time
- Background check completed (if required for class type)

**Soft Constraints (optimize):**
- Minimize deviation from volunteer's preferred time slots
- Balance workload across volunteers (avoid overloading)
- Prefer volunteers with experience at this level
- Consider volunteer's class type preferences
- Prioritize reliable volunteers (high substitute_reliability score)
- Account for recent substitution history (don't overuse same backups)

**Optimization Goals:**
1. Maximize volunteer satisfaction (preference matching)
2. Maximize class quality (experience matching)
3. Minimize volunteer burnout (workload balancing)
4. Maximize schedule stability (reliable volunteers)

## Human-Like Memory System

### Attention-Inspired Memory

De Palma remembers context like a human coordinator would:

**High Attention (Always Available)**
1. **Self-referential**: "I schedule volunteers for CCB English classes"
2. **Current Schedule**: This week's classes and assignments
3. **Recent Communications**: Last ~20 messages about scheduling

**Medium Attention (Retrievable)**
4. **Volunteer Preferences**: "Marie loves beginner classes, Paul prefers weekends"
5. **Substitution Patterns**: "Jean reliably covers for Marie"
6. **Problem History**: "Wednesday mornings are always hard to fill"

**Low Attention (Archived)**
7. **Historical Assignments**: Past semester schedules
8. **Old Substitutions**: Coverage from 6+ months ago

### Implementation in DynamoDB

```typescript
interface MemoryContext {
  // Always included
  self: {
    role: "CCB Volunteer Scheduling Coordinator",
    organization: "Centre Culturel Britannique de Lille",
    capabilities: ["class_assignment", "substitute_finding", "capacity_analysis"]
  },
  
  // Current week
  currentSchedule: ClassAssignment[],
  
  // Recent conversations
  recentMessages: Message[], // Last 20
  
  // Active volunteers
  activeVolunteers: Volunteer[],
  
  // Recent assignments and their success
  recentAssignments: AssignmentDecision[]
}
```

## Development Priorities

### Phase 1: Core Email Loop
1. ✅ Initialize SAM TypeScript project
2. ✅ Email receiver Lambda (SES integration)
3. ✅ Basic Claude integration
4. ✅ Email sender Lambda
5. ✅ DynamoDB schema and memory

### Phase 2: Volunteer Scheduling
6. ✅ Google Sheets tool MCP server (TypeScript) - for volunteer/class data
7. ✅ Volunteer scheduler skill MCP server (Python/OR-Tools)
8. ✅ Orchestration logic to coordinate tools/skills
9. ✅ Assignment workflow end-to-end

### Phase 3: Substitution & Capacity
10. ⬜ Substitution request handling
11. ⬜ Capacity analysis for new classes
12. ⬜ Conflict detection and resolution
13. ⬜ Volunteer preference learning

### Phase 4: Polish
14. ⬜ Louie personality implementation
15. ⬜ Comprehensive error handling
16. ⬜ Testing with real CCB scenarios
17. ⬜ Deployment and monitoring

## Configuration

### Environment Variables
```bash
CLAUDE_API_KEY=sk-...
GOOGLE_SHEETS_ID=1abc...  # CCB volunteer spreadsheet
EMAIL_DOMAIN=ccb-scheduling.org
AWS_REGION=eu-west-1  # Paris region (closer to Lille)
DYNAMODB_TABLE_MEMORY=depalma-memory
DYNAMODB_TABLE_STATE=depalma-state
CCB_COORDINATOR_EMAIL=coordinator@ccb.com
```

## Extensibility

After proving this works for CCB, extend to other volunteer organizations:

**Similar Organizations:**
- Other language schools/conversation exchanges
- Library volunteer programs  
- Community center class scheduling
- Tutoring programs

**Potential Future Features:**
- Recurring schedule optimization (semester planning)
- Volunteer recruitment suggestions ("We need more advanced-level teachers")
- Student progress tracking integration
- Automated class cancellation handling
- Multi-location support

## Testing Strategy

### Test Scenarios (Based on Real CCB Needs)

**Scenario 1: Regular Assignment**
- Input: Need volunteer for Thursday intermediate class
- Expected: Marie assigned (she's qualified and available)

**Scenario 2: Substitution**
- Input: Marie sick, need Thursday substitute
- Expected: Jean assigned (successfully subbed for Marie before)

**Scenario 3: Capacity Check**
- Input: Can we add Wednesday beginner class?
- Expected: Analysis of available volunteers with recommendation

**Scenario 4: No Coverage**
- Input: Need volunteer Saturday morning (no one available)
- Expected: Clear explanation of why coverage impossible + suggestions

**Scenario 5: Conflicting Requests**
- Input: Two classes same time, both need Marie
- Expected: Assign Marie to one, find substitute for other

## Open Questions

- Email address: `louie@ccb-scheduling.org` or integrate with existing CCB domain?
- How to handle volunteer declines? (Reply to assignment email?)
- Should De Palma track volunteer hours for reporting?
- Integration with CCB's existing scheduling spreadsheet or start fresh?
- How to handle emergency same-day cancellations? (SMS support?)
- Should volunteers be able to request specific classes? (Self-service via email?)

## Getting Started

When beginning development:

1. **Get sample CCB data**
   - Current volunteer roster
   - Typical class schedule
   - Real scheduling scenarios/pain points

2. **Set up Google Sheets**
   - Create sheets with CCB structure
   - Populate with anonymized test data
   - Get sharing credentials

3. **Build volunteer-specific logic**
   - Time slot parsing (day + time range)
   - Teaching level requirements
   - Availability matching

4. **Test with CCB scenarios**
   - Real requests from coordinators
   - Validate against their current Excel process
   - Iterate based on feedback

The goal: Make scheduling so easy that CCB coordinators wonder how they lived without Louie.