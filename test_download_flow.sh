#!/bin/bash
# Test download flow to check for errors

cd /Users/agungperkasa/Documents/02\ Dev/sandbox/ods-apkt

# Input sequence:
# OTP code (dummy)
# Menu 2 (download)
# Period: 202601
# Browser mode: n (tampil)
# Confirm: y
# Menu: 0 (exit)

echo "Testing download flow..."
printf "123456\n2\n202601\nn\ny\n0\n" | python -m apkt_agent.cli 2>&1 | tee test_download_log.txt
