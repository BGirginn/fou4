"""
Kali Tool - Penetration Testing Toolkit

A comprehensive penetration testing toolkit with modules for:
- Wi-Fi Attacks
- Network Analysis
- Web Exploitation
- OSINT Tools
- Reporting
- Workspace Management
"""

__version__ = "1.0.0"
__author__ = "Kali Tool Team"

# Re-export main entry for integration tests that import fou4 and expect 'main'
try:
	from .fou4 import main, setup_argparse  # type: ignore
except Exception:
	# In some contexts, importing main may import heavy modules; ignore import errors here.
	pass

