#!/bin/bash

# Short Report Rebuttal Assistant - Quick Start Script

echo "🚀 Starting Short Report Rebuttal Assistant..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from sample.env..."
    cp sample.env .env
    echo "✅ Created .env file. Please edit it if needed."
fi

# Check if Ollama is running
echo "🔍 Checking Ollama connection..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama is not running. Please start Ollama first:"
    echo "   ollama serve"
    exit 1
fi
echo "✅ Ollama is running"

# Check if models are available
echo "🔍 Checking Ollama models..."
MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
if [[ ! "$MODELS" == *"llama3.1"* ]] && [[ ! "$MODELS" == *"llama3"* ]]; then
    echo "⚠️  LLM model (llama3.1:8b) not found. Downloading..."
    ollama pull llama3.1:8b
fi
if [[ ! "$MODELS" == *"nomic-embed-text"* ]]; then
    echo "⚠️  Embedding model (nomic-embed-text) not found. Downloading..."
    ollama pull nomic-embed-text
fi
echo "✅ Required models are available"

# Check if internal documents are indexed
if [ ! -d "storage/chroma" ] || [ -z "$(ls -A storage/chroma 2>/dev/null)" ]; then
    echo "⚠️  Internal documents not indexed. Running index script..."
    python -m app.index_internal
    echo "✅ Internal documents indexed"
else
    echo "✅ Internal documents already indexed"
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    if [ ! -z "$FASTAPI_PID" ]; then
        kill $FASTAPI_PID 2>/dev/null
        echo "   ✅ FastAPI server stopped"
    fi
    if [ ! -z "$STREAMLIT_PID" ]; then
        kill $STREAMLIT_PID 2>/dev/null
        echo "   ✅ Streamlit UI stopped"
    fi
    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup SIGINT SIGTERM

# Start FastAPI server in background
echo ""
echo "📡 Starting FastAPI server..."
echo "   API will be available at http://localhost:8000"
echo "   API docs at http://localhost:8000/docs"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &
FASTAPI_PID=$!

# Wait a bit for FastAPI to start
sleep 3

# Check if FastAPI started successfully
if ! kill -0 $FASTAPI_PID 2>/dev/null; then
    echo "❌ Failed to start FastAPI server. Check /tmp/fastapi.log for details."
    exit 1
fi

echo "✅ FastAPI server started (PID: $FASTAPI_PID)"

# Start Streamlit UI in background
echo ""
echo "🎨 Starting Streamlit UI..."
echo "   UI will be available at http://localhost:8501"
streamlit run streamlit_app.py --server.headless true > /tmp/streamlit.log 2>&1 &
STREAMLIT_PID=$!

# Wait a bit for Streamlit to start
sleep 3

# Check if Streamlit started successfully
if ! kill -0 $STREAMLIT_PID 2>/dev/null; then
    echo "❌ Failed to start Streamlit UI. Check /tmp/streamlit.log for details."
    kill $FASTAPI_PID 2>/dev/null
    exit 1
fi

echo "✅ Streamlit UI started (PID: $STREAMLIT_PID)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 All services are running!"
echo ""
echo "📍 Access points:"
echo "   • Streamlit UI:  http://localhost:8501"
echo "   • FastAPI API:   http://localhost:8000"
echo "   • API Docs:     http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   • FastAPI:   tail -f /tmp/fastapi.log"
echo "   • Streamlit: tail -f /tmp/streamlit.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Wait a bit more for Streamlit to fully initialize
sleep 2

# Open browser automatically
echo "🌐 Opening browser..."
if command -v open >/dev/null 2>&1; then
    # macOS
    open http://localhost:8501
elif command -v xdg-open >/dev/null 2>&1; then
    # Linux
    xdg-open http://localhost:8501
elif command -v start >/dev/null 2>&1; then
    # Windows (Git Bash)
    start http://localhost:8501
else
    echo "⚠️  Could not automatically open browser. Please visit http://localhost:8501"
fi

# Wait for user interrupt
wait
