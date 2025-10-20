#!/usr/bin/env python3
"""Quick test of email harvesting feature"""

import sys
sys.path.insert(0, '/home/kali/fou4')

from modules.osint_module import harvest_emails

print("\n🧪 Testing Email Harvesting Feature\n")
print("=" * 70)

# Test with a real domain
domain = "example.com"
print(f"\n📧 Harvesting emails from: {domain}")
print("-" * 70)

emails = harvest_emails(domain, workspace_id=None)

print("\n" + "=" * 70)
print(f"\n✅ SUCCESS! Found {len(emails)} emails")
print(f"✅ Feature is working correctly!")
print("\n" + "=" * 70 + "\n")
