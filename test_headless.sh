#!/bin/bash

# Test script to check if headless mode prompt is displayed
cd "/Users/agungperkasa/Documents/02 Dev/sandbox/ods-apkt"

echo "Testing APKT Agent headless mode prompt..."
echo "Input sequence: n (tampil), exit with 0"
echo ""

# Run with timeout 20 seconds, send inputs
echo -e "n\n0" | timeout 20 python -m apkt_agent.cli 2>&1 | head -100
