# Plugin-Based Auto Ticket Handler Architecture
## Python Implementation with REST API + Webhook

## 1. Executive Summary

The Auto Ticket Handler is a **plugin-based decision engine** that:
- Receives tickets from any source (ServiceNow today, any system tomorrow)
- Allocates tickets to any handler system
- Contains **zero** business logic about source or handler systems
- Acts purely as a **decision maker** based on allocation algorithms

**Key Design Principle**: The agent knows nothing about specific systems. Only interfaces matter.

---

## 2. Plugin Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TICKET SOURCE (Plugin)                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ServiceNow / Jira / GitHub Issues / Any REST API           │  │
│  │  (Implements SourcePlugin Interface)                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                    ┌────────▼───────────┐
                    │  REST Webhook      │
                    │  POST /ticket      │
                    │  {StandardTicket}  │
                    └────────┬───────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼──┐          ┌──────▼───────┐      ┌─────▼────┐
    │Store │          │  Decision    │      │  Database│
    │Metrics          │  Engine      │      │ (Store)  │
    │      │          │  (Agent)     │      │          │
    └──────┘          └──────┬───────┘      └──────────┘
                             │
                    ┌────────▼──────────┐
                    │  REST Call        │
                    │  POST /assign     │
                    │  {Allocation}     │
                    └────────┬──────────┘
                             │
┌────────────────────────────┴─────────────────────────────────────────┐
│                    HANDLER SYSTEM (Plugin)                           │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  ServiceNow / Jira / Custom ITSM / Any REST API              │ │
│  │  (Implements HandlerPlugin Interface)                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Architectural Concepts

### 3.1 Plugin System

Everything external is a **plugin** following strict interfaces:

**SourcePlugin Interface**:
- Sends tickets via webhook to agent
- Ticket must conform to `StandardTicket` template
- Receives allocation decision via callback

**HandlerPlugin Interface**:
- Responds to allocation requests
- Provides assignment groups with metrics
- Updates ticket with assignment

**Agent Core**:
- Receives `StandardTicket`
- Queries handler for groups
- Runs allocation algorithm
- Returns allocation decision

### 3.2 Contract-Based Communication

All communication uses JSON contracts:

```python
# StandardTicket (Source → Agent)
{
    "ticket_id": "unique_id",
    "ticket_number": "INC0001",
    "title": "Issue title",
    "description": "Full description",
    "category": "network|application|database|other",
    "priority": "critical|high|medium|low",
    "source": "servicenow",  # identifies which source sent this
    "requester_location": {
        "lat": 40.7128,
        "lng": -74.0060,
        "timezone": "America/New_York"
    },
    "urgency": "1",  # 1-5 scale
    "impact": "2",   # 1-5 scale
    "external_metadata": {
        # Source-specific data (ignored by agent)
        "assignment_group_id": "group123",
        "caller_id": "user456"
    }
}

# AllocationDecision (Agent → Handler)
{
    "ticket_id": "unique_id",
    "decision_timestamp": "2026-02-24T14:30:45.123Z",
    "allocation": {
        "group_id": "group_sys_id",
        "group_name": "Network Support Team",
        "assigned_to_user_id": "user_id"  # optional
    },
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

# AssignmentGroup (Handler → Agent)
{
    "group_id": "unique_group_id",
    "name": "Network Support Team",
    "location": {
        "lat": 40.7128,
        "lng": -74.0060,
        "timezone": "America/New_York"
    },
    "capabilities": ["network", "connectivity", "vpn"],
    "status": "active",
    "max_bandwidth": 100,
    "current_load": 45,
    "metrics": {
        "avg_resolution_time_hours": 18.5,
        "sla_compliance_rate": 0.96,
        "quality_score": 0.89,
        "cultural_competencies": ["english_speakers", "24x7_support"]
    }
}
```

---

## 3.3 Complete User Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              USER TICKET CREATION FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘

STEP 1: USER CREATES TICKET
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│  User (End User / Support Portal)                                               │
│  ↓                                                                               │
│  📝 Creates Ticket via ServiceNow Portal / Self-Service Portal                 │
│    - Title: "Network connectivity issue"                                       │
│    - Description: "Can't connect to VPN"                                       │
│    - Category: Network                                                          │
│    - Location: New York                                                         │
│    - Priority: High                                                             │
│  ↓                                                                               │
│  ✅ Ticket Created in ServiceNow                                               │
│    - Incident ID: INC0012345                                                   │
│    - State: "New"                                                               │
│    - Assigned to: (empty, waiting for allocation)                              │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

STEP 2: SERVICENOW TRIGGERS WEBHOOK
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│  ServiceNow System (Incident Table)                                             │
│  ↓                                                                               │
│  🔔 Business Rule / Workflow Trigger Fires                                     │
│    (On insert of Incident record)                                              │
│  ↓                                                                               │
│  📤 ServiceNow Sends Webhook POST Request:                                     │
│     URL: https://agent.company.com/api/v1/webhooks/ticket                     │
│     Headers:                                                                    │
│       X-Source-ID: servicenow                                                 │
│       Content-Type: application/json                                           │
│       Authorization: Bearer {token}                                            │
│     Body: {                                                                     │
│       "record": {                                                              │
│         "sys_id": "abc123xyz",                                                │
│         "number": "INC0012345",                                               │
│         "short_description": "Network connectivity issue",                     │
│         "description": "Can't connect to VPN",                                │
│         "category": "network",                                                │
│         "priority": "2",  # High                                              │
│         "urgency": "2",                                                       │
│         "impact": "2",                                                        │
│         "caller_id": "user_789",                                             │
│         "location": "New York"                                               │
│       }                                                                        │
│     }                                                                          │
│  ↓                                                                               │
│  ⏳ Waiting for response from Agent                                            │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

