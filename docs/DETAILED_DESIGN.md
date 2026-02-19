# Auto Ticket Handler - Detailed Design Document

## 1. Detailed Component Specifications

### 1.1 Ticket Ingestion Service

#### Responsibilities
- Validate incoming ticket payloads against schema
- Normalize ticket data into standard format
- Enrich tickets with derived metadata
- Perform geolocation lookup and geocoding
- Detect and handle duplicates
- Log all ingestion events for audit trail

#### API Endpoint
```
POST /api/v1/tickets/ingest
Content-Type: application/json

Request Body:
{
  "source": "web_portal|api|email|chat",
  "priority": "critical|high|medium|low",
  "category": "technical|billing|account|other",
  "content": "Detailed ticket description",
  "requester_email": "user@example.com",
  "requester_location": "City, Country or lat/lng",
  "additional_metadata": {
    "department": "string",
    "account_id": "string",
    "phone": "string"
  }
}

Response:
{
  "status": "success|error",
  "ticket_id": "TKT-20260219-001234",
  "enriched_data": {
    "location": { "lat": 40.7128, "lng": -74.0060, "city": "New York" },
    "timezone": "America/New_York",
    "estimated_complexity": 0.75,
    "category_confidence": 0.92
  },
  "message": "Ticket ingested successfully"
}
```

#### Data Enrichment Logic
```
ENRICH_TICKET(ticket):
  1. Extract location from ticket
  2. Call GeolocationService(location) → geo_coordinates
  3. Call TimezoneDB(geo_coordinates) → timezone
  4. Analyze content → estimate_complexity [0-1]
  5. Apply categorization model → category
  6. Check duplicate detection → is_duplicate boolean
  7. Extract keywords → tags
  8. Return enriched ticket
```

#### Validation Rules
- Ticket content minimum 10 characters, maximum 10,000
- Priority must be one of: critical, high, medium, low
- Category must be from predefined list
- Location must be valid (either address or coordinates)
- Source must be registered and active

---

### 1.2 Allocation Agent Engine (Core Algorithm)

#### Main Algorithm Flow

```
ALLOCATE_TICKET(ticket):
  1. Retrieve all active assignment groups
  2. Filter groups by capability match (category)
  3. Filter groups with available capacity (bandwidth > 0)
  
  FOR EACH qualified_group:
    4a. Calculate availability_score(group, ticket)
    4b. Calculate bandwidth_score(group)
    4c. Calculate velocity_score(group)
    4d. Calculate performance_score(group)
    4e. Calculate proximity_score(group, ticket.location)
    4f. Calculate cultural_compatibility_score(group, ticket)
    4g. Calculate timezone_score(group, ticket.timezone)
    
    4h. composite_score = weighted_sum(all_scores)
    4i. Store (group, composite_score, breakdown)
  
  5. Select group with MAX(composite_score)
  6. Apply business rules constraints
  7. Create AllocationDecision record
  8. Publish ticket to selected group
  9. Return allocation result
```

#### Detailed Scoring Functions

##### 4a. Availability Score
```
AVAILABILITY_SCORE(group, ticket):
  available_capacity = group.max_bandwidth - group.current_load
  capacity_ratio = available_capacity / group.max_bandwidth
  
  IF capacity_ratio > 0.5:
    return 1.0 (Excellent capacity)
  ELSE IF capacity_ratio > 0.25:
    return 0.6 (Moderate capacity)
  ELSE IF capacity_ratio > 0:
    return 0.3 (Low capacity)
  ELSE:
    return 0 (No capacity)
```

##### 4b. Bandwidth Score
```
BANDWIDTH_SCORE(group):
  max_bw = group.max_bandwidth
  ticket_complexity = ticket.estimated_complexity
  required_capacity = ticket_complexity * 2 (empirical factor)
  
  IF max_bw >= required_capacity * 2:
    return 1.0
  ELSE IF max_bw >= required_capacity:
    return 0.7
  ELSE:
    return 0.4
```

