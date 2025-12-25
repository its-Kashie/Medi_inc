# HealthLink360 - Getting Started

## 🚀 Quick Start Guide

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+**
- **Node.js 18+** and npm
- **PostgreSQL 14+**
- **MongoDB 6+**
- **Redis 7+**

### Installation Steps

#### 1. Clone and Setup Environment

```bash
cd /home/kyim/Medi_inc
cp .env.example .env
# Edit .env with your configuration (already done for development)
```

#### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

#### 4. Start Databases (if not using Docker)

**PostgreSQL:**
```bash
# Create database
createdb healthlink_core
```

**MongoDB:**
```bash
# Start MongoDB service
sudo systemctl start mongod
```

**Redis:**
```bash
# Start Redis service
sudo systemctl start redis
```

#### 5. Initialize Database

```bash
# Create database tables
python3 -c "from backend_core.models import init_db; init_db()"
```

#### 6. Start Backend Core

```bash
cd backend_core
python3 backend.py
# Or use uvicorn directly:
# uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

Backend Core will be available at: http://localhost:8000

#### 7. Start Frontend (in a new terminal)

```bash
cd frontend
npm start
```

Frontend will be available at: http://localhost:3000

### Using Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## 📚 Project Structure

```
HealthLink360/
├── backend_core/          # Healthcare Operations Backend
│   ├── backend.py         # FastAPI application
│   ├── models/            # Database models
│   ├── routers/           # API routes
│   ├── agents/            # Operational agents
│   └── services/          # Business logic
│
├── backend_reporting/     # Analytics & Reporting Backend
│   ├── api_server.py      # FastAPI application
│   ├── agents/            # Department & orchestrator agents
│   └── workflows/         # Reporting workflows
│
├── frontend/              # React Frontend
│   ├── src/
│   │   ├── App.jsx        # Main application
│   │   ├── pages/         # Page components
│   │   └── components/    # Reusable components
│   └── public/
│
├── shared/                # Shared utilities
│   ├── config.py          # Configuration management
│   ├── logger.py          # Logging system
│   ├── pii_redaction.py   # PII protection
│   └── utils.py           # Common utilities
│
├── mcp_servers/           # MCP Server implementations
├── docs/                  # Documentation
├── data/                  # Reference data
└── logs/                  # Application logs
```

## 🔧 Development

### Backend Core API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Base URL**: http://localhost:8000/api/v1

### Backend Reporting API

- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **Base URL**: http://localhost:8001/api/v1

### Frontend

- **Development Server**: http://localhost:3000
- **Hot Reload**: Enabled by default

## 🧪 Testing

```bash
# Run backend tests
pytest backend_core/tests/
pytest backend_reporting/tests/

# Run frontend tests
cd frontend
npm test
```

## 📖 Next Steps

1. **Explore the Documentation**: Check the `docs/` folder for detailed guides
2. **Review API Endpoints**: Visit http://localhost:8000/docs
3. **Customize Configuration**: Edit `.env` for your environment
4. **Add Sample Data**: Use the admin panel to add test data
5. **Explore Features**: Navigate through the frontend pages

## 🆘 Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check MongoDB is running
sudo systemctl status mongod

# Check Redis is running
sudo systemctl status redis
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Module Import Errors

```bash
# Ensure you're in the project root
cd /home/kyim/Medi_inc

# Add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/home/kyim/Medi_inc"
```

## 📞 Support

For issues and questions:
- Check the documentation in `docs/`
- Review the README.md in the project root
- Check the logs in `logs/` directory

## 🎯 Current Status

✅ **Completed:**
- Project scaffold and structure
- Shared utilities (config, logging, PII redaction)
- Backend Core FastAPI application
- Database models (User, Patient, Medical Records, Prescriptions, Appointments)
- Frontend React application with routing
- Modern UI design system
- Home page with feature overview

🚧 **In Progress:**
- API routers and endpoints
- Agent implementations
- MCP server implementations
- Additional frontend pages

📋 **Planned:**
- Authentication system
- Patient management features
- Emergency tracking
- Reporting workflows
- WHO/NIH integration
