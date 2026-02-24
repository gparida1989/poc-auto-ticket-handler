# Auto Ticket Handler - High-Level Design (HLD)
## Plugin-Based Architecture with Python

## 1. Executive Summary

The Auto Ticket Handler is a **plugin-based decision engine** that:
- Receives tickets from ANY source via REST webhooks (ServiceNow today, Jira tomorrow)
- Allocates tickets to ANY handler system (ServiceNow, BMC ITSM, custom systems)
- Contains **ZERO** business logic about specific systems
- Acts purely as a **decision maker** using a multi-parameter allocation algorithm
- Enables easy swapping of source and handler systems without code changes

## 2. System Architecture Overview (Plugin-Based)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SOURCE PLUGIN (External)                      │
│  ServiceNow / Jira / GitHub Issues / Custom REST API           │
│  Implements: SourcePlugin Interface                            │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                REST Webhook POST
              /api/v1/webhooks/ticket
               (StandardTicket JSON)
                         │
        ┌────────────────▼────────────────┐
        │   AGENT (Pure Decision Maker)   │
        │  ┌─────────────────────────────┐│
        │  │ REST API + Webhook Server   ││
        │  │ (Flask / FastAPI)           ││
        │  └──────────────┬──────────────┘│
        │                 │               │
        │  ┌──────────────▼──────────────┐│
        │  │ Allocation Engine           ││
        │  │ - 7 Scoring Functions       ││
        │  │ - Decision Logic            ││
        │  │ - Config-driven Parameters  ││
        │  └──────────────┬──────────────┘│
        │                 │               │
        │  ┌──────────────▼──────────────┐│
        │  │ Storage Layer               ││
        │  │ - SQLite/PostgreSQL         ││
        │  │ - Metrics & Audit Log       ││
        │  └─────────────────────────────┘│
        └────────────────┬────────────────┘
                         │
                REST API POST
              /api/v1/handlers/allocate
             (AllocationDecision JSON)
                         │
┌─────────────────────────▼─────────────────────────────────────────┐
│                   HANDLER PLUGIN (External)                        │
│  ServiceNow / BMC ITSM / Custom System                           │
│  Implements: HandlerPlugin Interface                            │
│  - Returns AssignmentGroups                                      │
│  - Accepts AllocationDecision                                    │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Principle**: Agent and plugins communicate via JSON contracts, not code coupling.

## 3. Core Components

### 3.1 Source Plugin Interface
**Purpose**: Standardize how ANY ticket source connects to the agent

**What it does**:
- Receives tickets from external system (webhook)
- Validates ticket format against StandardTicket template
- Converts system-specific format to standard JSON contract
- Returns ticket to agent

**Implementations**:
- ServiceNowSource: Converts ServiceNow incidents
- JiraSource: Converts Jira issues
- CustomSource: Template for integrating any system
- GitHubSource, SlackSource, etc. (future)

**Key Contract**: `StandardTicket` JSON format
```json
{
  "ticket_id": "unique_id",
  "ticket_number": "INC0001",
  "title": "Issue title",
  "description": "Full description",
  "category": "network|application|database",
  "priority": "critical|high|medium|low",
  "source": "servicenow",
  "requester_location": {"lat": 40.7128, "lng": -74.0060, "timezone": "America/New_York"},
  "urgency": "1",
  "impact": "2",
  "external_metadata": {}  // Source-specific data
}
```

---

### 3.2 Agent Core (Decision Engine Only)
**Purpose**: Pure allocation decision logic with ZERO system knowledge

**What it does**:
1. Receives `StandardTicket` from any source plugin
2. Queries handler plugin for available `AssignmentGroups`
3. Runs allocation algorithm (7 parallel scoring functions)
4. Generates `AllocationDecision` JSON
5. Sends decision to handler plugin

**Zero coupling**:
- Doesn't import specific plugins (uses abstract interfaces)
- Doesn't know if source is ServiceNow or Jira
- Doesn't know if handler is ServiceNow or BMC ITSM
- Uses dependency injection for pluggability

**Python implementation**: `agent/core.py`
- REST API server (Flask/FastAPI)
- Webhook endpoint: `POST /api/v1/webhooks/ticket`
- Assignment endpoint: `POST /api/v1/handlers/allocate`
- Health check: `GET /health`

