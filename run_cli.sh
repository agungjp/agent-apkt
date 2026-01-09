#!/bin/bash

cd "/Users/agungperkasa/Documents/02 Dev/sandbox/ods-apkt"

# Run apkt-agent with input
(echo 2; echo 202501; echo y; echo y) | /opt/homebrew/bin/apkt-agent

# Wait a moment for everything to finish
sleep 5

# Show results
echo ""
echo "========== RUN COMPLETE =========="
ls -ltr workspace/runs/ | head -5
