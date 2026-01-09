#!/usr/bin/env python
"""Quick test to check if download logic is working."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from apkt_agent.config import load_config
from apkt_agent.datasets.se004.multi_download import load_units_selection

# Test load config
print("=" * 60)
print("Testing Configuration")
print("=" * 60)

config = load_config()
print(f"✓ Config loaded")
print(f"  - APKT URL: {config.get('apkt.login_url')}")
print(f"  - Headless: {config.data.get('runtime', {}).get('headless', 'NOT SET')}")

# Test load units
print("\n" + "=" * 60)
print("Testing Units Loading")
print("=" * 60)

units_file = Path("credentials/units_selection.yaml")
if units_file.exists():
    units = load_units_selection(units_file)
    print(f"✓ Units loaded: {len(units)} units")
    for i, unit in enumerate(units[:3], 1):
        print(f"  {i}. {unit.get('text', 'N/A')}")
else:
    print(f"✗ Units file not found: {units_file}")

print("\n✓ Tests completed!")
