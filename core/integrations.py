"""
External API integrations for CyberToolkit.
Provides interfaces to Shodan, VirusTotal, CVE databases, and more.
"""

import json
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None


@dataclass
class APIResponse:
    """Standardized API response container."""
    success: bool
    data: Any = None
    error: str = ""
    cached: bool = False
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class BaseIntegration:
    """Base class for API integrations."""
    
    name: str = "base"
    base_url: str = ""
    rate_limit: float = 1.0  # Seconds between requests
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._last_request = 0.0
        self._cache: Dict[str, APIResponse] = {}
    
    def _rate_limit_wait(self):
        """Wait for rate limit if needed."""
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request = time.time()
    
    def _get(self, endpoint: str, params: Optional[dict] = None) -> APIResponse:
        """Make GET request to API."""
        if requests is None:
            return APIResponse(success=False, error="requests library not installed")
        
        self._rate_limit_wait()
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            return APIResponse(
                success=True,
                data=response.json()
            )
        except requests.RequestException as e:
            return APIResponse(success=False, error=str(e))
    
    def _get_headers(self) -> dict:
        """Get request headers. Override in subclasses."""
        return {}
    
    def _cache_key(self, *args) -> str:
        """Generate cache key."""
        return f"{self.name}:{':'.join(str(a) for a in args)}"
    
    def _get_cached(self, key: str) -> Optional[APIResponse]:
        """Get cached response."""
        return self._cache.get(key)
    
    def _set_cached(self, key: str, response: APIResponse):
        """Cache response."""
        response.cached = True
        self._cache[key] = response


class ShodanIntegration(BaseIntegration):
    """Shodan API integration for host intelligence."""
    
    name = "shodan"
    base_url = "https://api.shodan.io"
    rate_limit = 1.0
    
    def _get_headers(self) -> dict:
        return {}
    
    def _get(self, endpoint: str, params: Optional[dict] = None) -> APIResponse:
        """Override to add API key to params."""
        if not params:
            params = {}
        params["key"] = self.api_key
        return super()._get(endpoint, params)
    
    def host_info(self, ip: str) -> APIResponse:
        """
        Get detailed information about a host.
        
        Args:
            ip: IP address to lookup
        
        Returns:
            APIResponse with host data
        """
        if not self.api_key:
            return APIResponse(success=False, error="Shodan API key not configured")
        
        cache_key = self._cache_key("host", ip)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        response = self._get(f"/shodan/host/{ip}")
        
        if response.success:
            self._set_cached(cache_key, response)
        
        return response
    
    def search(self, query: str, page: int = 1) -> APIResponse:
        """
        Search Shodan for hosts.
        
        Args:
            query: Shodan search query
            page: Results page
        
        Returns:
            APIResponse with search results
        """
        if not self.api_key:
            return APIResponse(success=False, error="Shodan API key not configured")
        
        return self._get("/shodan/host/search", params={"query": query, "page": page})
    
    def ports(self, ip: str) -> APIResponse:
        """Get open ports for an IP."""
        result = self.host_info(ip)
        if result.success and result.data:
            ports = result.data.get("ports", [])
            return APIResponse(success=True, data=ports)
        return result
    
    def vulnerabilities(self, ip: str) -> APIResponse:
        """Get vulnerabilities for an IP."""
        result = self.host_info(ip)
        if result.success and result.data:
            vulns = result.data.get("vulns", [])
            return APIResponse(success=True, data=vulns)
        return result


class VirusTotalIntegration(BaseIntegration):
    """VirusTotal API integration for threat intelligence."""
    
    name = "virustotal"
    base_url = "https://www.virustotal.com/api/v3"
    rate_limit = 15.0  # Free tier: 4 lookups/minute
    
    def _get_headers(self) -> dict:
        return {"x-apikey": self.api_key}
    
    def scan_url(self, url: str) -> APIResponse:
        """
        Get URL scan results.
        
        Args:
            url: URL to check
        
        Returns:
            APIResponse with scan data
        """
        if not self.api_key:
            return APIResponse(success=False, error="VirusTotal API key not configured")
        
        import base64
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        
        return self._get(f"/urls/{url_id}")
    
    def scan_ip(self, ip: str) -> APIResponse:
        """
        Get IP reputation.
        
        Args:
            ip: IP address to check
        
        Returns:
            APIResponse with IP data
        """
        if not self.api_key:
            return APIResponse(success=False, error="VirusTotal API key not configured")
        
        cache_key = self._cache_key("ip", ip)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        response = self._get(f"/ip_addresses/{ip}")
        
        if response.success:
            self._set_cached(cache_key, response)
        
        return response
    
    def scan_domain(self, domain: str) -> APIResponse:
        """
        Get domain reputation.
        
        Args:
            domain: Domain to check
        
        Returns:
            APIResponse with domain data
        """
        if not self.api_key:
            return APIResponse(success=False, error="VirusTotal API key not configured")
        
        return self._get(f"/domains/{domain}")


