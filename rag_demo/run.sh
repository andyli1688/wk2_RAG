#!/bin/bash

# Short Report Rebuttal Assistant - Start Script (Frontend + Backend)

echo "🚀 Starting Short Report Rebuttal Assistant..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env exists in backend
if [ ! -f backend/.env ]; then
    echo "⚠️  backend/.env file not found. Creating from .env.example..."
    cp backend/.env.example backend/.env 2>/dev/null || cp backend/sample.env backend/.env 2>/dev/null
    echo "✅ Created backend/.env file. Please edit it if needed."
fi

# Load .env file to get LLM_PROVIDER
if [ -f backend/.env ]; then
    export $(grep -v '^#' backend/.env | xargs)
fi

# Default to openai if not specified
LLM_PROVIDER=${LLM_PROVIDER:-openai}
echo "📦 LLM Provider: $LLM_PROVIDER"

if [ "$LLM_PROVIDER" = "openai" ]; then
    # Check for OpenAI API key
    echo "🔍 Checking OpenAI configuration..."
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "❌ OPENAI_API_KEY is not set."
        echo "   Please set OPENAI_API_KEY in backend/.env or as an environment variable."
        echo "   Or switch to Ollama by setting LLM_PROVIDER=ollama"
        exit 1
    fi
    echo "✅ OpenAI API key is configured"
else
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
    echo "✅ Required Ollama models are available"
fi

# Check if internal documents are indexed
echo "🔍 Checking vector database..."
cd backend
python3 << 'PYTHON_SCRIPT'
import sys
from pathlib import Path
import chromadb
from chromadb.config import Settings

try:
    chroma_dir = Path("../storage/chroma")
    if chroma_dir.exists():
        client = chromadb.PersistentClient(
            path=str(chroma_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        try:
            collection = client.get_collection("internal_documents")
            count = collection.count()
            if count > 0:
                print(f"✅ Vector DB exists with {count} chunks")
                sys.exit(0)
            else:
                print("⚠️  Vector DB exists but is empty")
                sys.exit(1)
        except Exception:
            print("⚠️  Vector DB directory exists but collection not found")
            sys.exit(1)
    else:
        print("⚠️  Vector DB not found")
        sys.exit(1)
except Exception as e:
    print(f"⚠️  Error checking vector DB: {e}")
    sys.exit(1)
PYTHON_SCRIPT

INDEX_CHECK=$?

if [ $INDEX_CHECK -ne 0 ]; then
    echo "⚠️  Vector DB not found or empty. Indexing company_data.pdf..."
    python -m app.index_internal
    if [ $? -eq 0 ]; then
        echo "✅ Internal documents indexed successfully"
    else
        echo "❌ Failed to index documents"
        exit 1
    fi
fi
cd ..

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "   ✅ Backend server stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "   ✅ Frontend server stopped"
    fi
    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup SIGINT SIGTERM

# Start backend server
echo ""
echo "📡 Starting backend server..."
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Failed to start backend server. Check /tmp/backend.log for details."
    exit 1
fi

echo "✅ Backend server started (PID: $BACKEND_PID)"

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo ""
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Start frontend server
echo ""
echo "🎨 Starting frontend server..."
cd frontend
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 5

if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Failed to start frontend server. Check /tmp/frontend.log for details."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Frontend server started (PID: $FRONTEND_PID)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 All services are running!"
echo ""
echo "📍 Access points:"
echo "   • Frontend:     http://localhost:3000"
echo "   • Backend API:  http://localhost:8000"
echo "   • API Docs:     http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   • Backend:   tail -f /tmp/backend.log"
echo "   • Frontend:  tail -f /tmp/frontend.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Wait a bit more for services to fully initialize
sleep 2

# Open browser automatically
echo "🌐 Opening browser..."
if command -v open >/dev/null 2>&1; then
    open http://localhost:3000
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:3000
elif command -v start >/dev/null 2>&1; then
    start http://localhost:3000
else
    echo "⚠️  Could not automatically open browser. Please visit http://localhost:3000"
fi

# Wait for user interrupt
wait