---

### 3.3 Allocation Engine (Scoring & Decision)
**Purpose**: Multi-parameter decision algorithm

**7 Scoring Parameters**:
1. **Availability** (25%) - Available capacity vs max bandwidth
2. **Bandwidth** (15%) - Can handle ticket complexity
3. **Velocity** (20%) - Resolution speed (fast = higher)
4. **Performance** (20%) - Historical quality & SLA compliance
5. **Proximity** (10%) - Geographic distance to requester
6. **Cultural Fit** (5%) - Expertise/cultural competency
7. **Timezone** (5%) - Timezone alignment with requester

**Algorithm**: Weighted sum of all scores [0-1]
- Scores each group in parallel
- Selects highest-scoring group
- Returns rationale and confidence score

**Key Contract**: `AllocationDecision` JSON
```json
{
  "ticket_id": "unique_id",
  "allocation": {"group_id": "xyz", "group_name": "Network Team"},
  "scores": {
    "availability": 0.85,
    "bandwidth": 0.90,
    "velocity": 0.88,
    "performance": 0.92,
    "proximity": 0.78,
    "cultural_fit": 0.95,
    "timezone": 0.88,
    "composite": 0.87
  },
  "rationale": "Best match for network expertise in Eastern timezone",
  "confidence": 0.87
}
```

---

### 3.4 Handler Plugin Interface
**Purpose**: Standardize how ANY handler system receives allocations

**What it does**:
1. Returns list of `AssignmentGroups` with metrics
2. Accepts `AllocationDecision` from agent
3. Updates ticket in external system
4. May trigger workflows or notifications

**Implementations**:
- ServiceNowHandler: Updates ServiceNow incidents
- BMCITSMHandler: Updates BMC ITSM tickets
- CustomHandler: Template for any system
- JiraHandler, SlackHandler, etc. (future)

**Key Contract**: `AssignmentGroup` JSON
```json
{
  "group_id": "unique_group_id",
  "name": "Network Support Team",
  "location": {"lat": 40.7128, "lng": -74.0060, "timezone": "America/New_York"},
  "capabilities": ["network", "connectivity", "vpn"],
  "status": "active",
  "max_bandwidth": 100,
  "current_load": 45,
  "metrics": {
    "avg_resolution_time_hours": 18.5,
    "sla_compliance_rate": 0.96,
    "quality_score": 0.89,
    "cultural_competencies": ["english_speakers", "24x7"]
  }
}
```

---

### 3.5 Storage Layer (Metrics & Audit)
**Purpose**: Record all allocation decisions and metrics

**Stores**:
- Allocation decisions (which ticket → group)
- Performance metrics (group resolution time, SLA, quality)
- Audit trail (who assigned what, when)
- System health events

**Tech**: SQLite (POC) or PostgreSQL (production)

---

## 4. Plugin Ecosystem

The beauty of this architecture: **Add new systems without touching agent code**.

```
Today:
┌─────────────────────────┐
│ ServiceNow Source       │
│ ↓                       │
│ Agent (decision-only)   │
│ ↓                       │
│ ServiceNow Handler      │
└─────────────────────────┘

Tomorrow (add Jira):
┌─────────────────────────┐
│ ServiceNow Source       │
│ + Jira Source           │◄── New plugin
│ ↓                       │
│ Agent (NO CHANGES!)     │
│ ↓                       │
│ ServiceNow Handler      │
│ + BMC ITSM Handler      │◄── New plugin
└─────────────────────────┘
```

**Plugin Development**: 20 lines of code to add a new source or handler
- Implement abstract `SourcePlugin` interface
- Implement abstract `HandlerPlugin` interface
- Register plugin in config
- Done!

---

## 5. REST API (Option 1: REST + Webhook)

### Webhook Flow (Source → Agent)

```
ServiceNow (or any source system)
    ↓
    Create ticket event
    ↓
    POST /api/v1/webhooks/ticket
    Headers: X-Source-ID: servicenow
    Body: {StandardTicket JSON}
    ↓
Agent
    ├─ Validate using source plugin
    ├─ Query handler for groups
    ├─ Run allocation algorithm
    └─ Send to handler plugin
    ↓
202 Accepted
Response: {status: "processing", ticket_id: "xyz"}
```

