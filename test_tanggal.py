#!/usr/bin/env python3
"""Test parsing improvements untuk tanggal_cetak."""

import sys
sys.path.insert(0, '/Users/agungperkasa/Documents/02 Dev/sandbox/ods-apkt/src')

from apkt_agent.datasets.se004.schema import parse_tanggal_to_ddmmyyyy

# Test cases
test_cases = [
    ("08/01/2026 ", "08/01/2026"),  # With trailing space
    (" 08/01/2026", "08/01/2026"),  # With leading space
    ("  08/01/2026  ", "08/01/2026"),  # With multiple spaces
    ("08 Januari 2026", "08/01/2026"),  # Indonesian format
    ("Selasa, 08 Januari 2026", "08/01/2026"),  # With day name
    ("2026-01-08", "08/01/2026"),  # ISO format
    ("08 Januari 2026 ", "08/01/2026"),  # Indonesian with space
]

print("=" * 60)
print("Testing tanggal_cetak parsing improvements")
print("=" * 60)

all_passed = True
for input_val, expected in test_cases:
    result = parse_tanggal_to_ddmmyyyy(input_val)
    status = "✓" if result == expected else "✗"
    
    if result != expected:
        all_passed = False
    
    print(f"{status} Input: {repr(input_val):30} => {result:12} (expected: {expected})")

print("=" * 60)
if all_passed:
    print("✅ ALL TESTS PASSED!")
else:
    print("❌ SOME TESTS FAILED!")
print("=" * 60)