STEP 3: SOURCE PLUGIN RECEIVES & VALIDATES
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│  Agent Server (Source Plugin Handler)                                           │
│  ↓                                                                               │
│  📥 POST /api/v1/webhooks/ticket received                                      │
│  ↓                                                                               │
│  🔌 ServiceNow Source Plugin Invoked:                                          │
│     - Validates webhook payload                                                │
│     - Maps ServiceNow fields → StandardTicket contract                         │
│     - Extracts geolocation data (latitude, longitude, timezone)                │
│  ↓                                                                               │
│  ✅ StandardTicket Created:                                                    │
│  {                                                                              │
│    "ticket_id": "abc123xyz",                                                  │
│    "ticket_number": "INC0012345",                                             │
│    "title": "Network connectivity issue",                                      │
│    "category": "network",                                                      │
│    "priority": "high",                                                         │
│    "source": "servicenow",                                                    │
│    "requester_location": {                                                    │
│      "lat": 40.7128,                                                         │
│      "lng": -74.0060,                                                        │
│      "timezone": "America/New_York"                                          │
│    },                                                                          │
│    "urgency": "2",                                                            │
│    "impact": "2",                                                             │
│    "external_metadata": {                                                     │
│      "assignment_group": null,                                               │
│      "caller_id": "user_789"                                                │
│    }                                                                          │
│  }                                                                              │
│  ↓                                                                               │
│  💾 Store ticket in database for tracking                                     │
│  ↓                                                                               │
│  ✅ Response 202 Accepted sent to ServiceNow                                   │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

STEP 4: AGENT QUERIES HANDLER FOR ASSIGNMENT GROUPS
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│  Allocation Agent (Decision Engine)                                             │
│  ↓                                                                               │
│  🤔 Processing StandardTicket                                                  │
│  ↓                                                                               │
│  🔌 Call Handler Plugin (ServiceNow):                                          │
│     - Query: "Get all active assignment groups for category=network"            │
│  ↓                                                                               │
│  📋 Handler Plugin Returns Assignment Groups:                                  │
│  [                                                                              │
│    {                                                                            │
│      "group_id": "group_001",                                                 │
│      "name": "Network Support Team - NYC",                                   │
│      "location": {"lat": 40.7128, "lng": -74.0060, "tz": "America/New_York"},                     │
│      "capabilities": ["network", "vpn", "connectivity"],                     │
│      "max_bandwidth": 100,                                                   │
│      "current_load": 45,                                                     │
│      "metrics": {                                                             │
│        "avg_resolution_time_hours": 18.5,                                   │
│        "sla_compliance_rate": 0.96,                                         │
│        "quality_score": 0.89                                                │
│      }                                                                        │
│    },                                                                          │
│    {                                                                            │
│      "group_id": "group_002",                                                 │
│      "name": "Network Support Team - Chicago",                              │
│      "location": {"lat": 41.8781, "lng": -87.6298, "tz": "America/Chicago"},      │
│      "max_bandwidth": 100,                                                   │
│      "current_load": 78,                                                     │
│      "metrics": {...}                                                         │
│    }                                                                            │
│  ]                                                                              │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

STEP 5: AGENT RUNS ALLOCATION ALGORITHM
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│  Allocation Engine (Scoring System)                                             │
│  ↓                                                                               │
│  ️⚙️  Runs 7 Parallel Scorers for Each Group:                                   │
│                                                                                  │
│  GROUP 1: Network Support Team - NYC                                            │
│  ├─ Availability Score:        0.85  (55/100 slots available)                 │
│  ├─ Bandwidth Score:           0.90  (can handle high-priority)               │
│  ├─ Velocity Score:            0.88  (fast resolvers)                         │
│  ├─ Performance Score:         0.92  (96% SLA compliance)                     │
│  ├─ Proximity Score:           0.98  (same city as requester)                 │
│  ├─ Cultural Fit Score:        0.90  (English speakers, diverse team)         │
│  ├─ Timezone Score:            1.00  (same timezone as requester)             │
│  └─ COMPOSITE SCORE:           ═══════════════════════════════════            │
│     (0.25×0.85 + 0.15×0.90 + 0.20×0.88 + 0.20×0.92 + 0.10×0.98 + 0.05×0.90 + 0.05×1.00)  = 0.90
│                                                                                  │
│  GROUP 2: Network Support Team - Chicago                                        │
│  ├─ Availability Score:        0.65  (22/100 slots available - busy!)          │
│  ├─ Bandwidth Score:           0.75  (stretched)                               │
│  ├─ Velocity Score:            0.82  (slower resolvers)                        │
│  ├─ Performance Score:         0.88  (88% SLA compliance)                      │
│  ├─ Proximity Score:           0.45  (different city, 800 miles away)          │
│  ├─ Cultural Fit Score:        0.85  (English speakers)                        │
│  ├─ Timezone Score:            0.80  (1 hour behind requester)                 │
│  └─ COMPOSITE SCORE:           ═══════════════════════════════════            │
│     (0.25×0.65 + 0.15×0.75 + 0.20×0.82 + 0.20×0.88 + 0.10×0.45 + 0.05×0.85 + 0.05×0.80)  = 0.74
│                                                                                  │
│  🏆 WINNER: Group 1 (NYC) with Score 0.90                                      │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