##### 4c. Velocity Score
```
VELOCITY_SCORE(group):
  avg_resolution_time = group.performance_metrics.avg_resolution_time
  velocity = 1 / (avg_resolution_time + 1) [tickets per hour]
  
  normalized_velocity = MIN(velocity / reference_velocity, 1.0)
  
  return normalized_velocity
```

##### 4d. Performance Score
```
PERFORMANCE_SCORE(group):
  sla_compliance = group.performance_metrics.sla_compliance_rate
  quality_score = group.performance_metrics.quality_score
  
  combined = (sla_compliance * 0.6) + (quality_score * 0.4)
  
  return combined
```

##### 4e. Proximity Score
```
PROXIMITY_SCORE(group, ticket_location):
  distance_km = HAVERSINE_DISTANCE(group.location, ticket_location)
  
  IF distance_km < 50:
    return 1.0 (Same city/region)
  ELSE IF distance_km < 500:
    return 0.7 (Same country/region)
  ELSE IF distance_km < 2000:
    return 0.4 (Different region, same continent)
  ELSE:
    return 0.2 (Different continent)
```

##### 4f. Cultural Compatibility Score
```
CULTURAL_SCORE(group, ticket):
  group_competencies = group.performance_metrics.cultural_competencies
  ticket_context = ticket.cultural_context
  
  IF ticket_context IN group_competencies:
    return 1.0
  ELSE IF NO specific_context_required:
    return 0.8 (Generic support capable)
  ELSE:
    return 0.3 (Competency gap)
```

##### 4g. Timezone Score
```
TIMEZONE_SCORE(group, ticket_timezone):
  group_tz_offset = GET_TIMEZONE_OFFSET(group.timezone)
  ticket_tz_offset = GET_TIMEZONE_OFFSET(ticket_timezone)
  hour_difference = ABS(group_tz_offset - ticket_tz_offset)
  
  IF hour_difference <= 2:
    return 1.0 (Ideal timezone overlap)
  ELSE IF hour_difference <= 6:
    return 0.7 (Good overlap, some edge hours)
  ELSE IF hour_difference <= 12:
    return 0.4 (Limited overlap)
  ELSE:
    return 0.1 (Minimal overlap)
```

##### Composite Score Calculation
```
COMPOSITE_SCORE(group, ticket):
  scores = {
    availability: AVAILABILITY_SCORE(group, ticket),
    bandwidth: BANDWIDTH_SCORE(group),
    velocity: VELOCITY_SCORE(group),
    performance: PERFORMANCE_SCORE(group),
    proximity: PROXIMITY_SCORE(group, ticket.location),
    cultural: CULTURAL_SCORE(group, ticket),
    timezone: TIMEZONE_SCORE(group, ticket.timezone)
  }
  
  weights = {
    availability: 0.20,
    bandwidth: 0.15,
    velocity: 0.15,
    performance: 0.20,
    proximity: 0.10,
    cultural: 0.12,
    timezone: 0.08
  }
  
  composite = Σ(scores[i] * weights[i])
  return composite [0-1]
```

---

## 2. Data Flow Diagrams

### 2.1 End-to-End Allocation Flow

```
┌──────────────┐
│ Ticket       │
│ Source       │
│ (API/Queue)  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│  Ingestion Service       │
│  ├─ Validate Schema      │
│  ├─ Normalize Data       │
│  ├─ Enrich Metadata      │
│  ├─ Geocoding            │
│  └─ Store in DB          │
└──────┬───────────────────┘
       │ (Standard Ticket)
       ▼
┌──────────────────────────┐
│  Allocation Agent        │
│  ├─ Load Groups          │
│  ├─ Filter by Category   │
│  ├─ Score All Groups     │
│  ├─ Rank by Score        │
│  └─ Apply Business Rules │
└──────┬───────────────────┘
       │ (Allocation Decision)
       ▼
┌──────────────────────────┐
│  Notification Service    │
│  ├─ Publish to Queue     │
│  ├─ Broadcast Event      │
│  └─ Log Decision         │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  Assignment Group        │
│  (Handler System)        │
│  ├─ Receive Ticket       │
│  ├─ Process/Resolve      │
│  └─ Report Metrics       │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  Feedback Loop           │
│  ├─ Update Metrics       │
│  ├─ Track Performance    │
│  └─ Inform Next Cycle    │
└──────────────────────────┘
```

