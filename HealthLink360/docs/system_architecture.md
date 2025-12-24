# HealthLink360 System Architecture

**Version**: 1.0  
**Last Updated**: December 2025  
**Status**: Production-Ready

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Design Principles](#design-principles)
3. [System Components](#system-components)
4. [Data Flow Architecture](#data-flow-architecture)
5. [Technology Stack](#technology-stack)
6. [Scalability & Performance](#scalability--performance)
7. [Disaster Recovery](#disaster-recovery)
8. [Integration Points](#integration-points)

---

## Architecture Overview

HealthLink360 implements a **microservices-based, agent-oriented architecture** designed for national-scale healthcare operations. The system is built on three foundational pillars:

### 1. **Dual Backend Architecture**

The system separates operational concerns from analytical concerns through two independent backend systems:

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              React.js Frontend Application                │  │
│  │  • Patient Portal      • Admin Dashboard                  │  │
│  │  • Doctor Interface    • NIH Portal                       │  │
│  │  • Researcher Portal   • Emergency Console                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS/REST API
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
┌───────▼──────────────┐                 ┌──────────▼───────────────┐
│   BACKEND CORE       │                 │  BACKEND REPORTING       │
│   (Operations)       │                 │  (Analytics & Research)  │
│                      │                 │                          │
│ ┌──────────────────┐ │                 │ ┌──────────────────────┐ │
│ │ Operational      │ │                 │ │ Department Agents    │ │
│ │ Agents           │ │                 │ │ • Cardiology         │ │
│ │ • Tracking       │ │                 │ │ • Maternal Health    │ │
│ │ • Maternal       │ │                 │ │ • Infectious Disease │ │
│ │ • Mental Health  │ │                 │ │ • Nutrition          │ │
│ │ • Pharmacy       │ │                 │ │ • Mental Health      │ │
│ │ • Criminal Case  │ │                 │ │ • NCD                │ │
│ │ • Waste Mgmt     │ │                 │ │ • Endocrinology      │ │
│ └──────────────────┘ │                 │ │ • Oncology           │ │
│                      │                 │ └──────────────────────┘ │
│ ┌──────────────────┐ │                 │                          │
│ │ FastAPI Server   │ │                 │ ┌──────────────────────┐ │
│ │ PostgreSQL DB    │ │                 │ │ Orchestrator Agents  │ │
│ │ Redis Cache      │ │                 │ │ • Hospital Central   │ │
│ │ WebSocket        │ │                 │ │ • NIH Agent          │ │
│ └──────────────────┘ │                 │ │ • R&D Agent          │ │
└──────────────────────┘                 │ └──────────────────────┘ │
                                         │                          │
                                         │ ┌──────────────────────┐ │
                                         │ │ FastAPI Server       │ │
                                         │ │ MongoDB              │ │
                                         │ │ Apache Kafka         │ │
                                         │ │ Celery Workers       │ │
                                         │ └──────────────────────┘ │
                                         └──────────────────────────┘
                              │
                              │ MCP Protocol
                              │
┌─────────────────────────────▼─────────────────────────────────────┐
│                      MCP SERVER LAYER                              │
│                                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────┐│
│  │  Core    │  │   NIH    │  │Orchestr. │  │ Report   │  │ R&D ││
│  │  Agents  │  │   MCP    │  │   MCP    │  │ Gen MCP  │  │ MCP ││
│  │   MCP    │  │          │  │          │  │          │  │     ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └─────┘│
└────────────────────────────────────────────────────────────────────┘
```

**Rationale for Separation**:

- **Performance Isolation**: Real-time operations (emergency response) are not impacted by heavy analytical queries
- **Security Boundaries**: Sensitive operational data (criminal cases) isolated from research access
- **Scalability**: Each backend can scale independently based on load patterns
- **Technology Optimization**: Different databases optimized for transactional vs. analytical workloads

---

### 2. **Agent-Based Intelligence**

The system employs **14 specialized AI agents** organized into three tiers:

#### Tier 1: Operational Agents (Backend Core)
- Direct patient care and service delivery
- Real-time decision making
- Low latency requirements (<500ms)

#### Tier 2: Department Agents (Backend Reporting)
- Data aggregation and analysis
- Quarterly reporting cycles
- Medium latency tolerance (<5s)

#### Tier 3: Orchestrator Agents (Backend Reporting)
- Multi-agent coordination
- National-level decision making
- High latency tolerance (<30s)

---

### 3. **MCP Server Infrastructure**

Model Context Protocol (MCP) servers provide:

- **Inter-Agent Communication**: Standardized messaging between agents
- **State Management**: Shared context across distributed agents
- **Workflow Orchestration**: Multi-step process coordination
- **Timeout Management**: Graceful handling of long-running operations

---

## Design Principles

### 1. **Separation of Concerns**

Each component has a single, well-defined responsibility:

- **Frontend**: User interaction and presentation
- **Backend Core**: Operational healthcare services
- **Backend Reporting**: Analytics and research
- **MCP Servers**: Agent coordination
- **Shared Libraries**: Cross-cutting concerns (logging, PII redaction)

### 2. **Security by Design**

Security is not an afterthought but a foundational principle:

- **Defense in Depth**: Multiple layers of security controls
- **Least Privilege**: Users and agents have minimum necessary permissions
- **Data Encryption**: At rest (AES-256) and in transit (TLS 1.3)
- **Audit Logging**: Comprehensive, immutable audit trails
- **PII Protection**: Automated redaction and anonymization

### 3. **Scalability First**

The architecture supports growth from single hospital to national scale:

- **Horizontal Scaling**: Add more servers to handle increased load
- **Database Sharding**: Partition data across multiple database instances
- **Caching Strategy**: Multi-tier caching (Redis, CDN)
- **Asynchronous Processing**: Non-blocking operations for heavy workloads

### 4. **Resilience & Fault Tolerance**

The system is designed to handle failures gracefully:

- **Circuit Breakers**: Prevent cascading failures
- **Retry Logic**: Automatic retry with exponential backoff
- **Graceful Degradation**: Core services remain available during partial outages
- **Health Checks**: Continuous monitoring of component health

### 5. **Compliance & Auditability**

Healthcare regulations require strict compliance:

- **HIPAA Compliance**: Protected Health Information (PHI) safeguards
- **WHO Standards**: International Health Regulations (IHR) compliance
- **Data Sovereignty**: Data residency requirements for national health data
- **Audit Trails**: Complete traceability of all data access and modifications

---

## System Components

### Frontend Layer

**Technology**: React.js 18+ with TypeScript

**Key Features**:
- **Responsive Design**: Mobile-first approach for field workers
- **Real-Time Updates**: WebSocket integration for emergency notifications
- **Offline Capability**: Service workers for limited offline functionality
- **Accessibility**: WCAG 2.1 AA compliance

**Component Structure**:
```
src/
├── components/          # Reusable UI components
│   ├── common/          # Buttons, forms, modals
│   ├── patient/         # Patient-specific components
│   ├── admin/           # Admin dashboard components
│   └── charts/          # Data visualization components
├── pages/               # Page-level components
│   ├── PatientPortal/
│   ├── DoctorDashboard/
│   ├── AdminPanel/
│   ├── NIHPortal/
│   └── ResearchPortal/
├── services/            # API service layers
│   ├── api.js           # Base API client
│   ├── auth.js          # Authentication service
│   ├── patient.js       # Patient data service
│   └── reporting.js     # Reporting service
└── App.jsx              # Main application entry
```

---

### Backend Core (Operations)

**Technology**: FastAPI (Python 3.10+), PostgreSQL, Redis

**Database Schema**:

```sql
-- Core tables
patients (id, cnic_encrypted, name, dob, contact, created_at)
appointments (id, patient_id, doctor_id, datetime, status)
medical_records (id, patient_id, diagnosis, treatment, created_by)
prescriptions (id, patient_id, medication, dosage, prescribed_by)
emergency_cases (id, patient_id, severity, ambulance_id, status)
maternal_records (id, patient_id, pregnancy_week, risk_level)
mental_health_sessions (id, patient_id, therapist_id, notes_encrypted)
pharmacy_inventory (id, drug_name, quantity, expiry_date)
criminal_cases (id, case_number, evidence_hash, chain_of_custody)
waste_logs (id, waste_type, quantity, disposal_date, manifest_id)

-- User management
users (id, username, role, hospital_id, permissions)
audit_logs (id, user_id, action, resource, timestamp, ip_address)
```

**API Endpoints** (Sample):

```
POST   /api/v1/patients/register          # Register new patient
GET    /api/v1/patients/{id}              # Get patient details
POST   /api/v1/emergency/dispatch         # Dispatch ambulance
GET    /api/v1/pharmacy/inventory         # Check drug inventory
POST   /api/v1/maternal/record            # Record maternal health data
POST   /api/v1/mental-health/session      # Log therapy session
POST   /api/v1/criminal/evidence          # Log forensic evidence
POST   /api/v1/waste/log                  # Log waste disposal
```

---

### Backend Reporting (Analytics)

**Technology**: FastAPI (Python 3.10+), MongoDB, Apache Kafka, Celery

**MongoDB Collections**:

```javascript
// Department reports
cardiology_reports {
  hospital_id, quarter, year,
  procedures: { angioplasty: count, bypass: count },
  outcomes: { mortality_rate, readmission_rate },
  submitted_at, approved_by
}

maternal_health_reports {
  hospital_id, quarter, year,
  deliveries: { total, cesarean, vaginal },
  maternal_mortality_ratio,
  prenatal_coverage_rate,
  submitted_at
}

infectious_disease_reports {
  hospital_id, quarter, year,
  diseases: [{ icd10_code, case_count, deaths }],
  outbreaks: [{ disease, start_date, end_date, cases }],
  vaccination_coverage: { measles: rate, polio: rate }
}

// National aggregations
national_statistics {
  quarter, year,
  total_hospitals, total_patients,
  disease_burden: { ... },
  resource_utilization: { ... },
  generated_at, generated_by
}

// Research datasets
research_datasets {
  dataset_id, irb_approval_number,
  description, anonymization_level,
  record_count, created_at,
  access_log: [{ researcher_id, accessed_at }]
}
```

**Kafka Topics**:

```
hospital.reports.submitted       # New hospital reports
nih.aggregation.requested        # NIH requests national aggregation
research.dataset.requested       # Research dataset requests
outbreak.alert                   # Disease outbreak alerts
```

**Celery Tasks**:

```python
@celery.task
def aggregate_quarterly_reports(quarter, year):
    """Aggregate all hospital reports for a quarter"""
    
@celery.task
def generate_who_report(quarter, year):
    """Generate WHO-compliant report"""
    
@celery.task
def anonymize_research_dataset(dataset_id):
    """Apply k-anonymity to research dataset"""
```

---

### MCP Servers

Each MCP server is a standalone FastAPI application providing agent coordination services.

#### Core Agents MCP

**Port**: 9000  
**Timeout**: 30 seconds

**Endpoints**:

```python
POST /mcp/dispatch_emergency
POST /mcp/update_patient_status
POST /mcp/coordinate_handoff
GET  /mcp/check_resource_availability
```

**State Management**: Redis-backed shared state for active emergencies

---

#### NIH MCP

**Port**: 9001  
**Timeout**: 120 seconds

**Endpoints**:

```python
POST /mcp/aggregate_national_data
POST /mcp/generate_who_report
POST /mcp/publish_health_bulletin
POST /mcp/coordinate_outbreak_response
```

**State Management**: MongoDB for aggregation state tracking

---

#### Orchestrator MCP

**Port**: 9002  
**Timeout**: 180 seconds

**Endpoints**:

```python
POST /mcp/initiate_quarterly_workflow
POST /mcp/coordinate_department_agents
POST /mcp/escalate_critical_issue
POST /mcp/generate_executive_summary
```

**State Management**: Workflow state machine in PostgreSQL

---

#### Report Generation MCP

**Port**: 9003  
**Timeout**: 60 seconds

**Endpoints**:

```python
POST /mcp/generate_pdf_report
POST /mcp/create_data_visualization
POST /mcp/compile_quarterly_report
POST /mcp/export_to_excel
```

**Dependencies**: WeasyPrint (PDF), Matplotlib (charts), Pandas (data processing)

---

#### R&D MCP

**Port**: 9004  
**Timeout**: 90 seconds

**Endpoints**:

```python
POST /mcp/register_clinical_trial
POST /mcp/match_patients_to_trials
POST /mcp/aggregate_research_data
POST /mcp/coordinate_university_collaboration
```

**State Management**: Clinical trial registry in MongoDB

---

## Data Flow Architecture

### 1. **Patient Care Flow** (Backend Core)

```
Patient → Frontend → Backend Core → Operational Agent → Database
                                         ↓
                                    MCP Server
                                         ↓
                              Other Agents (if needed)
```

**Example: Emergency Dispatch**

1. Emergency call received → Frontend emergency console
2. Frontend sends dispatch request → Backend Core API
3. Backend Core validates request → Tracking Agent
4. Tracking Agent checks ambulance availability → Core Agents MCP
5. MCP coordinates with Hospital Central Agent → Resource allocation
6. Ambulance dispatched → Real-time updates via WebSocket
7. Patient handoff → Mental Health/Maternal Health agents (if needed)

---

### 2. **Quarterly Reporting Flow** (Backend Reporting)

```
Hospital Data → Department Agents → Hospital Central Agent → NIH Agent → WHO
                                                                  ↓
                                                             R&D Agent
                                                                  ↓
                                                            Universities
```

**Example: Quarterly Workflow**

1. **Day 1**: Orchestrator MCP initiates quarterly workflow
2. **Days 1-15**: Department agents collect data from Backend Core
3. **Days 16-25**: Department agents compile reports → MongoDB
4. **Days 26-35**: Hospital Central Agent aggregates → Kafka event
5. **Days 36-45**: Hospitals submit to NIH Agent → Validation
6. **Days 46-60**: NIH Agent aggregates national data → National statistics
7. **Days 61-70**: R&D Agent identifies research opportunities
8. **Days 71-80**: NIH Agent generates policy recommendations
9. **Days 81-85**: Report Generation MCP creates WHO report
10. **Days 86-90**: Feedback disseminated to hospitals

---

### 3. **Research Data Flow**

```
Researcher Request → R&D Agent → IRB Approval → Anonymization → Dataset Provision
                                                      ↓
                                              Audit Logging
```

**Example: Research Dataset Request**

1. Researcher submits dataset request → Research Portal
2. R&D Agent validates IRB approval → Backend Reporting
3. Dataset anonymization task → Celery worker
4. PII redaction applied → `shared/pii_redaction.py`
5. K-anonymity verification → Statistical disclosure control
6. Dataset packaged → Secure download link
7. Access logged → Audit trail

---

## Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Web Framework | FastAPI | 0.104+ | High-performance async API |
| Language | Python | 3.10+ | Backend logic |
| ORM | SQLAlchemy | 2.0+ | Database abstraction |
| Validation | Pydantic | 2.0+ | Data validation |
| Task Queue | Celery | 5.3+ | Asynchronous processing |
| Message Broker | Apache Kafka | 3.5+ | Event streaming |
| Cache | Redis | 7.0+ | Session & data caching |

### Databases

| Type | Technology | Version | Use Case |
|------|-----------|---------|----------|
| Relational | PostgreSQL | 14+ | Operational data (Backend Core) |
| Document | MongoDB | 6.0+ | Reporting data (Backend Reporting) |
| In-Memory | Redis | 7.0+ | Caching, session management |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | React | 18+ | UI framework |
| Language | TypeScript | 5.0+ | Type-safe JavaScript |
| State Management | Redux Toolkit | 1.9+ | Global state |
| Routing | React Router | 6.0+ | Client-side routing |
| HTTP Client | Axios | 1.5+ | API communication |
| Charts | Chart.js | 4.0+ | Data visualization |

### Infrastructure

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Containerization | Docker | 24+ | Application packaging |
| Orchestration | Docker Compose | 2.20+ | Multi-container deployment |
| Web Server | Nginx | 1.24+ | Reverse proxy, load balancing |
| Process Manager | Supervisor | 4.2+ | Process monitoring |

### Security

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Authentication | JWT | Stateless authentication |
| Encryption (Transit) | TLS 1.3 | HTTPS communication |
| Encryption (Rest) | AES-256 | Database encryption |
| Password Hashing | Argon2 | Secure password storage |
| PII Redaction | Custom | Automated data anonymization |

---

## Scalability & Performance

### Horizontal Scaling Strategy

**Backend Core**:
- Load balancer (Nginx) distributes requests across multiple FastAPI instances
- PostgreSQL read replicas for query distribution
- Redis cluster for distributed caching

**Backend Reporting**:
- Celery workers scale independently based on queue depth
- MongoDB sharding by hospital_id for data distribution
- Kafka partitioning for parallel event processing

**MCP Servers**:
- Each MCP server can run multiple instances behind load balancer
- Stateless design allows seamless scaling

### Performance Targets

| Operation | Target Latency | Throughput |
|-----------|---------------|------------|
| Patient lookup | <100ms | 1000 req/s |
| Emergency dispatch | <500ms | 100 req/s |
| Prescription creation | <200ms | 500 req/s |
| Report generation | <30s | 10 req/s |
| National aggregation | <120s | 1 req/min |

### Caching Strategy

**Layer 1: Browser Cache**
- Static assets (CSS, JS, images): 1 year
- API responses (patient data): No cache (sensitive)

**Layer 2: CDN Cache**
- Public resources (documentation, images): 1 month
- API responses: No cache

**Layer 3: Redis Cache**
- User sessions: 24 hours
- Frequently accessed data (hospital info): 1 hour
- Aggregated statistics: 15 minutes

**Layer 4: Database Query Cache**
- PostgreSQL query cache: Automatic
- MongoDB aggregation cache: 5 minutes

---

## Disaster Recovery

### Backup Strategy

**Databases**:
- **PostgreSQL**: Daily full backups, hourly incremental backups
- **MongoDB**: Daily full backups, continuous oplog backups
- **Redis**: Daily RDB snapshots, AOF for point-in-time recovery

**Retention**:
- Daily backups: 30 days
- Weekly backups: 1 year
- Monthly backups: 7 years (regulatory compliance)

**Storage**:
- Primary: On-site NAS
- Secondary: Cloud storage (encrypted)
- Tertiary: Offsite tape backup (quarterly)

### Recovery Time Objectives (RTO)

| Component | RTO | RPO |
|-----------|-----|-----|
| Backend Core | 1 hour | 15 minutes |
| Backend Reporting | 4 hours | 1 hour |
| MCP Servers | 30 minutes | 5 minutes |
| Databases | 2 hours | 15 minutes |

### High Availability

**Database Replication**:
- PostgreSQL: Primary-replica setup with automatic failover
- MongoDB: Replica set with 3 nodes (1 primary, 2 secondaries)
- Redis: Sentinel for automatic failover

**Application Redundancy**:
- Minimum 2 instances of each backend service
- Load balancer health checks every 10 seconds
- Automatic removal of unhealthy instances

---

## Integration Points

### External Systems

**National Identity Database**:
- **Purpose**: CNIC verification
- **Protocol**: SOAP/REST API
- **Authentication**: Mutual TLS
- **Rate Limit**: 100 requests/minute

**WHO DHIS2**:
- **Purpose**: International health reporting
- **Protocol**: REST API
- **Authentication**: OAuth 2.0
- **Data Format**: JSON (DHIS2 schema)

**NIH Central Database**:
- **Purpose**: National health data submission
- **Protocol**: REST API
- **Authentication**: API key + JWT
- **Data Format**: Custom JSON schema

**University Research Portals**:
- **Purpose**: Research collaboration
- **Protocol**: REST API
- **Authentication**: OAuth 2.0
- **Data Format**: FHIR (HL7)

### Internal Integrations

**Backend Core ↔ Backend Reporting**:
- **Method**: Scheduled data synchronization (nightly)
- **Protocol**: Internal REST API
- **Data**: Anonymized operational statistics
- **Security**: Internal network only, mutual TLS

**Backends ↔ MCP Servers**:
- **Method**: Real-time API calls
- **Protocol**: HTTP/2
- **Timeout**: Varies by MCP server (30-180s)
- **Retry**: Exponential backoff (max 3 retries)

---

## Monitoring & Observability

### Logging

**Centralized Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)

**Log Levels**:
- **DEBUG**: Development only
- **INFO**: Normal operations
- **WARNING**: Potential issues
- **ERROR**: Errors requiring attention
- **CRITICAL**: System failures

**Log Retention**:
- Application logs: 90 days
- Audit logs: 7 years
- Error logs: 1 year

### Metrics

**Application Metrics** (Prometheus):
- Request rate, latency, error rate
- Database connection pool utilization
- Cache hit/miss ratio
- Celery queue depth

**System Metrics**:
- CPU, memory, disk utilization
- Network throughput
- Database performance (queries/sec, slow queries)

**Business Metrics**:
- Patient registrations per day
- Emergency response time
- Report submission rate
- System uptime

### Alerting

**Critical Alerts** (PagerDuty):
- Database connection failures
- Backend service down
- Emergency dispatch failures
- Security incidents

**Warning Alerts** (Email):
- High error rate (>1%)
- Slow response time (>2s average)
- Low disk space (<20%)
- Backup failures

---

## Conclusion

HealthLink360's architecture is designed for **scalability, security, and resilience** at national scale. The dual-backend approach ensures operational efficiency while enabling advanced analytics. The agent-based system provides intelligent, autonomous decision-making across all levels of healthcare delivery.

For specific implementation details, refer to:
- [Agent Roles](agent_roles.md)
- [Department Roles](department_roles.md)
- [Workflows](workflows.md)
- [API Endpoints](api_endpoints.md)
- [Security & Compliance](security_compliance.md)