STEP 6: AGENT SENDS ALLOCATION DECISION TO HANDLER
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│  Allocation Agent → Handler Plugin Communication                                │
│  ↓                                                                               │
│  📤 POST /handler/allocate                                                     │
│     Headers:                                                                    │
│       X-Handler-ID: servicenow                                               │
│       Content-Type: application/json                                           │
│     Body: {                                                                     │
│       "ticket_id": "abc123xyz",                                              │
│       "decision_timestamp": "2026-02-24T14:30:45.123Z",                      │
│       "allocation": {                                                         │
│         "group_id": "group_001",                                            │
│         "group_name": "Network Support Team - NYC"                          │
│       },                                                                      │
│       "scores": {                                                             │
│         "availability": 0.85,                                               │
│         "bandwidth": 0.90,                                                  │
│         "velocity": 0.88,                                                   │
│         "performance": 0.92,                                                │
│         "proximity": 0.98,                                                  │
│         "cultural_fit": 0.90,                                               │
│         "timezone": 1.00,                                                   │
│         "composite": 0.90                                                   │
│       },                                                                      │
│       "rationale": "NYC team has best proximity, availability, and SLA performance for network issues", │
│       "confidence": 0.90                                                     │
│     }                                                                         │
│  ↓                                                                               │
│  💾 Store AllocationDecision in database                                       │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

STEP 7: HANDLER PLUGIN ASSIGNS TICKET
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│  ServiceNow Handler Plugin                                                      │
│  ↓                                                                               │
│  🔌 Receives AllocationDecision:                                               │
│  ↓                                                                               │
│  📝 Updates ServiceNow Incident Record:                                        │
│     - Set Assignment Group = "Network Support Team - NYC"                     │
│     - Set State = "Assigned"                                                   │
│     - Add Comment: "Auto-allocated by Agent with 90% confidence"              │
│     - Add Tags: allocation_engine, auto_routed                               │
│     - Store Decision Scores for reporting                                     │
│  ↓                                                                               │
│  🔔 ServiceNow Workflow Triggers:                                             │
│     - Send notification to team                                               │
│     - Send update notification to requester                                   │
│  ↓                                                                               │
│  ✅ Response 200 OK sent back to Agent:                                       │
│  {                                                                              │
│    "status": "assigned",                                                      │
│    "ticket_id": "abc123xyz",                                                 │
│    "group_id": "group_001",                                                 │
│    "assigned_to_group": "Network Support Team - NYC",                        │
│    "timestamp": "2026-02-24T14:30:47.456Z"                                  │
│  }                                                                              │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

STEP 8: USER RECEIVES NOTIFICATION
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│  Requester / End User                                                           │
│  ↓                                                                               │
│  📧 Email Notification:                                                        │
│     "Your ticket INC0012345 has been assigned to Network Support Team - NYC"  │
│     "Assignment Details: High priority network issue"                         │
│     "Estimated Resolution: ~18 hours based on team metrics"                   │
│  ↓                                                                               │
│  🔔 Portal Update:                                                             │
│     - Incident status changed to "Assigned"                                    │
│     - Assignment Group field populated                                         │
│     - Team confirmed receipt                                                   │
│  ↓                                                                               │
│  ✅ Ticket Now in Handler Queue:                                              │
│     - Network Support Team - NYC can see it in their queue                    │
│     - SLA timer started (based on priority)                                    │
│     - Team member begins work                                                  │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

COMPLETE FLOW TIMELINE:
├─ T+0ms:    User creates ticket in ServiceNow
├─ T+100ms:  ServiceNow webhook triggered
├─ T+150ms:  Agent receives webhook
├─ T+200ms:  Source plugin validates → StandardTicket created
├─ T+250ms:  Handler plugin queries for groups
├─ T+300ms:  Allocation engine runs 7 scorers in parallel
├─ T+350ms:  Best group selected, AllocationDecision created
├─ T+400ms:  Handler plugin receives allocation decision
├─ T+450ms:  ServiceNow Incident updated (assigned group, state changed)
├─ T+500ms:  Notifications sent to team and requester
└─ T+600ms:  Ticket appears in support team's queue
   
   TOTAL END-TO-END TIME: ~500ms

```

---

## 4. Plugin Implementation Guide

### 4.1 Source Plugin Template (Python)

```python
# plugins/sources/source_plugin_template.py

from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class StandardTicket:
    """Template for all tickets entering the agent"""
    ticket_id: str
    ticket_number: str
    title: str
    description: str
    category: str
    priority: str
    source: str  # identifier for this plugin
    requester_location: Dict[str, Any]
    urgency: str
    impact: str
    external_metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__

