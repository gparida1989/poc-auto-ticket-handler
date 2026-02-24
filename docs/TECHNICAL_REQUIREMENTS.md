# Technical Requirements Document
## POC Auto Ticket Handler - Free Tier Only

**Project**: Auto Ticket Handler POC  
**Date**: February 24, 2026  
**Scope**: Single-tenant, plugin-based allocation agent  
**Budget**: $0 (free tier services only)

---

## 1. Core Runtime & Framework

| Component | Requirement | Free Option | Notes |
|-----------|-------------|------------|-------|
| **Python** | Python 3.8+ | Python 3.11 (latest) | [python.org](https://www.python.org/downloads/) - Always free |
| **Web Framework** | REST API server | FastAPI or Flask | Both fully open-source, MIT licensed |
| **Package Manager** | Dependency management | pip (included with Python) | No cost |
| **Virtual Environment** | Isolation | venv (included with Python) | Standard library, no cost |

### Recommendation: Use FastAPI
- Smaller codebase than Flask
- Built-in async/await support
- Auto-generated API documentation (Swagger UI)
- Excellent performance for webhooks
- Production-ready

---

## 2. Database & Storage

| Component | Requirement | Free Option | POC Scale | Notes |
|-----------|-------------|-----------|-----------|-------|
| **Primary Database** | Store tickets, groups, decisions | SQLite 3 | 100K+ records | Built into Python, no setup |
| **File Storage** | Metrics, audit logs | Local filesystem | ~1GB | No cost |
| **Backup Storage** | Optional backup | Manual .db file export | As-needed | No cost |

### SQLite Rationale
- Zero setup required
- Perfect for POC (single instance)
- Easy to migrate to PostgreSQL later
- Built into Python standard library
- Typical POC needs: ~50MB database

### Database Schema (SQLite)
```sql
-- Tickets table
CREATE TABLE tickets (
    id TEXT PRIMARY KEY,
    ticket_number TEXT UNIQUE,
    source TEXT,
    title TEXT,
    category TEXT,
    priority TEXT,
    status TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Assignment Groups table
CREATE TABLE assignment_groups (
    id TEXT PRIMARY KEY,
    name TEXT,
    location_lat REAL,
    location_lng REAL,
    timezone TEXT,
    capabilities TEXT,  -- JSON array
    max_bandwidth INTEGER,
    current_load INTEGER,
    last_updated TIMESTAMP
);

-- Allocation Decisions table
CREATE TABLE allocation_decisions (
    id TEXT PRIMARY KEY,
    ticket_id TEXT,
    group_id TEXT,
    scores TEXT,  -- JSON object
    rationale TEXT,
    confidence REAL,
    created_at TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
    FOREIGN KEY (group_id) REFERENCES assignment_groups(id)
);

-- Metrics table (performance tracking)
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id TEXT,
    resolution_time_hours REAL,
    sla_compliance REAL,
    quality_score REAL,
    recorded_at TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES assignment_groups(id)
);

-- Audit Log table
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    ticket_id TEXT,
    details TEXT,  -- JSON
    created_at TIMESTAMP
);
```

---

## 3. External Services (Free Tier)

### 3.1 ServiceNow Developer Instance

| Component | Free Option | Setup Time | Details |
|-----------|-------------|-----------|---------|
| **ServiceNow Instance** | Free Developer Tier | 10 minutes | [developer.servicenow.com](https://developer.servicenow.com) |
| **License** | None required for POC | - | Free tier = 1 developer instance |
| **API Access** | Full REST API access | Included | All APIs available in free tier |
| **Users** | 1 concurrent user | - | Enough for single developer + testing |
| **Duration** | 30 days, renewable | - | Request extension when needed |

**What you get:**
- Full ServiceNow instance (Istanbul or later version)
- REST API enabled
- Webhook capability
- All out-of-box tables (Incident, CMDB, etc.)
- User management
- Workflow engine

**Registration Steps:**
1. Visit [developer.servicenow.com](https://developer.servicenow.com)
2. Sign up (free account)
3. Request developer instance (auto-provisioned)
4. Access: `https://{your-instance}.service-now.com`
5. Default credentials sent via email

---

### 3.2 Geolocation Services (Free Tier)

| Service | Free Tier | API Calls/Month | Use Case |
|---------|----------|-----------------|----------|
| **OpenStreetMap + Nominatim** | Open source, unlimited | Unlimited | Location geocoding, reverse geocoding |
| **Google Maps** | Free tier | 28,000 requests/month | Distance calculation, timezone lookup |
| **IP Geolocation** | ip-api.com free tier | 45 reqs/minute | Determine requester location from IP |

**Recommendation for POC: Nominatim (free, no key)**
```python
# No API key needed
import requests

def get_coordinates(location_name: str) -> dict:
    """
    Free geolocation using OpenStreetMap Nominatim
    Example: "New York, NY" → {"lat": 40.7128, "lng": -74.0060}
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": location_name,
        "format": "json",
        "limit": 1
    }
    response = requests.get(url, params=params)
    if response.json():
        result = response.json()[0]
        return {
            "lat": float(result["lat"]),
            "lng": float(result["lon"])
        }
```

---

### 3.3 Timezone Database (Free)

| Service | Details | Cost |
|---------|---------|------|
| **pytz** | Python package | Free, open source |
| **timezonefinder** | Python package | Free, open source |
| **IANA TZ Database** | Built into Python | Free |

**Usage:**
```python
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz

# Get timezone from coordinates
tf = TimezoneFinder()
tz_name = tf.timezone_at(lat=40.7128, lng=-74.0060)
# Results: "America/New_York"
```

---

## 4. Development Tools (All Free)

| Tool | Purpose | Type | Cost | Version |
|------|---------|------|------|---------|
| **VS Code** | IDE | Desktop | Free | Latest |
| **Git** | Version control | CLI | Free | Latest |
| **pytest** | Unit testing | Python package | Free | Latest |
| **Black** | Code formatting | Python package | Free | Latest |
| **Flake8** | Linting | Python package | Free | Latest |
| **mypy** | Type checking | Python package | Free | Latest |
| **Postman** | API testing | Desktop app | Free tier | Latest |
| **Docker** | Containerization | Desktop app | Free Community | Latest |

### Development Setup

```bash
# All free, total download size ~500MB

# 1. Python 3.11
# 2. VS Code
# 3. Docker (optional, for local container)
# 4. Git
# Total cost: $0
```

---

## 5. Testing Tools (All Free)

| Framework | Purpose | Free Option | Notes |
|-----------|---------|------------|-------|
| **pytest** | Unit testing | Full version (open source) | Industry standard for Python |
| **pytest-asyncio** | Async test support | Free | For testing async endpoints |
| **unittest.mock** | Mocking | Built into Python | Perfect for plugin testing |
| **requests-mock** | HTTP mocking | Free package | Mock external API calls |
| **sqlite3** | In-memory testing DB | Built into Python | Test database ops without files |

---

## 6. Deployment Options (Free Tier)

### Option A: Local Machine (Laptop)
```
Cost: $0
Setup: Run app locally
Best for: Solo development during POC

# Run locally
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

### Option B: AWS Free Tier
| Service | Free Tier | Details |
|---------|----------|---------|
| **EC2** | 750 hours/month (t2.micro) | Enough for continuous POC server |
| **RDS** | Not needed (using SQLite) | - |
| **API Gateway** | 1 million calls/month | Webhook endpoint |
| **Lambda** | 1 million invocations/month | Optional async processing |
| **CloudWatch** | 5GB logs/month | Monitoring |

**AWS Free Tier Cost**: $0 (for 12 months)

### Option C: Heroku Free Tier (Simple)
| Component | Free Tier | Notes |
|-----------|----------|-------|
| **Dyno** | Deprecated (Nov 2022) | No longer free |
| **Heroku Postgres** | Deprecated | Not available free |

*Note: Heroku free tier was discontinued. Use AWS or local development instead.*

### Option D: Docker + GitHub Codespaces
| Service | Free Tier | Details |
|---------|----------|---------|
| **GitHub Codespaces** | 60 hours/month (2-core) | Online VS Code environment |
| **GitHub Actions** | 2,000 minutes/month | CI/CD pipeline |
| **GitHub Packages** | Free | Container registry |

**Total Cost**: $0 (GitHub free account)

### Recommendation for POC: **AWS EC2 + Local SQLite**
- Simple to set up
- Reliable for testing
- Easy to access from anywhere
- Sufficient for POC workloads

---

## 7. Monitoring & Logging (All Free)

| Component | Framework | Cost | Setup |
|-----------|-----------|------|-------|
| **Logging** | Python `logging` module | Free, built-in | Write to stdout + files |
| **Application Logs** | Write to local files | Free | SQLite → JSON logs |
| **Performance Metrics** | `time` module | Free, built-in | Track allocation latency |
| **Health Checks** | Simple HTTP endpoint | Free | `/health` endpoint |
| **uptime Monitoring** | uptime.com free tier | Free | Monitor service availability |

**Logging Setup (Example)**
```python
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger(__name__)

# Log allocation decisions as JSON for analysis
def log_allocation(ticket_id, decision):
    logger.info(json.dumps({
        "event": "allocation_decision",
        "ticket_id": ticket_id,
        "group_id": decision["allocation"]["group_id"],
        "confidence": decision["confidence"],
        "timestamp": datetime.utcnow().isoformat()
    }))
```

---

## 8. Communication Infrastructure (Free)

| Need | Solution | Free Option | Setup |
|------|----------|------------|-------|
| **Email** (optional status) | SMTP | Gmail SMTP | Free with Google account |
| **Webhooks** | Standard HTTP POST | Built into Flask/FastAPI | No cost |
| **Slack Notifications** (optional) | Slack API | Free workspace + webhooks | Optional, free |

**Email via Gmail (Free)**
```python
import smtplib
from email.mime.text import MIMEText

def send_notification(to_email, subject, message):
    sender = "your-email@gmail.com"
    password = "your-app-password"  # Generate app-specific password
    
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.sendmail(sender, to_email, msg.as_string())
```

---

## 9. Source Control & Collaboration (Free)

| Service | Purpose | Free Option | Notes |
|---------|---------|------------|-------|
| **GitHub** | Repository hosting | Free public/private repos | Unlimited users, private repos |
| **GitHub Issues** | Tracking | Built-in | Track POC tasks |
| **GitHub Wiki** | Documentation | Built-in | Supplement to markdown docs |
| **GitHub Projects** | Planning | Board view, table view | Kanban for sprint tracking |

---

## 10. Complete Component List

### Runtime & Frameworks
- [ ] Python 3.11
- [ ] FastAPI or Flask
- [ ] pip + venv
- [ ] Uvicorn (ASGI server)

### Database
- [ ] SQLite 3
- [ ] SQLAlchemy (optional ORM)

### External Services
- [ ] ServiceNow Developer Instance
- [ ] Nominatim / OpenStreetMap (geolocation)
- [ ] pytz (timezone library)

### Python Packages (pip install)
- [ ] fastapi
- [ ] uvicorn
- [ ] pydantic
- [ ] sqlalchemy
- [ ] requests
- [ ] timezonefinder
- [ ] pytz
- [ ] pytest
- [ ] pytest-asyncio
- [ ] python-dotenv
- [ ] pyyaml

### Development Tools
- [ ] VS Code
- [ ] Git
- [ ] Docker (optional)
- [ ] Postman

### Testing
- [ ] pytest
- [ ] requests-mock
- [ ] unittest.mock

### Infrastructure
- [ ] AWS EC2 (t2.micro, free tier)
- [ ] OR: Local development machine

### Monitoring
- [ ] Python logging module
- [ ] File-based metrics
- [ ] Health check endpoint

### Version Control
- [ ] GitHub repository

---

## 11. Pre-POC Checklist

### Week 1: Setup
- [ ] Create GitHub account (if needed)
- [ ] Create ServiceNow developer instance
- [ ] Download Python 3.11
- [ ] Install VS Code
- [ ] Install Git
- [ ] Create GitHub repository

### Week 2: Environment Setup
- [ ] Create local virtual environment
- [ ] Install Python packages (FastAPI, etc.)
- [ ] Test ServiceNow API access
- [ ] Create SQLite database schema
- [ ] Test local Flask/FastAPI app

### Week 3: Development
- [ ] Implement core agent components
- [ ] Create ServiceNow plugins
- [ ] Build test suite
- [ ] Deploy to AWS EC2 (optional)

### Week 4: Testing
- [ ] End-to-end testing with ServiceNow
- [ ] Load testing (100+ tickets)
- [ ] Documentation

---

## 12. Python Environment Setup Script

```bash
# Clone repository
git clone <your-repo-url>
cd poc-auto-ticket-handler

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
python -m pytest tests/

# Run application
python -m uvicorn app.main:app --reload
```

### requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
requests==2.31.0
python-dotenv==1.0.0
pyyaml==6.0.1
timezonefinder==6.2.0
pytz==2023.3
pytest==7.4.3
pytest-asyncio==0.21.1
requests-mock==1.11.0
black==23.12.0
flake8==6.1.0
mypy==1.7.1
```

---

## 13. Configuration Management (Free)

### Environment Variables (.env)
```bash
# .env file (keep in .gitignore)

# ServiceNow Configuration
SERVICENOW_HOST=https://{your-instance}.service-now.com
SERVICENOW_USER=integration_user
SERVICENOW_PASSWORD=secure_password
SERVICENOW_API_KEY=optional_api_key

# Agent Configuration
AGENT_PORT=8000
AGENT_HOST=0.0.0.0
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./app.db

# Webhook Secret (optional)
WEBHOOK_SECRET=your_secret_key
```

### YAML Configuration (config.yaml)
```yaml
# Algorithm weights
scoring:
  availability_weight: 0.25
  bandwidth_weight: 0.15
  velocity_weight: 0.20
  performance_weight: 0.20
  proximity_weight: 0.10
  cultural_fit_weight: 0.05
  timezone_weight: 0.05

# Plugins
plugins:
  sources:
    - name: servicenow
      enabled: true
      type: servicenow
  handlers:
    - name: servicenow
      enabled: true
      type: servicenow

# Geolocation
geolocation:
  provider: nominatim  # free
  use_cache: true

# Logging
logging:
  level: INFO
  format: json
  file: logs/app.log
```

---

## 14. Cost Summary

| Component | Cost |
|-----------|------|
| Python 3.11 | $0 |
| FastAPI + Uvicorn | $0 |
| SQLite | $0 |
| ServiceNow Developer Instance | $0 |
| Nominatim Geolocation | $0 |
| pytest + testing frameworks | $0 |
| GitHub (with free account) | $0 |
| AWS EC2 (12 months free tier) | $0 |
| Development Tools (VS Code, Git, Docker) | $0 |
| ---| --- |
| **TOTAL for POC** | **$0** |

---

## 15. Production Migration Path (Future)

When ready to go beyond POC:

| Component | POC | Production |
|-----------|-----|-----------|
| Database | SQLite | PostgreSQL (AWS RDS) |
| Hosting | AWS EC2 free tier | AWS EC2 paid tier |
| Logging | File-based | CloudWatch + ELK Stack |
| Monitoring | Basic health check | Datadog / New Relic |
| API Gateway | Direct | AWS API Gateway |
| Load Balancing | N/A (single instance) | AWS ELB |
| Cost/Month | $0 | ~$200-500 (estimate) |

---

## 16. Troubleshooting Common Issues

### ServiceNow Instance Issues
**Problem**: Can't access developer instance  
**Solution**: Check email for provisioning link, or request a new one

**Problem**: API returns 401 Unauthorized  
**Solution**: Verify ServiceNow credentials, ensure REST API is enabled

### Database Issues
**Problem**: SQLite database locked  
**Solution**: Use WAL mode (Write-Ahead Logging) for concurrent access
```python
import sqlite3
conn = sqlite3.connect(':memory:')
conn.execute('PRAGMA journal_mode=WQL')
```

### Webhook Issues
**Problem**: ServiceNow webhook not reaching agent  
**Solution**: 
- Ensure agent is publicly accessible (EC2 with security group)
- Test with Postman first
- Check firewall rules

---

## 17. Resources & Links

| Resource | Link |
|----------|------|
| **Python Download** | https://www.python.org/downloads/ |
| **FastAPI Docs** | https://fastapi.tiangolo.com/ |
| **ServiceNow Developer** | https://developer.servicenow.com/ |
| **SQLite Documentation** | https://www.sqlite.org/docs.html |
| **pytest Documentation** | https://docs.pytest.org/ |
| **AWS Free Tier** | https://aws.amazon.com/free/ |
| **GitHub Guides** | https://guides.github.com/ |
| **OpenStreetMap Nominatim** | https://nominatim.org/ |

---

*Document Version: 1.0*  
*Last Updated: February 24, 2026*  
*Status: Ready for POC Implementation*
