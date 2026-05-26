#!/usr/bin/env bash
# UrivDocs — Stop everything
echo "Stopping UrivDocs..."
docker compose down --remove-orphans 2>/dev/null || true
lsof -ti tcp:8000 | xargs kill -TERM 2>/dev/null || true
lsof -ti tcp:5173 | xargs kill -TERM 2>/dev/null || true
pkill -f "ollama serve" 2>/dev/null || true
echo "✓ All stopped"
