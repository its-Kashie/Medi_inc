#!/bin/bash

# HealthLink360 Backend Core Startup Script

# Set PYTHONPATH to include project root
export PYTHONPATH="/home/kyim/Medi_inc:$PYTHONPATH"

# Activate virtual environment
source /home/kyim/Medi_inc/venv/bin/activate

# Navigate to project root
cd /home/kyim/Medi_inc

# Start Backend Core
echo "🚀 Starting HealthLink360 Backend Core..."
echo "📍 API will be available at: http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo ""

python backend_core/backend.py