---

## 3. Sequence Diagrams

### 3.1 Ticket Allocation Sequence

```
Client          Ingestion       Agent Engine       Handler        Database
  │                 │               │                 │              │
  │─ POST Ticket───▶│               │                 │              │
  │                 │─ Validate ───▶│ Store Ticket   │              │
  │                 │◀──────────────│                 │              │
  │                 │               │                 │◀─────────────│
  │                 │─ Enrich Data ─│ Get Groups      │              │
  │                 │               │                 │              │
  │                 │─ Call Agent ──▶│                 │              │
  │                 │               │─ Score Groups ─▶│              │
  │                 │               │◀────────────────│              │
  │                 │               │                 │              │
  │                 │               │─ Select Best ───│              │
  │                 │               │                 │              │
  │                 │               │─ Store Decision─────────────────▶│
  │                 │               │                 │              │
  │                 │               │─ Publish Event ─────────────────▶│
  │                 │     ◀─────────│                 │              │
  │◀─ 200 + TicketID│                 │                 │              │
  │                 │                 │                 │              │
  │                 │                 │               │─ Receive ────│
  │                 │                 │               │              │
  │                 │                 │               │─ Process ───▶│
  │                 │                 │               │              │
  │                 │                 │               │─ Report ────▶│
```

### 3.2 Scoring Calculation Sequence

```
Agent Engine        Parameter        Scoring
                    Calculator       Function
    │                   │               │
    │─ Call Scorer ────▶│               │
    │                   │               │
    │                   │─ Availability─▶ [0-1]
    │                   │◀───────────────│
    │                   │               │
    │                   │─ Bandwidth ───▶ [0-1]
    │                   │◀───────────────│
    │                   │               │
    │                   │─ Velocity────▶ [0-1]
    │                   │◀───────────────│
    │                   │               │
    │                   │─ Performance ─▶ [0-1]
    │                   │◀───────────────│
    │                   │               │
    │                   │─ Proximity ───▶ [0-1]
    │                   │◀───────────────│
    │                   │               │
    │                   │─ Cultural ────▶ [0-1]
    │                   │◀───────────────│
    │                   │               │
    │                   │─ Timezone ────▶ [0-1]
    │                   │◀───────────────│
    │                   │               │
    │◀─ Composite Score─│               │
    │  + Breakdown      │               │
```

---

## 4. Database Schema

### 4.1 Core Tables

#### `tickets` Table
```sql
CREATE TABLE tickets (
  id VARCHAR(50) PRIMARY KEY,
  source VARCHAR(50) NOT NULL,
  category VARCHAR(100) NOT NULL,
  priority VARCHAR(20) NOT NULL,
  content TEXT NOT NULL,
  requester_email VARCHAR(255),
  requester_location_lat DECIMAL(10,8),
  requester_location_lng DECIMAL(11,8),
  requester_timezone VARCHAR(50),
  cultural_context VARCHAR(100),
  estimated_complexity FLOAT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_status (status),
  INDEX idx_created_at (created_at),
  INDEX idx_category (category)
);
```

