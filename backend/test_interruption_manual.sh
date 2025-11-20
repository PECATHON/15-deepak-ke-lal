#!/bin/bash
# Manual Test Script for Interruption System
# This script demonstrates how to test interruption with curl commands

echo "======================================================================"
echo "  INTERRUPTION SYSTEM - MANUAL TEST GUIDE"
echo "======================================================================"
echo ""
echo "Prerequisites:"
echo "  1. Backend must be running: uvicorn main:app --reload"
echo "  2. Open another terminal for these commands"
echo ""
echo "======================================================================"
echo "TEST 1: Basic Interruption"
echo "======================================================================"
echo ""
echo "Step 1: Send first query (will take ~3 seconds)"
echo "Command:"
echo 'curl -X POST http://localhost:8000/chat \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"user_id": "test_user", "message": "Find flights from NYC to London"}'"'"
echo ""
echo "Step 2: IMMEDIATELY send second query (interrupts first)"
echo "Command:"
echo 'curl -X POST http://localhost:8000/chat \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"user_id": "test_user", "message": "Find hotels in Paris"}'"'"
echo ""
echo "Step 3: Check status and partial results"
echo "Command:"
echo 'curl http://localhost:8000/status/test_user'
echo ""
echo "Expected: First task interrupted, partial results preserved"
echo ""
echo "======================================================================"
echo "TEST 2: WebSocket Real-time Updates"
echo "======================================================================"
echo ""
echo "Use a WebSocket client (wscat, browser console, or Python script):"
echo ""
echo "Install wscat:"
echo "  npm install -g wscat"
echo ""
echo "Connect:"
echo "  wscat -c ws://localhost:8000/ws/test_user"
echo ""
echo "Then in another terminal, send queries:"
echo '  curl -X POST http://localhost:8000/chat \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '"'"'{"user_id": "test_user", "message": "Find flights to Tokyo"}'"'"
echo ""
echo "You'll see real-time updates in the WebSocket connection!"
echo ""
echo "======================================================================"
echo "TEST 3: Explicit Interruption"
echo "======================================================================"
echo ""
echo "Step 1: Start a query"
echo 'curl -X POST http://localhost:8000/chat \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"user_id": "test_user", "message": "Find flights to Rome"}'"'"
echo ""
echo "Step 2: Interrupt it explicitly"
echo 'curl -X POST http://localhost:8000/interrupt \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"user_id": "test_user"}'"'"
echo ""
echo "Step 3: Check status"
echo 'curl http://localhost:8000/status/test_user'
echo ""
echo "======================================================================"
