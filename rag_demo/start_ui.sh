#!/bin/bash

# Start Streamlit UI
cd "$(dirname "$0")"
echo "🚀 Starting Streamlit UI..."
echo "   UI will be available at http://localhost:8501"
echo ""
streamlit run streamlit_app.py
