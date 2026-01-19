#!/bin/bash

# Stop Short Report Rebuttal Assistant services

echo "🛑 Stopping services..."

# Find and kill FastAPI (uvicorn) processes
FASTAPI_PIDS=$(ps aux | grep "uvicorn main:app" | grep -v grep | awk '{print $2}')
if [ ! -z "$FASTAPI_PIDS" ]; then
    echo "   Stopping FastAPI server..."
    echo "$FASTAPI_PIDS" | xargs kill 2>/dev/null
    echo "   ✅ FastAPI server stopped"
else
    echo "   ℹ️  FastAPI server not running"
fi

# Find and kill Streamlit processes
STREAMLIT_PIDS=$(ps aux | grep "streamlit run streamlit_app.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$STREAMLIT_PIDS" ]; then
    echo "   Stopping Streamlit UI..."
    echo "$STREAMLIT_PIDS" | xargs kill 2>/dev/null
    echo "   ✅ Streamlit UI stopped"
else
    echo "   ℹ️  Streamlit UI not running"
fi

# Also check for any Python processes running main.py or streamlit_app.py
PYTHON_PIDS=$(ps aux | grep -E "(main.py|streamlit_app.py)" | grep python | grep -v grep | awk '{print $2}')
if [ ! -z "$PYTHON_PIDS" ]; then
    echo "   Stopping remaining Python processes..."
    echo "$PYTHON_PIDS" | xargs kill 2>/dev/null
    echo "   ✅ Python processes stopped"
fi

echo ""
echo "✅ All services stopped!"
