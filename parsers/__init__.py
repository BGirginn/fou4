# Parsers module initialization
from .base import BaseParser, ScanResult, Finding
from .nmap_parser import NmapParser
from .nuclei_parser import NucleiParser

__all__ = ['BaseParser', 'ScanResult', 'Finding', 'NmapParser', 'NucleiParser']