class SourcePlugin(ABC):
    """Base class for all ticket sources"""
    
    @abstractmethod
    def validate_ticket(self, ticket: Dict[str, Any]) -> StandardTicket:
        """
        Convert source-specific ticket format to StandardTicket
        Raises ValueError if tickets don't match expected schema
        """
        pass
    
    @abstractmethod
    def get_ticket_metadata(self, ticket_id: str) -> Dict[str, Any]:
        """Retrieve full ticket details from source system"""
        pass
    
    @abstractmethod
    def get_group_id_for_assignment(self, ticket_id: str) -> str:
        """Get source system's field name for assignment group ID"""
        pass

# Example: ServiceNow Source Plugin
class ServiceNowSource(SourcePlugin):
    """ServiceNow ticket source plugin"""
    
    def __init__(self, api_host: str, api_user: str, api_password: str):
        self.api_host = api_host
        self.api_user = api_user
        self.api_password = api_password
        self.source_name = "servicenow"
    
    def validate_ticket(self, webhook_payload: Dict) -> StandardTicket:
        """
        ServiceNow webhook payload → StandardTicket
        """
        record = webhook_payload.get('record', {})
        
        # Map ServiceNow fields to standard contract
        return StandardTicket(
            ticket_id=record.get('sys_id'),
            ticket_number=record.get('number'),
            title=record.get('short_description'),
            description=record.get('description'),
            category=self._map_category(record.get('category')),
            priority=self._map_priority(record.get('priority')),
            source=self.source_name,
            requester_location=self._extract_location(record),
            urgency=record.get('urgency', '3'),
            impact=record.get('impact', '3'),
            external_metadata={
                'assignment_group': record.get('assignment_group'),
                'caller_id': record.get('caller_id'),
                'state': record.get('state')
            }
        )
    
    def get_ticket_metadata(self, ticket_id: str) -> Dict:
        """Fetch ticket from ServiceNow API"""
        # Implementation calls ServiceNow API
        pass
    
    def _map_category(self, sn_category: str) -> str:
        """Map ServiceNow categories to standard categories"""
        mapping = {
            'network': 'network',
            'database': 'database',
            'application': 'application',
            'hardware': 'hardware'
        }
        return mapping.get(sn_category, 'other')
    
    def _map_priority(self, sn_priority: str) -> str:
        """Map ServiceNow priority to standard priority"""
        mapping = {'1': 'critical', '2': 'high', '3': 'medium', '4': 'low'}
        return mapping.get(sn_priority, 'medium')
    
    def _extract_location(self, record: Dict) -> Dict[str, Any]:
        """Extract location from ServiceNow record"""
        # Parse location field and return lat/lng/tz
        pass
```

### 4.2 Handler Plugin Template (Python)

```python
# plugins/handlers/handler_plugin_template.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class AssignmentGroup:
    """Template for assignment groups"""
    group_id: str
    name: str
    location: Dict[str, Any]  # {lat, lng, timezone}
    capabilities: List[str]
    status: str  # active, inactive, maintenance
    max_bandwidth: int
    current_load: int
    metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__

@dataclass
class AllocationDecision:
    """Template for allocation decisions from agent"""
    ticket_id: str
    decision_timestamp: str
    allocation: Dict[str, Any]  # {group_id, group_name, assigned_to_user_id}
    scores: Dict[str, float]
    rationale: str
    confidence: float

class HandlerPlugin(ABC):
    """Base class for all ticket handlers"""
    
    @abstractmethod
    def get_assignment_groups(self, category: str = None) -> List[AssignmentGroup]:
        """
        Return list of available assignment groups
        Filter by category if provided
        """
        pass
    
    @abstractmethod
    def assign_ticket(self, decision: AllocationDecision) -> bool:
        """
        Accept allocation decision from agent and update ticket
        Return True if successful
        """
        pass
    
    @abstractmethod
    def get_group_metrics(self, group_id: str) -> Dict[str, Any]:
        """Get current metrics for specific group"""
        pass
    
    def post_assignment_callback(self, ticket_id: str, group_id: str) -> None:
        """
        Optional: Called after successful assignment
        Can trigger workflows or notifications in handler system
        """
        pass

# Example: ServiceNow Handler Plugin
class ServiceNowHandler(HandlerPlugin):
    """ServiceNow assignment group handler plugin"""
    
    def __init__(self, api_host: str, api_user: str, api_password: str):
        self.api_host = api_host
        self.api_user = api_user
        self.api_password = api_password
        self.handler_name = "servicenow"
    
    def get_assignment_groups(self, category: str = None) -> List[AssignmentGroup]:
        """
        Query ServiceNow for assignment groups
        Apply category filter if provided
        """
        # Call ServiceNow API: GET /table/sys_user_group
        groups = self._query_servicenow_groups(category)
        
        return [
            AssignmentGroup(
                group_id=g['sys_id'],
                name=g['name'],
                location=self._extract_location(g),
                capabilities=self._extract_capabilities(g),
                status='active' if not g.get('inactive') else 'inactive',
                max_bandwidth=self._get_max_bandwidth(g),
                current_load=self._get_current_load(g['sys_id']),
                metrics=self._get_metrics(g['sys_id'])
            )
            for g in groups
        ]
    
    def assign_ticket(self, decision: AllocationDecision) -> bool:
        """
        Update ServiceNow ticket with allocation decision
        PUT /api/now/v2/table/incident/{ticket_id}
        """
        try:
            payload = {
                'assignment_group': decision.allocation['group_id'],
                'assigned_to': decision.allocation.get('assigned_to_user_id'),
                'work_notes': f"Auto-assigned by Agent (confidence: {decision.confidence:.2f})\n{decision.rationale}"
            }
            
            response = self._update_incident(decision.ticket_id, payload)
            return response.status_code == 200
        
        except Exception as e:
            logger.error(f"Failed to assign ticket {decision.ticket_id}: {e}")
            return False
    
    def get_group_metrics(self, group_id: str) -> Dict[str, Any]:
        """Get performance metrics for group from ServiceNow"""
        # Query historical data about this group
        pass
    
    def _query_servicenow_groups(self, category: str = None) -> List[Dict]:
        """Query ServiceNow for groups"""
        # Implementation
        pass
    
    def _get_max_bandwidth(self, group: Dict) -> int:
        """Extract max parallel tickets from group custom field"""
        # Implementation
        pass
    
    def _get_current_load(self, group_id: str) -> int:
        """Count open incidents assigned to group"""
        # Implementation
        pass
    
    def _get_metrics(self, group_id: str) -> Dict[str, Any]:
        """Get SLA stats, average resolution time, quality score"""
        # Implementation
        pass