#### `assignment_groups` Table
```sql
CREATE TABLE assignment_groups (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  location_lat DECIMAL(10,8),
  location_lng DECIMAL(11,8),
  timezone VARCHAR(50) NOT NULL,
  capabilities JSON, -- ["technical", "billing", "account"]
  max_bandwidth INT NOT NULL,
  current_load INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### `allocation_decisions` Table
```sql
CREATE TABLE allocation_decisions (
  id VARCHAR(50) PRIMARY KEY,
  ticket_id VARCHAR(50) NOT NULL,
  assigned_group_id VARCHAR(50) NOT NULL,
  decision_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  availability_score FLOAT,
  bandwidth_score FLOAT,
  velocity_score FLOAT,
  performance_score FLOAT,
  proximity_score FLOAT,
  cultural_score FLOAT,
  timezone_score FLOAT,
  final_score FLOAT,
  rationale TEXT,
  FOREIGN KEY (ticket_id) REFERENCES tickets(id),
  FOREIGN KEY (assigned_group_id) REFERENCES assignment_groups(id),
  INDEX idx_ticket_id (ticket_id),
  INDEX idx_group_id (assigned_group_id),
  INDEX idx_decision_timestamp (decision_timestamp)
);
```

#### `group_performance_metrics` Table
```sql
CREATE TABLE group_performance_metrics (
  id VARCHAR(50) PRIMARY KEY,
  group_id VARCHAR(50) NOT NULL UNIQUE,
  avg_resolution_time_hours FLOAT DEFAULT 24,
  sla_compliance_rate FLOAT DEFAULT 0.95,
  quality_score FLOAT DEFAULT 0.80,
  total_tickets_handled INT DEFAULT 0,
  cultural_competencies JSON, -- ["english_speakers", "spanish_fluent", "remote_support"]
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (group_id) REFERENCES assignment_groups(id),
  INDEX idx_group_id (group_id)
);
```

#### `allocation_audit_log` Table
```sql
CREATE TABLE allocation_audit_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ticket_id VARCHAR(50) NOT NULL,
  event_type VARCHAR(50), -- 'ingestion_start', 'enrichment_complete', 'scoring_start', 'allocation_complete'
  event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  details JSON,
  FOREIGN KEY (ticket_id) REFERENCES tickets(id),
  INDEX idx_ticket_id (ticket_id),
  INDEX idx_event_timestamp (event_timestamp)
);
```

---

## 5. API Specifications

### 5.1 Ticket Ingestion API

```yaml
POST /api/v1/tickets/ingest
Description: Ingest and enrich a new ticket

Request:
  Content-Type: application/json
  Headers:
    Authorization: Bearer {token}
    X-Source-ID: {source_identifier}
  
  Body:
    source: string (required)
    priority: string (required) - critical|high|medium|low
    category: string (required)
    content: string (required, 10-10000 chars)
    requester_email: string (required)
    requester_location: string (required, address or "lat,lng")
    additional_metadata: object (optional)

Response (200 OK):
  {
    "status": "success",
    "ticket_id": "TKT-20260219-001234",
    "enriched_data": {
      "location": {"lat": 40.7128, "lng": -74.0060, "city": "New York"},
      "timezone": "America/New_York",
      "estimated_complexity": 0.72
    }
  }

Response (400 Bad Request):
  {
    "status": "error",
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "errors": [
      {"field": "content", "message": "Minimum length is 10 characters"}
    ]
  }
```

### 5.2 Allocation Status API

```yaml
GET /api/v1/tickets/{ticket_id}/allocation
Description: Get allocation decision for a ticket

Response (200 OK):
  {
    "ticket_id": "TKT-20260219-001234",
    "assigned_group_id": "GRP-002",
    "assigned_group_name": "North America Technical Support",
    "decision_timestamp": "2026-02-19T10:30:45Z",
    "scores": {
      "availability": 0.85,
      "bandwidth": 0.90,
      "velocity": 0.88,
      "performance": 0.92,
      "proximity": 0.78,
      "cultural": 0.95,
      "timezone": 0.88,
      "final": 0.87
    }
  }
```

### 5.3 Performance Metrics API

```yaml
GET /api/v1/groups/{group_id}/metrics
Description: Get current performance metrics for assignment group

