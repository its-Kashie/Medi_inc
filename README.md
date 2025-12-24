# HealthLink360

**Enterprise Healthcare Management & Intelligence System**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-production--ready-green.svg)]()

---

## 🏥 Executive Summary

**HealthLink360** is a comprehensive, AI-powered healthcare management platform designed to orchestrate multi-level healthcare operations across national health systems. The platform integrates real-time patient care, emergency response, maternal health tracking, mental health services, pharmacy management, criminal case handling, waste management, and advanced reporting capabilities for research and policy-making.

### Key Capabilities

- **Dual Backend Architecture**: Separate backends for operational healthcare and reporting/research
- **Multi-Agent System**: 14+ specialized AI agents for department-specific and orchestration tasks
- **MCP Server Infrastructure**: 5 dedicated Model Context Protocol servers for agent coordination
- **Compliance-First Design**: Built-in PII redaction, CNIC verification, and medico-legal isolation
- **National Scale**: Supports quarterly reporting workflows across hospitals, NIH, and research institutions

---

## 📋 Table of Contents

1. [System Architecture](#-system-architecture)
2. [Project Structure](#-project-structure)
3. [Backend Systems](#-backend-systems)
4. [Agent Ecosystem](#-agent-ecosystem)
5. [MCP Servers](#-mcp-servers)
6. [User Roles & Permissions](#-user-roles--permissions)
7. [Workflows](#-workflows)
8. [Security & Compliance](#-security--compliance)
9. [Installation & Setup](#-installation--setup)
10. [API Documentation](#-api-documentation)
11. [Contributing](#-contributing)

---

## 🏗 System Architecture

HealthLink360 employs a **microservices-oriented architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                          │
│              (React.js - Patient & Admin UI)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────────┐    ┌────────▼─────────────┐
│  Backend Core    │    │ Backend Reporting    │
│  (Operations)    │    │ (Analytics & R&D)    │
│                  │    │                      │
│ • Patient Care   │    │ • Dept. Agents       │
│ • Emergency      │    │ • Orchestrators      │
│ • Pharmacy       │    │ • WHO Reports        │
│ • Waste Mgmt     │    │ • NIH Coordination   │
└────────┬─────────┘    └──────────┬───────────┘
         │                         │
         └────────┬────────────────┘
                  │
         ┌────────▼─────────┐
         │   MCP Servers    │
         │                  │
         │ • Core Agents    │
         │ • NIH            │
         │ • Orchestrator   │
         │ • Report Gen     │
         │ • R&D            │
         └──────────────────┘
```

### Architecture Principles

1. **Separation of Concerns**: Healthcare operations isolated from reporting/analytics
2. **Agent-Based Intelligence**: Specialized agents for each medical department and function
3. **Scalable Communication**: MCP servers handle inter-agent messaging and coordination
4. **Data Security**: Multi-layer PII protection and role-based access control
5. **Compliance by Design**: WHO, NIH, and national health standards built-in

---

## 📁 Project Structure

```
HealthLink360/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── docker-compose.yml                 # Container orchestration
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore rules
│
├── frontend/                          # React.js frontend application
│   ├── public/                        # Static assets
│   ├── src/
│   │   ├── components/                # Reusable UI components
│   │   ├── pages/                     # Page-level components
│   │   ├── services/                  # API service layers
│   │   └── App.jsx                    # Main application entry
│   └── package.json                   # Node.js dependencies
│
├── backend_core/                      # Backend 1: Healthcare Operations
│   ├── backend.py                     # FastAPI application entry
│   ├── routers/                       # API route handlers
│   ├── agents/                        # Operational agents
│   ├── services/                      # Business logic services
│   ├── models/                        # Database models
│   └── tests/                         # Unit & integration tests
│
├── backend_reporting/                 # Backend 2: Reporting & Research
│   ├── api_server.py                  # FastAPI application entry
│   ├── agents/
│   │   ├── department/                # Department-specific agents
│   │   └── orchestrators/             # High-level orchestration agents
│   ├── workflows/                     # Workflow definitions
│   ├── database/                      # Reporting database schemas
│   └── tests/                         # Unit & integration tests
│
├── mcp_servers/                       # Model Context Protocol Servers
│   ├── core_agents_mcp/
│   │   └── agents_mcp.py              # Core operational agent MCP
│   ├── nih_mcp/
│   │   └── nih_mcp.py                 # NIH coordination MCP
│   ├── orchestrator_mcp/
│   │   └── agent_orchestrator_mcp.py  # Orchestrator MCP
│   ├── report_generation_mcp/
│   │   └── report_generation_mcp_tool.py  # Report generation MCP
│   └── rnd_mcp/
│       └── rnd_mcp_tools.py           # Research & Development MCP
│
├── shared/                            # Shared utilities across backends
│   ├── config.py                      # Configuration management
│   ├── logger.py                      # Centralized logging
│   ├── pii_redaction.py               # PII protection utilities
│   └── utils.py                       # Common helper functions
│
├── data/                              # Reference data & configurations
│   ├── hospitals.json                 # Hospital registry
│   ├── departments.json               # Department configurations
│   ├── universities.json              # Research institution registry
│   └── disease_codes.json             # ICD-10 & disease classifications
│
├── docs/                              # Comprehensive documentation
│   ├── system_architecture.md         # Detailed architecture guide
│   ├── agent_roles.md                 # Agent responsibilities
│   ├── department_roles.md            # Department-specific documentation
│   ├── workflows.md                   # Workflow specifications
│   ├── api_endpoints.md               # API reference
│   └── security_compliance.md         # Security & compliance guide
│
├── filled_reports/                    # Completed reports from hospitals
├── generated_reports/                 # System-generated reports
│   └── who_proposals/                 # WHO submission-ready reports
│
├── logs/                              # Application logs
└── scripts/                           # Utility scripts
    ├── start_backend_core.sh          # Start operational backend
    ├── start_backend_reporting.sh     # Start reporting backend
    └── run_full_workflow.py           # Execute quarterly workflow
```

---

## 🔧 Backend Systems

### Backend 1: Healthcare Operations (`backend_core/`)

**Purpose**: Real-time healthcare service delivery and emergency response

**Technology Stack**:
- FastAPI (Python 3.10+)
- PostgreSQL (Patient records)
- Redis (Session management)
- WebSocket (Real-time updates)

**Core Agents**:

#### 1. **Tracking Agent** (Emergency & Ambulance)
- **Purpose**: Real-time emergency response coordination
- **Responsibilities**:
  - Ambulance dispatch and tracking
  - Emergency room bed availability
  - Critical patient handoff protocols
  - GPS-based routing optimization
- **Data Handled**: Patient vitals, location data, emergency codes, hospital capacity
- **Security**: End-to-end encryption for patient data in transit

#### 2. **Maternal Health Agent**
- **Purpose**: Prenatal, delivery, and postnatal care management
- **Responsibilities**:
  - Pregnancy tracking and milestone monitoring
  - High-risk pregnancy identification
  - Delivery scheduling and resource allocation
  - Postpartum care coordination
- **Data Handled**: Maternal health records, fetal monitoring data, delivery outcomes
- **Security**: HIPAA-compliant data storage, restricted access to OB/GYN personnel

#### 3. **Mental Health Agent**
- **Purpose**: Mental health service delivery and crisis intervention
- **Responsibilities**:
  - Patient mental health assessments
  - Therapy session scheduling
  - Crisis hotline integration
  - Medication management for psychiatric conditions
- **Data Handled**: Psychiatric evaluations, therapy notes, medication records
- **Security**: Enhanced confidentiality protocols, separate database encryption

#### 4. **Pharmacy Agent**
- **Purpose**: Medication dispensing and inventory management
- **Responsibilities**:
  - Prescription validation and fulfillment
  - Drug interaction checking
  - Inventory tracking and reordering
  - Controlled substance monitoring
- **Data Handled**: Prescription records, drug inventory, patient medication history
- **Security**: Audit trails for controlled substances, pharmacist verification

#### 5. **Criminal Case Agent**
- **Purpose**: Medico-legal case management
- **Responsibilities**:
  - Forensic evidence collection
  - Chain of custody documentation
  - Law enforcement coordination
  - Court report generation
- **Data Handled**: Forensic reports, evidence logs, legal documentation
- **Security**: **Isolated database**, restricted access, tamper-proof logging

#### 6. **Waste Management Agent**
- **Purpose**: Medical waste tracking and disposal compliance
- **Responsibilities**:
  - Hazardous waste categorization
  - Disposal scheduling and tracking
  - Regulatory compliance monitoring
  - Environmental impact reporting
- **Data Handled**: Waste manifests, disposal records, compliance certificates
- **Security**: Audit logs, regulatory authority access

---

### Backend 2: Reporting & Research (`backend_reporting/`)

**Purpose**: Data aggregation, analytics, and research coordination

**Technology Stack**:
- FastAPI (Python 3.10+)
- MongoDB (Document-based reporting)
- Apache Kafka (Event streaming)
- Celery (Async task processing)

**Department Agents**:

#### 1. **Cardiology Agent**
- **Reporting Duties**: Cardiac disease prevalence, intervention outcomes, mortality rates
- **Aggregation Logic**: Quarterly aggregation of cardiac procedures, risk factor analysis
- **Decision Authority**: Recommend cardiac care protocols, equipment procurement
- **Inter-Agent Communication**: Coordinates with NCD Agent, NIH Agent

#### 2. **Maternal Health Agent (OBGYN)**
- **Reporting Duties**: Maternal mortality ratio, delivery outcomes, prenatal care coverage
- **Aggregation Logic**: Monthly maternal health indicators, high-risk case analysis
- **Decision Authority**: Maternal care policy recommendations
- **Inter-Agent Communication**: Feeds data to Hospital Central Agent, NIH Agent

#### 3. **Infectious Diseases Agent**
- **Reporting Duties**: Disease outbreak tracking, vaccination coverage, epidemic response
- **Aggregation Logic**: Real-time disease surveillance, geographic clustering analysis
- **Decision Authority**: Outbreak alerts, quarantine recommendations
- **Inter-Agent Communication**: Direct line to NIH Agent, WHO reporting pipeline

#### 4. **Nutrition Agent**
- **Reporting Duties**: Malnutrition rates, dietary intervention outcomes, food security metrics
- **Aggregation Logic**: Quarterly nutrition surveys, demographic analysis
- **Decision Authority**: Nutrition program recommendations
- **Inter-Agent Communication**: Coordinates with Maternal Health, Pediatrics

#### 5. **Mental Health Agent**
- **Reporting Duties**: Mental health service utilization, suicide rates, treatment outcomes
- **Aggregation Logic**: De-identified mental health statistics, trend analysis
- **Decision Authority**: Mental health resource allocation recommendations
- **Inter-Agent Communication**: Feeds anonymized data to NIH Agent

#### 6. **NCD Agent** (Non-Communicable Diseases)
- **Reporting Duties**: Diabetes, hypertension, cancer prevalence and management
- **Aggregation Logic**: Chronic disease burden analysis, treatment adherence tracking
- **Decision Authority**: NCD prevention program recommendations
- **Inter-Agent Communication**: Coordinates with Cardiology, Endocrinology, Oncology

#### 7. **Endocrinology Agent**
- **Reporting Duties**: Diabetes management, thyroid disorders, hormonal therapies
- **Aggregation Logic**: Endocrine disease prevalence, treatment outcome analysis
- **Decision Authority**: Endocrine care protocol recommendations
- **Inter-Agent Communication**: Feeds data to NCD Agent, Hospital Central Agent

#### 8. **Oncology Agent**
- **Reporting Duties**: Cancer incidence, treatment modalities, survival rates
- **Aggregation Logic**: Cancer registry maintenance, staging and outcome analysis
- **Decision Authority**: Cancer care resource allocation recommendations
- **Inter-Agent Communication**: Coordinates with NIH Agent, R&D Agent for clinical trials

---

**Orchestrator Agents**:

#### 1. **Hospital Central Agent**
- **Purpose**: Hospital-level data aggregation and coordination
- **Responsibilities**:
  - Aggregate reports from all department agents within a hospital
  - Quality assurance on submitted data
  - Hospital-level performance dashboards
  - Coordination with NIH Agent for national reporting
- **Decision Authority**: Hospital operational recommendations, resource requests
- **Communication**: Receives from all department agents, sends to NIH Agent

#### 2. **NIH Agent** (National Institutes of Health)
- **Purpose**: National-level health data aggregation and policy coordination
- **Responsibilities**:
  - Aggregate reports from all Hospital Central Agents nationwide
  - National health statistics compilation
  - Policy recommendation generation
  - WHO report preparation
- **Decision Authority**: National health policy influence, research funding allocation
- **Communication**: Receives from Hospital Central Agents, coordinates with R&D Agent

#### 3. **R&D Agent** (Research & Development)
- **Purpose**: Research coordination and clinical trial management
- **Responsibilities**:
  - Clinical trial protocol management
  - Research data aggregation from universities
  - Grant proposal coordination
  - Innovation pipeline tracking
- **Decision Authority**: Research priority recommendations, university collaboration approval
- **Communication**: Coordinates with NIH Agent, University Focal Persons

---

## 🤖 Agent Ecosystem

### Agent Communication Flow

```
Department Agents → Hospital Central Agent → NIH Agent → WHO/Policy Makers
                                               ↓
                                          R&D Agent ← Universities
```

### Agent Interaction Protocols

1. **Data Submission**: Department agents submit quarterly reports to Hospital Central Agent
2. **Validation**: Hospital Central Agent validates data completeness and quality
3. **Aggregation**: NIH Agent aggregates national-level statistics
4. **Research Coordination**: R&D Agent identifies research opportunities from aggregated data
5. **Policy Feedback**: NIH Agent provides policy recommendations based on insights

For detailed agent specifications, see [docs/agent_roles.md](docs/agent_roles.md).

---

## 🌐 MCP Servers

### 1. **Core Agents MCP** (`core_agents_mcp/`)

**Purpose**: Coordination for operational healthcare agents (Backend 1)

**Timeout**: 30 seconds (real-time operations)

**Functions**:
- `dispatch_emergency()`: Trigger emergency response workflow
- `update_patient_status()`: Real-time patient status updates
- `coordinate_handoff()`: Inter-department patient handoff
- `check_resource_availability()`: Bed/equipment availability queries

**Used By**: Tracking Agent, Maternal Health Agent, Mental Health Agent, Pharmacy Agent

---

### 2. **NIH MCP** (`nih_mcp/`)

**Purpose**: National-level data aggregation and policy coordination

**Timeout**: 120 seconds (complex aggregations)

**Functions**:
- `aggregate_national_data()`: Compile national health statistics
- `generate_who_report()`: Create WHO-compliant reports
- `publish_health_bulletin()`: Disseminate national health updates
- `coordinate_outbreak_response()`: Multi-hospital outbreak coordination

**Used By**: NIH Agent, Hospital Central Agents

---

### 3. **Orchestrator MCP** (`orchestrator_mcp/`)

**Purpose**: High-level workflow orchestration across all agents

**Timeout**: 180 seconds (multi-phase workflows)

**Functions**:
- `initiate_quarterly_workflow()`: Start 9-phase quarterly reporting
- `coordinate_department_agents()`: Synchronize department agent activities
- `escalate_critical_issue()`: Escalate urgent issues to appropriate authorities
- `generate_executive_summary()`: Create leadership dashboards

**Used By**: Hospital Central Agent, NIH Agent, R&D Agent

---

### 4. **Report Generation MCP** (`report_generation_mcp/`)

**Purpose**: Automated report creation and formatting

**Timeout**: 60 seconds (document generation)

**Functions**:
- `generate_pdf_report()`: Create formatted PDF reports
- `create_data_visualization()`: Generate charts and graphs
- `compile_quarterly_report()`: Assemble multi-section reports
- `export_to_excel()`: Data export for further analysis

**Used By**: All department agents, Hospital Central Agent, NIH Agent

---

### 5. **R&D MCP** (`rnd_mcp/`)

**Purpose**: Research coordination and clinical trial management

**Timeout**: 90 seconds (research queries)

**Functions**:
- `register_clinical_trial()`: Register new research studies
- `match_patients_to_trials()`: Identify eligible trial participants
- `aggregate_research_data()`: Compile research findings
- `coordinate_university_collaboration()`: Manage university partnerships

**Used By**: R&D Agent, University Focal Persons, NIH Agent

---

## 👥 User Roles & Permissions

### 1. **Patient**

**Access Scope**: Personal health records only

**Data Visibility**:
- Own medical history
- Appointment schedules
- Prescriptions and lab results
- Billing information

**Actions Allowed**:
- Book appointments
- View test results
- Request prescription refills
- Update contact information

---

### 2. **Doctor**

**Access Scope**: Assigned patients within their department

**Data Visibility**:
- Patient medical records (assigned patients)
- Department-wide statistics
- Referral information
- Lab and imaging results

**Actions Allowed**:
- Create/update patient records
- Order tests and procedures
- Prescribe medications
- Generate medical certificates
- Refer patients to specialists

---

### 3. **Nurse**

**Access Scope**: Patients in assigned ward/unit

**Data Visibility**:
- Patient vitals and care plans
- Medication schedules
- Nursing notes
- Ward capacity information

**Actions Allowed**:
- Record patient vitals
- Administer medications (with verification)
- Update nursing notes
- Coordinate patient transfers

---

### 4. **Hospital Admin**

**Access Scope**: Hospital-wide operational data (de-identified)

**Data Visibility**:
- Hospital performance metrics
- Resource utilization statistics
- Financial reports
- Staffing information

**Actions Allowed**:
- Manage hospital configurations
- Generate operational reports
- Coordinate with department heads
- Submit reports to NIH

---

### 5. **NIH Official**

**Access Scope**: National-level aggregated data (fully de-identified)

**Data Visibility**:
- National health statistics
- Hospital performance comparisons
- Disease prevalence trends
- Resource allocation data

**Actions Allowed**:
- Access all hospital reports
- Generate national health bulletins
- Coordinate outbreak responses
- Approve research funding

---

### 6. **Researcher**

**Access Scope**: Anonymized research datasets (IRB-approved)

**Data Visibility**:
- De-identified patient cohorts
- Clinical trial data
- Epidemiological statistics
- Research publications

**Actions Allowed**:
- Request research datasets
- Register clinical trials
- Publish research findings
- Collaborate with universities

---

### 7. **University Focal Person**

**Access Scope**: University-affiliated research projects

**Data Visibility**:
- University research portfolio
- Clinical trial enrollments
- Grant applications
- Collaboration opportunities

**Actions Allowed**:
- Submit grant proposals
- Coordinate clinical trials
- Access research datasets (approved)
- Collaborate with R&D Agent

---

### 8. **System Admin**

**Access Scope**: Full system access (with audit logging)

**Data Visibility**:
- All system configurations
- User access logs
- System performance metrics
- Security audit trails

**Actions Allowed**:
- Manage user accounts
- Configure system settings
- Monitor system health
- Investigate security incidents

---

## 🔁 Workflows

### 9-Phase Quarterly National Workflow

**Phase 1: Data Collection** (Days 1-15)
- Department agents collect data from hospital systems
- Automated data validation and quality checks
- Missing data alerts to department heads

**Phase 2: Department-Level Aggregation** (Days 16-25)
- Department agents compile quarterly reports
- Statistical analysis and trend identification
- Department-specific recommendations

**Phase 3: Hospital-Level Review** (Days 26-35)
- Hospital Central Agent aggregates department reports
- Quality assurance and data reconciliation
- Hospital administrator review and approval

**Phase 4: Hospital Submission** (Days 36-45)
- Hospitals submit reports to NIH Agent
- Automated compliance checking
- Resubmission requests for incomplete data

**Phase 5: National Aggregation** (Days 46-60)
- NIH Agent compiles national statistics
- Cross-hospital comparisons and benchmarking
- Identification of national health trends

**Phase 6: Research Coordination** (Days 61-70)
- R&D Agent identifies research opportunities
- Coordination with universities for grant proposals
- Clinical trial planning based on identified needs

**Phase 7: Policy Recommendation** (Days 71-80)
- NIH Agent generates policy recommendations
- Executive summaries for health ministry
- Resource allocation proposals

**Phase 8: WHO Report Generation** (Days 81-85)
- Automated WHO-compliant report creation
- International health regulation compliance
- Submission to WHO regional office

**Phase 9: Feedback & Planning** (Days 86-90)
- Dissemination of national health bulletin
- Feedback to hospitals on performance
- Planning for next quarter's priorities

---

### Emergency Handoff Workflow

**Trigger**: Critical patient requiring specialized care

1. **Emergency Detection**: Tracking Agent identifies critical condition
2. **Specialist Alert**: Automated notification to on-call specialist
3. **Resource Check**: Verify availability of required resources (ICU bed, equipment)
4. **Patient Transfer**: Coordinate ambulance/internal transfer
5. **Handoff Protocol**: Structured communication between care teams
6. **Documentation**: Automated handoff documentation and audit trail

**Timeout**: 15 minutes maximum for critical cases

---

### Research Coordination Workflow

**Trigger**: New research proposal or clinical trial registration

1. **Proposal Submission**: University Focal Person submits research proposal
2. **IRB Review**: Automated routing to Institutional Review Board
3. **Data Access Request**: Researcher requests specific datasets
4. **De-identification**: Automated PII redaction and anonymization
5. **Dataset Provision**: Secure transfer of approved datasets
6. **Ongoing Monitoring**: R&D Agent monitors research progress
7. **Publication Support**: Assistance with research dissemination

**Timeline**: 30-60 days for approval process

For detailed workflow specifications, see [docs/workflows.md](docs/workflows.md).

---

## 🔐 Security & Compliance

### PII Redaction

**Implementation**: `shared/pii_redaction.py`

**Protected Fields**:
- Patient names
- CNIC (National ID numbers)
- Contact information (phone, email, address)
- Biometric data
- Photographs

**Redaction Levels**:
1. **Level 1 (Internal)**: Partial redaction (last 4 digits visible)
2. **Level 2 (Reporting)**: Full redaction with pseudonymization
3. **Level 3 (Research)**: Complete anonymization with k-anonymity guarantee

---

### CNIC Verification

**Purpose**: Prevent duplicate patient records and ensure identity accuracy

**Process**:
1. CNIC entered during patient registration
2. Checksum validation (Luhn algorithm)
3. Cross-reference with national identity database (where available)
4. Duplicate detection across hospital network
5. Flagging of suspicious patterns (multiple registrations)

**Security**: CNIC stored with AES-256 encryption, access logged

---

### Medico-Legal Isolation

**Purpose**: Protect forensic evidence integrity and patient confidentiality

**Implementation**:
- **Separate Database**: Criminal Case Agent uses isolated database
- **Access Control**: Restricted to authorized forensic personnel and law enforcement
- **Audit Logging**: All access logged with timestamp, user, and purpose
- **Chain of Custody**: Cryptographic signatures on all evidence entries
- **Data Retention**: Compliance with legal retention requirements

---

### Audit Logging

**Scope**: All user actions, data access, and system events

**Log Fields**:
- Timestamp (UTC)
- User ID and role
- Action performed
- Data accessed (record IDs, not content)
- IP address and device information
- Success/failure status

**Retention**: 7 years (regulatory compliance)

**Storage**: Immutable append-only log storage

---

### WHO & NIH Compliance

**Standards Implemented**:
- **ICD-10**: International Classification of Diseases coding
- **HL7 FHIR**: Health data interoperability standards
- **WHO IHR**: International Health Regulations compliance
- **HIPAA**: Health Insurance Portability and Accountability Act (where applicable)
- **GDPR**: General Data Protection Regulation (for international collaborations)

**Reporting Formats**:
- WHO DHIS2-compatible data exports
- NIH-specified quarterly report templates
- Custom research data formats (IRB-approved)

For comprehensive security documentation, see [docs/security_compliance.md](docs/security_compliance.md).

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.10 or higher
- Node.js 18+ and npm
- PostgreSQL 14+
- MongoDB 6+
- Redis 7+
- Docker & Docker Compose (optional)

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/your-org/healthlink360.git
cd HealthLink360

# Copy environment variables
cp .env.example .env

# Edit .env with your configurations
nano .env

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend Core: http://localhost:8000
# Backend Reporting: http://localhost:8001
```

### Manual Installation

#### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up databases
# PostgreSQL for backend_core
createdb healthlink_core

# MongoDB for backend_reporting
# (Ensure MongoDB is running)

# Run database migrations
cd backend_core
alembic upgrade head

cd ../backend_reporting
python database/init_db.py

# Start backends
cd ../scripts
./start_backend_core.sh
./start_backend_reporting.sh
```

#### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### 3. MCP Servers Setup

```bash
# Each MCP server runs independently
cd mcp_servers/core_agents_mcp
python agents_mcp.py &

cd ../nih_mcp
python nih_mcp.py &

# Repeat for other MCP servers
```

### Configuration

Edit `.env` file with your specific configurations:

```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=healthlink_core
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password

MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=healthlink_reporting

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Security
SECRET_KEY=your_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here

# MCP Servers
CORE_AGENTS_MCP_URL=http://localhost:9000
NIH_MCP_URL=http://localhost:9001
ORCHESTRATOR_MCP_URL=http://localhost:9002
REPORT_GEN_MCP_URL=http://localhost:9003
RND_MCP_URL=http://localhost:9004

# External Services
NIH_API_ENDPOINT=https://nih.gov.pk/api
WHO_REPORTING_ENDPOINT=https://who.int/reporting
```

---

## 📚 API Documentation

API documentation is available at:

- **Backend Core**: `http://localhost:8000/docs` (Swagger UI)
- **Backend Reporting**: `http://localhost:8001/docs` (Swagger UI)

For detailed endpoint specifications, see [docs/api_endpoints.md](docs/api_endpoints.md).

---

## 🤝 Contributing

We welcome contributions from the healthcare and technology communities!

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- **Python**: PEP 8 compliance, type hints required
- **JavaScript**: ESLint with Airbnb config
- **Documentation**: All new features must include documentation
- **Testing**: Minimum 80% code coverage for new code

---

## 📞 Support & Contact

- **Documentation**: [docs/](docs/)
- **Issue Tracker**: GitHub Issues
- **Email**: support@healthlink360.org
- **Slack**: [Join our community](https://healthlink360.slack.com)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- National Institutes of Health (NIH) for policy guidance
- World Health Organization (WHO) for international standards
- Healthcare professionals and researchers who provided domain expertise
- Open-source community for foundational technologies

---

**HealthLink360** - *Connecting Care, Empowering Health*