```

---

## 5. REST API Specification

### 5.1 Plugin Registration

Before using plugins, register them:

```
POST /api/v1/plugins/register
Content-Type: application/json

{
  "type": "source",  # "source" or "handler"
  "name": "servicenow",
  "class": "plugins.sources.ServiceNowSource",
  "config": {
    "api_host": "https://dev12345.service-now.com",
    "api_user": "admin",
    "api_password": "password"
  }
}

Response: 201 Created
{
  "plugin_id": "source_servicenow_001",
  "status": "registered",
  "plugin_type": "source"
}
```

### 5.2 Webhook Endpoint (Source → Agent)

**Source systems POST to this endpoint when ticket is created:**

```
POST /api/v1/webhooks/ticket

Headers:
  X-Source-ID: servicenow      # identifies which source plugin sent this
  Content-Type: application/json

Body (StandardTicket):
{
  "ticket_id": "a1b2c3d4e5f6g7h8",
  "ticket_number": "INC0001234",
  "title": "Network connectivity issue",
  "description": "Users unable to access...",
  "category": "network",
  "priority": "high",
  "source": "servicenow",
  "requester_location": {
    "lat": 40.7128,
    "lng": -74.0060,
    "timezone": "America/New_York"
  },
  "urgency": "1",
  "impact": "2",
  "external_metadata": {
    "assignment_group_id": "",
    "caller_id": "user123"
  }
}

Response: 202 Accepted
{
  "status": "processing",
  "ticket_id": "a1b2c3d4e5f6g7h8",
  "message": "Ticket received. Allocation in progress."
}
```

### 5.3 Assignment Endpoint (Agent → Handler)

**Agent queries handler plugin for groups and assigns:**

```
POST /api/v1/handlers/allocate

Headers:
  X-Handler-ID: servicenow     # identifies which handler plugin to use
  Content-Type: application/json

