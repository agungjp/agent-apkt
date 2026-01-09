#!/usr/bin/env python3
"""Automated CLI runner for testing."""

import subprocess
import sys

# Run apkt-agent with input
process = subprocess.Popen(
    ['apkt-agent'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# Send inputs
inputs = "2\n202501\ny\ny\n"
stdout, _ = process.communicate(input=inputs, timeout=600)

# Print output
print(stdout)
sys.exit(process.returncode)