### Assignment Flow (Agent → Handler)

```
Agent:
    ├─ Run allocation on StandardTicket + AssignmentGroups
    ├─ Select best group
    └─ Create AllocationDecision
    ↓
    POST /handler/allocate
    Headers: X-Handler-ID: servicenow
    Body: {AllocationDecision JSON}
    ↓
Handler Plugin
    ├─ Update ticket in ServiceNow (or other system)
    └─ Trigger workflows/notifications
    ↓
200 OK
Response: {status: "assigned", ticket_id: "xyz", group_id: "abc"}
```

---

## 6. Technology Stack

- **Language**: Python 3.8+
- **Web Framework**: Flask or FastAPI
- **Database**: SQLite (POC) / PostgreSQL (production)
- **Deployment**: Docker, Kubernetes, AWS Lambda
- **Protocols**: REST API + JSON
- **Configuration**: YAML (algorithm weights)

---

## 7. Data Model (Generic)

### StandardTicket
All tickets conform to this standard:
- ticket_id, ticket_number
- title, description
- category, priority, urgency, impact
- requester_location (lat/lng/tz)
- source (which plugin sent it)
- external_metadata (source-specific data)

### AssignmentGroup
All groups conform to this standard:
- group_id, name
- location (lat/lng/tz)
- capabilities (list of expertise areas)
- status (active/inactive)
- max_bandwidth, current_load
- metrics (resolution time, SLA, quality score)

### AllocationDecision
All allocations use this standard:
- ticket_id
- allocation (group_id, group_name, assigned_user)
- scores (all 7 parameters + composite)
- rationale, confidence

---

## 8. Key Design Principles

1. **Agent is Plugin-Agnostic**
   - Zero hardcoded system knowledge
   - Uses interfaces, not implementations
   - Can add new systems without touching agent code

2. **Contract-Driven Architecture**
   - StandardTicket defines ticket format
   - AssignmentGroup defines group format
   - AllocationDecision defines decision format
   - Plugins implement contracts, not vice versa

3. **Single Responsibility**
   - Agent: Decision making only
   - Plugins: System integration only
   - Clear separation enables easy evolution

4. **Extensibility**
   - Add Jira source: 20 lines of code
   - Add BMC ITSM handler: 20 lines of code
   - Agent requires ZERO changes

5. **Testability**
   - Mock plugins for unit testing
   - Test agent logic independently
   - Test plugin logic independently

---

## 9. Integration Points

### To Source Systems
- Webhook: `POST /api/v1/webhooks/ticket`
- Source must send `StandardTicket` JSON
- Agent returns 202 Accepted

### To Handler Systems
- REST API: `POST /handler/allocate`
- Handler receives `AllocationDecision` JSON
- Handler returns updated status

### Optional Callbacks
- Handler can POST back to agent for status updates
- Agent can trigger workflows in source/handler systems
- Full bidirectional communication possible

---

## 10. Non-Functional Requirements

| Requirement | Target | Approach |
|---|---|---|
| Availability | 99.5% uptime | Auto-restart, health checks |
| Response Latency | < 500ms allocation | In-memory config, caching |
| Throughput | 100+ tickets/minute | Stateless, horizontal scaling |
| Data Consistency | Strong consistency | SQLite with transactions |
| Security | API authentication | Basic Auth + API keys |
| Compliance | Audit trail for all decisions | Immutable logs |

---

## 11. Roadmap

**Phase 1 (Current)**:
- Core agent with 7 scorers
- ServiceNow source + handler plugins
- REST API + webhook
- SQLite storage

**Phase 2**:
- 2nd source plugin (Jira)
- 2nd handler plugin (BMC ITSM)
- PostgreSQL for scale
- Real-time metrics dashboard

**Phase 3**:
- ML-based weight optimization
- Predictive capacity planning
- Self-learning algorithm

**Phase 4**:
- Multi-tenant support
- Custom scoring functions per tenant
- GraphQL API

---

*Version: 2.0 | Language: Python | Date: February 2026*
