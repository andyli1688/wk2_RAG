#!/bin/bash

# Cleanup script: Remove files not related to rebuttal assistant

echo "🧹 Cleaning up directory, keeping only rebuttal-related files..."

cd "$(dirname "$0")"

# Files to keep (rebuttal-related)
KEEP_FILES=(
    "app/"
    "main.py"
    "streamlit_app.py"
    "requirements_rebuttal.txt"
    "sample.env"
    ".env"
    "run_rebuttal.sh"
    "start_ui.sh"
    "stop_services.sh"
    "README_REBUTTAL.md"
    "QUICKSTART_REBUTTAL.md"
    "HOW_TO_RUN.md"
    "RESTART_SERVER.md"
    "company/"
    "storage/"
)

# Files/directories to remove (old/unrelated)
REMOVE_ITEMS=(
    "app.py"
    "document_process.py"
    "embedding.py"
    "faiss_demo.py"
    "generation.py"
    "requirements.txt"
    "run.sh"
    "setup.sh"
    "QUICKSTART.md"
    "README_STREAMLIT.md"
    "SETUP_GUIDE.md"
    "faiss_out/"
    "__pycache__/"
    "cleanup.sh"  # Remove this script after running
)

# Ask for confirmation
echo ""
echo "Files/directories to be REMOVED:"
for item in "${REMOVE_ITEMS[@]}"; do
    if [ -e "$item" ]; then
        echo "  - $item"
    fi
done

echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled"
    exit 1
fi

# Remove files/directories
echo ""
echo "🗑️  Removing old files..."
for item in "${REMOVE_ITEMS[@]}"; do
    if [ -e "$item" ]; then
        echo "   Removing: $item"
        rm -rf "$item"
    fi
done

# Clean up uploads directory (keep directory but remove old files)
if [ -d "uploads" ]; then
    echo "   Cleaning uploads/ directory..."
    # Keep the directory but you can manually clean it if needed
    # rm -rf uploads/*
fi

# Clean up __pycache__ directories
echo "   Cleaning __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Remaining files:"
ls -1 | head -20