Body (AllocationDecision):
{
  "ticket_id": "a1b2c3d4e5f6g7h8",
  "decision_timestamp": "2026-02-24T14:30:46.123Z",
  "allocation": {
    "group_id": "group456",
    "group_name": "Network Support Team",
    "assigned_to_user_id": "user789"
  },
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

Response: 200 OK
{
  "status": "assigned",
  "ticket_id": "a1b2c3d4e5f6g7h8",
  "group_id": "group456"
}
```

---

## 6. Agent Core Architecture

### 6.1 Agent Entry Point

```python
# agent/core.py

from typing import Dict, Any, List
from plugins.sources import StandardTicket, SourcePlugin
from plugins.handlers import AssignmentGroup, AllocationDecision, HandlerPlugin
from allocation_engine import AllocationEngine

class TicketAllocationAgent:
    """
    Pure decision maker.
    No knowledge of specific systems.
    Only cares about interfaces.
    """
    
    def __init__(self, source_plugins: Dict[str, SourcePlugin],
                 handler_plugins: Dict[str, HandlerPlugin],
                 engine: AllocationEngine):
        self.sources = source_plugins
        self.handlers = handler_plugins
        self.engine = engine
    
    async def process_webhook(self, webhook_payload: Dict, source_id: str) -> Dict:
        """
        Handle incoming webhook from source plugin
        1. Validate using source plugin
        2. Query handler for groups
        3. Run allocation algorithm
        4. Send to handler plugin
        """
        
        # Step 1: Use source plugin to validate/normalize ticket
        source_plugin = self.sources.get(source_id)
        if not source_plugin:
            raise ValueError(f"Unknown source: {source_id}")
        
        ticket = source_plugin.validate_ticket(webhook_payload)
        
        # Step 2: Query handler plugin for available groups
        handler_plugin = self._get_handler_for_category(ticket.category)
        groups = handler_plugin.get_assignment_groups(category=ticket.category)
        
        # Step 3: Run allocation algorithm (pure logic, no system knowledge)
        allocation = await self.engine.allocate(ticket, groups)
        
        # Step 4: Send allocation decision to handler plugin
        success = handler_plugin.assign_ticket(allocation)
        
        if success:
            handler_plugin.post_assignment_callback(ticket.ticket_id, allocation.allocation['group_id'])
        
        return {
            "status": "allocated" if success else "failed",
            "ticket_id": ticket.ticket_id,
            "decision": allocation.to_dict() if success else None
        }
    
    def _get_handler_for_category(self, category: str) -> HandlerPlugin:
        """
        Select which handler plugin to use
        Could be based on category, routing rules, etc.
        """
        # For now, use first available handler
        # Could be extended to route by category
        return next(iter(self.handlers.values()))
    
    async def health_check(self) -> Dict[str, Any]:
        """Check all plugins are operational"""
        return {
            "status": "healthy",
            "sources": {name: "connected" for name in self.sources.keys()},
            "handlers": {name: "connected" for name in self.handlers.keys()}
        }
```

### 6.2 Allocation Engine (Pure Decision Logic)

```python
# allocation_engine/engine.py

from typing import List
from plugins.handlers import AssignmentGroup, AllocationDecision
from plugins.sources import StandardTicket
from .scorers import *

class AllocationEngine:
    """
    Pure allocation algorithm.
    Zero awareness of source or handler systems.
    Takes generic inputs, returns generic outputs.
    """
    
    def __init__(self, weights: Dict[str, float], config: Dict):
        self.weights = weights  # Scoring parameter weights
        self.config = config
        self._validate_weights()
    
    async def allocate(self, ticket: StandardTicket, 
                      groups: List[AssignmentGroup]) -> AllocationDecision:
        """
        Main allocation logic
        """
        
        # Filter eligible groups
        eligible_groups = self._filter_groups(ticket, groups)
        
        if not eligible_groups:
            raise ValueError("No eligible groups available")
        
        # Score each group in parallel
        scores_map = await self._score_groups(eligible_groups, ticket)
        
        # Select best group
        best_group = max(scores_map, key=lambda g: scores_map[g]['composite'])
        scores = scores_map[best_group]
        
        # Create allocation decision
        return AllocationDecision(
            ticket_id=ticket.ticket_id,
            decision_timestamp=datetime.utcnow().isoformat(),
            allocation={
                'group_id': best_group.group_id,
                'group_name': best_group.name,
                'assigned_to_user_id': None  # Handler plugin assigns if needed
            },
            scores=scores,
            rationale=self._generate_rationale(best_group, scores),
            confidence=scores['composite']
        )
    
    async def _score_groups(self, groups: List[AssignmentGroup],
                           ticket: StandardTicket) -> Dict:
        """
        Score all groups in parallel
        """
        
        scorers = {
            'availability': AvailabilityScorer(),
            'bandwidth': BandwidthScorer(),
            'velocity': VelocityScorer(),
            'performance': PerformanceScorer(),
            'proximity': ProximityScorer(),
            'cultural_fit': CulturalScorer(),
            'timezone': TimezoneScorer()
        }
        
        scores = {}
        
        for group in groups:
            group_scores = {}
            
            # Score group on all parameters (can be parallelized)
            for param, scorer in scorers.items():
                score = await scorer.score(group, ticket)
                weight = self.weights[param]
                group_scores[param] = score
                group_scores[f'{param}_weighted'] = score * weight
            
            # Composite score
            group_scores['composite'] = sum(
                group_scores.get(f'{p}_weighted', 0)
                for p in scorers.keys()
            )
            
            scores[group] = group_scores
        
        return scores
    
    def _filter_groups(self, ticket: StandardTicket,
                      groups: List[AssignmentGroup]) -> List[AssignmentGroup]:
        """
        Filter to eligible groups
        - Has relevant capabilities
        - Has available bandwidth
        - Is active
        """
        
        eligible = []
        for group in groups:
            # Has matching capability
            if not any(cap in group.capabilities 
                      for cap in self._get_required_capabilities(ticket)):
                continue
            
            # Has available capacity
            if group.current_load >= group.max_bandwidth:
                continue
            
            # Is active
            if group.status != 'active':
                continue
            
            eligible.append(group)
        
        return eligible
    
    def _get_required_capabilities(self, ticket: StandardTicket) -> List[str]:
        """Map ticket category to required capabilities"""
        mapping = {
            'network': ['network', 'connectivity'],
            'application': ['application', 'software'],
            'database': ['database', 'data'],
            'hardware': ['hardware'],
            'other': []  # Any group can handle
        }
        return mapping.get(ticket.category, [])
```

---

## 7. Python Project Structure

```
poc-auto-ticket-handler/
├── agent/
│   ├── __init__.py
│   ├── core.py                    # Main Agent class
│   ├── app.py                     # Flask/FastAPI application
│   └── routes.py                  # HTTP endpoints
│
├── allocation_engine/
│   ├── __init__.py
│   ├── engine.py                  # Allocation algorithm
│   ├── scorers/
│   │   ├── __init__.py
│   │   ├── availability.py
│   │   ├── bandwidth.py
│   │   ├── velocity.py
│   │   ├── performance.py
│   │   ├── proximity.py
│   │   ├── cultural.py
│   │   └── timezone.py
│   └── config.py
│
├── plugins/
│   ├── __init__.py
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── source_plugin.py       # Abstract base class
│   │   ├── servicenow_source.py   # ServiceNow implementation
│   │   ├── jira_source.py         # Jira implementation (future)
│   │   └── custom_source.py       # Template for custom sources
│   │
│   └── handlers/
│       ├── __init__.py
│       ├── handler_plugin.py      # Abstract base class
│       ├── servicenow_handler.py  # ServiceNow implementation
│       ├── jira_handler.py        # Jira implementation (future)
│       └── custom_handler.py      # Template for custom handlers
│
├── models/
│   ├── __init__.py
│   ├── ticket.py                  # StandardTicket dataclass
│   ├── group.py                   # AssignmentGroup dataclass
│   ├── decision.py                # AllocationDecision dataclass
│   └── event.py                   # Event/Audit models
│
├── storage/
│   ├── __init__.py
│   ├── database.py                # SQLite/PostgreSQL
│   ├── metrics_store.py           # Store allocation decisions
│   └── audit_log.py               # Audit trail
│
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   ├── validators.py
│   ├── distance_calc.py           # Geolocation
│   └── timezone_util.py
│
├── config/
│   ├── __init__.py
│   ├── settings.py                # Configuration management
│   └── algorithm.yaml             # Weights and thresholds
│
├── tests/
│   ├── unit/
│   │   ├── test_engine.py
│   │   ├── test_scorers.py
│   │   └── test_plugins.py
│   └── integration/
│       ├── test_webhook_flow.py
│       └── test_e2e.py
│
├── requirements.txt
├── wsgi.py                        # Application entry point
└── README.md
```

---

## 8. Flask Application Example

```python
# agent/app.py

from flask import Flask, request, jsonify
from typing import Dict, Any
import logging
from agent.core import TicketAllocationAgent
from plugins.sources import ServiceNowSource
from plugins.handlers import ServiceNowHandler
from allocation_engine import AllocationEngine

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Initialize plugins
source_plugins = {
    'servicenow': ServiceNowSource(
        api_host=os.getenv('SN_HOST'),
        api_user=os.getenv('SN_USER'),
        api_password=os.getenv('SN_PASSWORD')
    )
}

handler_plugins = {
    'servicenow': ServiceNowHandler(
        api_host=os.getenv('SN_HOST'),
        api_user=os.getenv('SN_USER'),
        api_password=os.getenv('SN_PASSWORD')
    )
}

# Initialize agent
agent = TicketAllocationAgent(
    source_plugins,
    handler_plugins,
    AllocationEngine(weights=load_weights(), config=load_config())
)

@app.route('/api/v1/webhooks/ticket', methods=['POST'])
async def ticket_webhook():
    """
    Webhook endpoint for ticket creation
    Source systems POST to this endpoint
    """
    try:
        source_id = request.headers.get('X-Source-ID', 'servicenow')
        payload = request.get_json()
        
        logger.info(f"Webhook received from {source_id}")
        
        result = await agent.process_webhook(payload, source_id)
        
        return jsonify(result), 202
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
    
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health', methods=['GET'])
async def health():
    """Health check endpoint"""
    health_status = await agent.health_check()
    return jsonify(health_status), 200

@app.route('/api/v1/plugins/register', methods=['POST'])
def register_plugin():
    """Register a new plugin (dynamic registration)"""
    payload = request.get_json()
    plugin_type = payload.get('type')  # 'source' or 'handler'
    name = payload.get('name')
    
    # TODO: Implement dynamic plugin registration
    
    return jsonify({"status": "registered"}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
```

---

## 9. Adding a New Source Plugin

To add Jira as a ticket source:

```python
# plugins/sources/jira_source.py

from .source_plugin import SourcePlugin, StandardTicket
from typing import Dict, Any

class JiraSource(SourcePlugin):
    """Jira ticket source plugin"""
    
    def __init__(self, jira_url: str, jira_username: str, jira_api_token: str):
        self.jira_url = jira_url
        self.jira_username = jira_username
        self.jira_api_token = jira_api_token
        self.source_name = "jira"
    
    def validate_ticket(self, webhook_payload: Dict) -> StandardTicket:
        """
        Jira webhook payload → StandardTicket
        """
        issue = webhook_payload.get('issue', {})
        
        return StandardTicket(
            ticket_id=issue.get('key'),
            ticket_number=issue.get('key'),
            title=issue.get('fields', {}).get('summary'),
            description=issue.get('fields', {}).get('description'),
            category=self._map_jira_type(issue.get('fields', {}).get('issuetype')),
            priority=self._map_jira_priority(issue.get('fields', {}).get('priority')),
            source=self.source_name,
            requester_location=self._extract_reporter_location(issue),
            urgency=self._calc_urgency(issue),
            impact=self._calc_impact(issue),
            external_metadata={
                'project_key': issue.get('fields', {}).get('project', {}).get('key'),
                'assignee': issue.get('fields', {}).get('assignee'),
                'reporter': issue.get('fields', {}).get('reporter')
            }
        )
    
    def _map_jira_type(self, issue_type: Dict) -> str:
        """Map Jira issue type to standard category"""
        type_name = issue_type.get('name', '').lower() if issue_type else ''
        mapping = {
            'bug': 'application',
            'task': 'application',
            'incident': 'network',
            'problem': 'database'
        }
        return mapping.get(type_name, 'other')
```

Register it:

```
POST /api/v1/plugins/register
{
  "type": "source",
  "name": "jira",
  "class": "plugins.sources.JiraSource",
  "config": {
    "jira_url": "https://company.atlassian.net",
    "jira_username": "user@company.com",
    "jira_api_token": "token_here"
  }
}
```

---

## 10. Key Principles

1. **Agent is Plugin-Agnostic**
   - No hardcoded knowledge of ServiceNow, Jira, etc.
   - All source/handler logic in plugins

2. **Contract-Driven**
   - StandardTicket defines what sources must provide
   - AllocationDecision defines what handlers must accept
   - Plugins implement interfaces, not vice versa

3. **Single Responsibility**
   - Agent: Decision making only
   - Plugins: System integration only
   - Separation enables easy replacement

4. **Zero Coupling**
   - Agent doesn't import plugin implementations
   - Uses abstract base classes and dependency injection
   - Can add new plugins without modifying agent

5. **Extensible**
   - Add Jira source: Implement SourcePlugin
   - Add BMC ITSM handler: Implement HandlerPlugin
   - Agent requires zero changes

---

## 11. Migration Example: ServiceNow → Jira

**Current state**: ServiceNow source, ServiceNow handler

```python
agent = TicketAllocationAgent(
    source_plugins={'servicenow': ServiceNowSource(...)},
    handler_plugins={'servicenow': ServiceNowHandler(...)},
    engine=engine
)
```

**Future state**: Jira source, BMC ITSM handler

```python
from plugins.sources import JiraSource
from plugins.handlers import BMCITSMHandler

agent = TicketAllocationAgent(
    source_plugins={'jira': JiraSource(...)},
    handler_plugins={'bmc_itsm': BMCITSMHandler(...)},
    engine=engine
)
# Zero changes to agent.py!
```

---

## 12. Configuration File

```yaml
# config/algorithm.yaml

agent:
  port: 3000
  workers: 4
  timeout: 30

allocation:
  weights:
    availability: 0.25      # Current capacity
    bandwidth: 0.15         # Can handle complexity
    velocity: 0.20          # Resolution speed
    performance: 0.20       # Quality score
    proximity: 0.10         # Geographic distance
    cultural_fit: 0.05      # Expertise match
    timezone: 0.05          # TZ alignment

  thresholds:
    min_score: 0.40
    excellent_score: 0.80

plugins:
  sources:
    - name: servicenow
      enabled: true
      class: plugins.sources.ServiceNowSource
      config:
        api_host: ${SERVICENOW_HOST}
        api_user: ${SERVICENOW_USER}
        api_password: ${SERVICENOW_PASSWORD}
  
  handlers:
    - name: servicenow
      enabled: true
      class: plugins.handlers.ServiceNowHandler
      config:
        api_host: ${SERVICENOW_HOST}
        api_user: ${SERVICENOW_USER}
        api_password: ${SERVICENOW_PASSWORD}

storage:
  type: sqlite
  path: ./data/agent.db
  
logging:
  level: info
  format: json
```

---

## 13. Environment Variables

```bash
# .env

# ServiceNow
SERVICENOW_HOST=https://dev12345.service-now.com
SERVICENOW_USER=admin
SERVICENOW_PASSWORD=password

# Agent
AGENT_PORT=3000
LOG_LEVEL=info

# Storage
DB_PATH=./data/agent.db

# Webhook
WEBHOOK_SECRET=optional_secret
```

---

## 14. Testing Strategy

```python
# tests/unit/test_agent_abstraction.py

import pytest
from unittest.mock import Mock, AsyncMock
from agent.core import TicketAllocationAgent
from plugins.sources import StandardTicket
from plugins.handlers import AssignmentGroup

def test_agent_ignorant_of_specific_systems():
    """Verify agent doesn't care about plugin implementations"""
    
    # Create mock plugins (not real ServiceNow/Jira implementations)
    mock_source = Mock()
    mock_source.validate_ticket.return_value = StandardTicket(...)
    
    mock_handler = Mock()
    mock_handler.get_assignment_groups.return_value = [
        AssignmentGroup(...)
    ]
    
    # Agent works with any plugin following interfaces
    agent = TicketAllocationAgent(
        source_plugins={'mock': mock_source},
        handler_plugins={'mock': mock_handler},
        engine=mock_engine
    )
    
    # Process webhook using generic interface
    result = agent.process_webhook(payload, 'mock')
    
    assert result['status'] in ['allocated', 'failed']
    # Agent doesn't know (and doesn't care) this was a mock

def test_swappable_plugins():
    """Verify plugins are swappable without agent changes"""
    
    # Scenario 1: ServiceNow source + handler
    agent1 = TicketAllocationAgent(
        source_plugins={'servicenow': ServiceNowSource(...)},
        handler_plugins={'servicenow': ServiceNowHandler(...)},
        engine=engine
    )
    
    # Scenario 2: Jira source + BMC ITSM handler
    agent2 = TicketAllocationAgent(
        source_plugins={'jira': JiraSource(...)},
        handler_plugins={'bmc': BMCITSMHandler(...)},
        engine=engine  # Same engine!
    )
    
    # Both agents use identical core logic
    assert agent1.engine.allocate == agent2.engine.allocate
```

---

## 15. Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env from example
cp .env.example .env

# Run migrations
python -m alembic upgrade head

# Start agent
python wsgi.py

# Agent is now ready to receive webhooks
# Configure ServiceNow webhook to POST to: http://agent-url:3000/api/v1/webhooks/ticket
```

---

*Version: 1.0*
*Language: Python 3.8+*
*Framework: Flask or FastAPI*
*Date: February 24, 2026*