class CVELookup(BaseIntegration):
    """CVE/NVD database lookup."""
    
    name = "nvd"
    base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    rate_limit = 0.6  # NVD rate limit: 5 requests per 30 seconds
    
    def get_cve(self, cve_id: str) -> APIResponse:
        """
        Get CVE details from NVD.
        
        Args:
            cve_id: CVE identifier (e.g., CVE-2021-44228)
        
        Returns:
            APIResponse with CVE data
        """
        cache_key = self._cache_key("cve", cve_id)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        response = self._get("", params={"cveId": cve_id})
        
        if response.success and response.data:
            vulnerabilities = response.data.get("vulnerabilities", [])
            if vulnerabilities:
                cve_data = vulnerabilities[0].get("cve", {})
                
                # Extract key information
                parsed = {
                    "id": cve_id,
                    "description": "",
                    "cvss_v3": None,
                    "severity": "UNKNOWN",
                    "references": [],
                    "published": "",
                    "modified": ""
                }
                
                # Get description
                descriptions = cve_data.get("descriptions", [])
                for desc in descriptions:
                    if desc.get("lang") == "en":
                        parsed["description"] = desc.get("value", "")
                        break
                
                # Get CVSS
                metrics = cve_data.get("metrics", {})
                cvss_v3 = metrics.get("cvssMetricV31", metrics.get("cvssMetricV30", []))
                if cvss_v3:
                    cvss_data = cvss_v3[0].get("cvssData", {})
                    parsed["cvss_v3"] = cvss_data.get("baseScore")
                    parsed["severity"] = cvss_data.get("baseSeverity", "UNKNOWN")
                
                # Get references
                refs = cve_data.get("references", [])
                parsed["references"] = [r.get("url") for r in refs if r.get("url")]
                
                # Get dates
                parsed["published"] = cve_data.get("published", "")
                parsed["modified"] = cve_data.get("lastModified", "")
                
                response = APIResponse(success=True, data=parsed)
                self._set_cached(cache_key, response)
                return response
        
        return APIResponse(success=False, error=f"CVE not found: {cve_id}")
    
    def search(self, keyword: str, results_per_page: int = 10) -> APIResponse:
        """
        Search CVEs by keyword.
        
        Args:
            keyword: Search keyword
            results_per_page: Number of results
        
        Returns:
            APIResponse with search results
        """
        return self._get("", params={
            "keywordSearch": keyword,
            "resultsPerPage": results_per_page
        })


class ExploitDBIntegration(BaseIntegration):
    """Exploit-DB search integration."""
    
    name = "exploitdb"
    base_url = "https://exploit-db.com/search"
    
    def search_by_cve(self, cve_id: str) -> APIResponse:
        """
        Search for exploits by CVE ID.
        Note: This uses the local searchsploit if available.
        
        Args:
            cve_id: CVE identifier
        
        Returns:
            APIResponse with exploit data
        """
        import subprocess
        import shutil
        
        if not shutil.which("searchsploit"):
            return APIResponse(success=False, error="searchsploit not installed")
        
        try:
            result = subprocess.run(
                ["searchsploit", "--cve", cve_id, "-j"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                exploits = data.get("RESULTS_EXPLOIT", [])
                return APIResponse(success=True, data=exploits)
            else:
                return APIResponse(success=False, error=result.stderr)
                
        except subprocess.TimeoutExpired:
            return APIResponse(success=False, error="Search timed out")
        except json.JSONDecodeError:
            return APIResponse(success=False, error="Invalid JSON response")
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def search(self, query: str) -> APIResponse:
        """
        Search for exploits by keyword.
        
        Args:
            query: Search query
        
        Returns:
            APIResponse with exploit data
        """
        import subprocess
        import shutil
        
        if not shutil.which("searchsploit"):
            return APIResponse(success=False, error="searchsploit not installed")
        
        try:
            result = subprocess.run(
                ["searchsploit", query, "-j"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                exploits = data.get("RESULTS_EXPLOIT", [])
                return APIResponse(success=True, data=exploits)
            else:
                return APIResponse(success=False, error=result.stderr)
                
        except Exception as e:
            return APIResponse(success=False, error=str(e))


class IntegrationManager:
    """Manages all API integrations."""
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize integrations with API keys.
        
        Args:
            api_keys: Dictionary of service -> API key
        """
        api_keys = api_keys or {}
        
        self.shodan = ShodanIntegration(api_keys.get("shodan", ""))
        self.virustotal = VirusTotalIntegration(api_keys.get("virustotal", ""))
        self.cve = CVELookup()
        self.exploitdb = ExploitDBIntegration()
    
    def enrich_ip(self, ip: str) -> dict:
        """
        Enrich IP with data from multiple sources.
        
        Args:
            ip: IP address
        
        Returns:
            Combined intelligence data
        """
        result = {
            "ip": ip,
            "enriched_at": datetime.now().isoformat(),
            "sources": {}
        }
        
        # Shodan
        shodan_result = self.shodan.host_info(ip)
        if shodan_result.success:
            result["sources"]["shodan"] = {
                "ports": shodan_result.data.get("ports", []),
                "hostnames": shodan_result.data.get("hostnames", []),
                "org": shodan_result.data.get("org", ""),
                "country": shodan_result.data.get("country_code", ""),
                "vulns": shodan_result.data.get("vulns", [])
            }
        
        # VirusTotal
        vt_result = self.virustotal.scan_ip(ip)
        if vt_result.success and vt_result.data:
            attrs = vt_result.data.get("data", {}).get("attributes", {})
            result["sources"]["virustotal"] = {
                "reputation": attrs.get("reputation", 0),
                "malicious": attrs.get("last_analysis_stats", {}).get("malicious", 0),
                "suspicious": attrs.get("last_analysis_stats", {}).get("suspicious", 0)
            }
        
        return result
    
    def lookup_cve(self, cve_id: str) -> dict:
        """
        Lookup CVE with exploit information.
        
        Args:
            cve_id: CVE identifier
        
        Returns:
            CVE data with exploits
        """
        result = {
            "cve_id": cve_id,
            "looked_up_at": datetime.now().isoformat()
        }
        
        # CVE details
        cve_result = self.cve.get_cve(cve_id)
        if cve_result.success:
            result["cve"] = cve_result.data
        else:
            result["cve"] = {"error": cve_result.error}
        
        # Exploits
        exploit_result = self.exploitdb.search_by_cve(cve_id)
        if exploit_result.success:
            result["exploits"] = exploit_result.data
        else:
            result["exploits"] = []
        
        return result
