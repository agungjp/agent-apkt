#!/usr/bin/env python3
"""Auto run CLI untuk test."""

import subprocess
import time
import sys

# Run apkt-agent dengan input otomatis
process = subprocess.Popen(
    ['apkt-agent'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Send inputs dengan jeda waktu
inputs = ['2', '202501', 'y', 'y']
for inp in inputs:
    print(f"Sending: {inp}", file=sys.stderr)
    process.stdin.write(inp + '\n')
    process.stdin.flush()
    time.sleep(2)

# Tunggu selesai
stdout, _ = process.communicate(timeout=600)
print(stdout)