Response (200 OK):
  {
    "group_id": "GRP-002",
    "avg_resolution_time_hours": 18.5,
    "sla_compliance_rate": 0.96,
    "quality_score": 0.89,
    "current_load": 45,
    "max_bandwidth": 100,
    "available_capacity": 55,
    "capacity_percentage": 55.0,
    "cultural_competencies": ["english", "spanish", "technical_support"]
  }
```

---

## 6. Error Handling & Edge Cases

### 6.1 Error Scenarios

| Scenario | Handling |
|---|---|
| Invalid ticket format | Return 400 with validation errors |
| Geolocation lookup fails | Use default timezone, continue processing |
| No available groups | Escalate to admin, queue ticket |
| Database connection failure | Retry with exponential backoff |
| Scoring timeout | Use previously cached scores, log alert |
| Duplicate ticket detected | Link to existing ticket, notify requester |

### 6.2 Fallback Strategies

```
PRIMARY: Allocate to highest-scoring group
├─ IF no groups available
│  ├─ Check waiting queue
│  ├─ IF queue full, escalate to admin
│  └─ Ticket marked "PENDING_ASSIGNMENT"
│
└─ IF all groups in different timezones
   ├─ Prioritize group with best SLA compliance
   └─ Add notification to requester about response time
```

---

## 7. Configuration & Tuning

### 7.1 Configurable Parameters

```json
{
  "scoring_weights": {
    "availability": 0.20,
    "bandwidth": 0.15,
    "velocity": 0.15,
    "performance": 0.20,
    "proximity": 0.10,
    "cultural": 0.12,
    "timezone": 0.08
  },
  "thresholds": {
    "minimum_allocation_score": 0.50,
    "availability_critical": 0.25,
    "timezone_overlap_hours": 2
  },
  "distance_tiers": {
    "same_city": 50,
    "same_region": 500,
    "same_continent": 2000
  },
  "feature_flags": {
    "enable_cultural_scoring": true,
    "enable_proximity_scoring": true,
    "enable_timezone_optimization": true
  }
}
```

---

## 8. Performance & Scalability

### 8.1 Performance Targets

| Metric | Target | Approach |
|---|---|---|
| Allocation latency | < 500ms | In-memory caching of group metrics |
| Throughput | 1000 tickets/min | Stateless services, horizontal scaling |
| Geolocation lookup | < 100ms | Cached coordinate data |
| Database queries | < 50ms | Indexed queries, connection pooling |

### 8.2 Caching Strategy

```
Cache Layer (Redis):
├─ assignment_groups (TTL: 5 min)
├─ group_performance_metrics (TTL: 2 min)
├─ geolocation_cache (TTL: 24 hours)
└─ timezone_offsets (TTL: 7 days)
```

---

## 9. Monitoring & Observability

### 9.1 Key Metrics to Track

```
- Allocation accuracy (% correct assignments post-review)
- Allocation latency (p50, p95, p99)
- Group utilization (workload vs capacity)
- False allocation rate (reassignments)
- SLA compliance per group
- Scoring parameter distribution
```

### 9.2 Logging

```
ALL allocation decisions must log:
├─ ticket_id, group_id, final_score
├─ Individual parameter scores with breakdown
├─ Business rules applied or overridden
└─ Timestamp and decision duration
```

---

## 10. Testing Strategy

### 10.1 Unit Tests
- Individual scoring functions
- Data enrichment logic
- Validation rules

### 10.2 Integration Tests
- End-to-end allocation workflow
- Database persistence
- API contract validation

### 10.3 Load Tests
- 1000+ tickets/minute throughput
- Latency under sustained load
- Cache hit rate validation

### 10.4 Scenario Tests
- All groups at capacity
- Geolocation failures
- Timezone-only allocation
- Cultural competency prioritization

---

*Version: 2.0 | Date: February 2026 | Status: Design Review Complete*
