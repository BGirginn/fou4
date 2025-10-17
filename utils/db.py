import sqlite3
import os
from utils.console import print_info, print_success, print_error, print_warning

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kali_tool.db")

def get_connection() -> sqlite3.Connection:
    """
    Create and return a database connection with foreign keys enabled.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print_error(f"Failed to connect to database: {str(e)}")
        raise

def initialize_database():
    """Initialize the database with all required tables and indexes."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create workspaces table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                target TEXT,
                is_active INTEGER DEFAULT 0
            )
        """)
        
        # Create hosts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY,
                workspace_id INTEGER NOT NULL,
                ip_address TEXT NOT NULL,
                hostname TEXT,
                UNIQUE(workspace_id, ip_address),
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        """)
        
        # Create ports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ports (
                id INTEGER PRIMARY KEY,
                host_id INTEGER NOT NULL,
                port INTEGER NOT NULL,
                protocol TEXT NOT NULL,
                service TEXT,
                UNIQUE(host_id, port, protocol),
                FOREIGN KEY(host_id) REFERENCES hosts(id) ON DELETE CASCADE
            )
        """)
        
        # Create web_findings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS web_findings (
                id INTEGER PRIMARY KEY,
                host_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                found_path TEXT NOT NULL,
                status_code INTEGER,
                UNIQUE(host_id, url, found_path),
                FOREIGN KEY(host_id) REFERENCES hosts(id) ON DELETE CASCADE
            )
        """)
        
        # Create osint_emails table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS osint_emails (
                id INTEGER PRIMARY KEY,
                workspace_id INTEGER NOT NULL,
                domain TEXT NOT NULL,
                email TEXT NOT NULL,
                source TEXT,
                UNIQUE(workspace_id, domain, email),
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        """)
        
        # Create osint_subdomains table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS osint_subdomains (
                id INTEGER PRIMARY KEY,
                workspace_id INTEGER NOT NULL,
                domain TEXT NOT NULL,
                subdomain TEXT NOT NULL,
                ip_address TEXT,
                UNIQUE(workspace_id, domain, subdomain),
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        """)
        
        # Create osint_ips table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS osint_ips (
                id INTEGER PRIMARY KEY,
                workspace_id INTEGER NOT NULL,
                ip_address TEXT NOT NULL,
                location TEXT,
                organization TEXT,
                UNIQUE(workspace_id, ip_address),
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        """)
        
        # Create vulnerabilities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INTEGER PRIMARY KEY,
                host_id INTEGER NOT NULL,
                port INTEGER,
                cve TEXT,
                description TEXT NOT NULL,
                severity TEXT,
                UNIQUE(host_id, port, cve),
                FOREIGN KEY(host_id) REFERENCES hosts(id) ON DELETE CASCADE
            )
        """)
        
        # Create credentials table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY,
                host_id INTEGER NOT NULL,
                service TEXT NOT NULL,
                port TEXT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                UNIQUE(host_id, service, username),
                FOREIGN KEY(host_id) REFERENCES hosts(id) ON DELETE CASCADE
            )
        """)
        
        # Create performance indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hosts_workspace ON hosts(workspace_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hosts_ip ON hosts(ip_address)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ports_host ON ports(host_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ports_port ON ports(port)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_web_findings_host ON web_findings(host_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_osint_emails_workspace ON osint_emails(workspace_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_osint_emails_domain ON osint_emails(domain)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_osint_subdomains_workspace ON osint_subdomains(workspace_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_osint_subdomains_domain ON osint_subdomains(domain)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_osint_ips_workspace ON osint_ips(workspace_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workspaces_active ON workspaces(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vulnerabilities_host ON vulnerabilities(host_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vulnerabilities_cve ON vulnerabilities(cve)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_credentials_host ON credentials(host_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_credentials_service ON credentials(service)")
        
        conn.commit()
        conn.close()
        print_success("Database initialized successfully.")
        
    except Exception as e:
        print_error(f"Failed to initialize database: {str(e)}")
        raise

# ==================== Workspace Functions ====================

def create_workspace(name: str, description: str = "", target: str = "") -> bool:
    """
    Create a new workspace.
    
    Args:
        name: Workspace name
        description: Workspace description
        target: Target of the workspace
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO workspaces (name, description, target, is_active)
            VALUES (?, ?, ?, 0)
        """, (name, description, target))
        
        conn.commit()
        conn.close()
        print_success(f"Workspace '{name}' created successfully.")
        return True
        
    except sqlite3.IntegrityError:
        print_error(f"Workspace '{name}' already exists.")
        return False
    except Exception as e:
        print_error(f"Failed to create workspace: {str(e)}")
        return False

def list_workspaces():
    """
    List all workspaces.
    
    Returns:
        list: List of workspace records
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, target, is_active
            FROM workspaces
            ORDER BY is_active DESC, name ASC
        """)
        
        workspaces = cursor.fetchall()
        conn.close()
        return workspaces
        
    except Exception as e:
        print_error(f"Failed to list workspaces: {str(e)}")
        return []

def set_active_workspace(workspace_id: int) -> bool:
    """
    Set a workspace as active and deactivate all others.
    
    Args:
        workspace_id: ID of the workspace to activate
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Deactivate all workspaces
        cursor.execute("UPDATE workspaces SET is_active = 0")
        
        # Activate the specified workspace
        cursor.execute("""
            UPDATE workspaces SET is_active = 1 WHERE id = ?
        """, (workspace_id,))
        
        if cursor.rowcount == 0:
            print_error(f"Workspace with ID {workspace_id} not found.")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        print_success(f"Workspace {workspace_id} activated.")
        return True
        
    except Exception as e:
        print_error(f"Failed to set active workspace: {str(e)}")
        return False

def get_active_workspace():
    """
    Get the currently active workspace.
    
    Returns:
        sqlite3.Row or None: Active workspace record or None
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, target, is_active
            FROM workspaces
            WHERE is_active = 1
            LIMIT 1
        """)
        
        workspace = cursor.fetchone()
        conn.close()
        return workspace
        
    except Exception as e:
        print_error(f"Failed to get active workspace: {str(e)}")
        return None

def delete_workspace(workspace_id: int) -> bool:
    """
    Delete a workspace and all associated data.
    
    Args:
        workspace_id: ID of the workspace to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
        
        if cursor.rowcount == 0:
            print_error(f"Workspace with ID {workspace_id} not found.")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        print_success(f"Workspace {workspace_id} deleted successfully.")
        return True
        
    except Exception as e:
        print_error(f"Failed to delete workspace: {str(e)}")
        return False

# ==================== Data Insertion Functions ====================

def add_host(ip_address: str, hostname: str = None) -> int:
    """
    Add a host to the active workspace.
    
    Args:
        ip_address: IP address of the host
        hostname: Hostname (optional)
        
    Returns:
        int: Host ID or -1 if failed
    """
    try:
        workspace = get_active_workspace()
        if not workspace:
            print_error("No active workspace. Please activate a workspace first.")
            return -1
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO hosts (workspace_id, ip_address, hostname)
            VALUES (?, ?, ?)
            ON CONFLICT(workspace_id, ip_address) DO UPDATE SET
                hostname = COALESCE(excluded.hostname, hostname)
        """, (workspace['id'], ip_address, hostname))
        
        # Get the host ID
        cursor.execute("""
            SELECT id FROM hosts WHERE workspace_id = ? AND ip_address = ?
        """, (workspace['id'], ip_address))
        
        host_id = cursor.fetchone()['id']
        
        conn.commit()
        conn.close()
        return host_id
        
    except Exception as e:
        print_error(f"Failed to add host: {str(e)}")
        return -1

def add_port(host_id: int, port: int, protocol: str, service: str = None) -> bool:
    """
    Add a port to a host.
    
    Args:
        host_id: ID of the host
        port: Port number
        protocol: Protocol (tcp/udp)
        service: Service name (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ports (host_id, port, protocol, service)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(host_id, port, protocol) DO UPDATE SET
                service = COALESCE(excluded.service, service)
        """, (host_id, port, protocol, service))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Failed to add port: {str(e)}")
        return False

def add_web_finding(host_id: int, url: str, found_path: str, status_code: int = None) -> bool:
    """
    Add a web finding to a host.
    
    Args:
        host_id: ID of the host
        url: Base URL
        found_path: Found path/directory
        status_code: HTTP status code (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO web_findings (host_id, url, found_path, status_code)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(host_id, url, found_path) DO UPDATE SET
                status_code = COALESCE(excluded.status_code, status_code)
        """, (host_id, url, found_path, status_code))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Failed to add web finding: {str(e)}")
        return False

def add_osint_email(domain: str, email: str, source: str = None) -> bool:
    """
    Add an OSINT email finding to the active workspace.
    
    Args:
        domain: Domain name
        email: Email address
        source: Source of the finding (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        workspace = get_active_workspace()
        if not workspace:
            print_error("No active workspace. Please activate a workspace first.")
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO osint_emails (workspace_id, domain, email, source)
            VALUES (?, ?, ?, ?)
        """, (workspace['id'], domain, email, source))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Failed to add OSINT email: {str(e)}")
        return False

def add_osint_subdomain(domain: str, subdomain: str, ip_address: str = None) -> bool:
    """
    Add an OSINT subdomain finding to the active workspace.
    
    Args:
        domain: Parent domain
        subdomain: Subdomain
        ip_address: IP address (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        workspace = get_active_workspace()
        if not workspace:
            print_error("No active workspace. Please activate a workspace first.")
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO osint_subdomains (workspace_id, domain, subdomain, ip_address)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(workspace_id, domain, subdomain) DO UPDATE SET
                ip_address = COALESCE(excluded.ip_address, ip_address)
        """, (workspace['id'], domain, subdomain, ip_address))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Failed to add OSINT subdomain: {str(e)}")
        return False

def add_osint_ip(ip_address: str, location: str = None, organization: str = None) -> bool:
    """
    Add an OSINT IP finding to the active workspace.
    
    Args:
        ip_address: IP address
        location: Location information (optional)
        organization: Organization information (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        workspace = get_active_workspace()
        if not workspace:
            print_error("No active workspace. Please activate a workspace first.")
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO osint_ips (workspace_id, ip_address, location, organization)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(workspace_id, ip_address) DO UPDATE SET
                location = COALESCE(excluded.location, location),
                organization = COALESCE(excluded.organization, organization)
        """, (workspace['id'], ip_address, location, organization))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Failed to add OSINT IP: {str(e)}")
        return False


def add_vulnerability(host_id: int, port: int, cve: str, description: str, severity: str = None) -> bool:
    """
    Add a vulnerability finding to a host.
    
    Args:
        host_id: ID of the host
        port: Port number where vulnerability was found (None for host-level)
        cve: CVE identifier (e.g., CVE-2021-1234)
        description: Vulnerability description
        severity: Severity level (optional: critical, high, medium, low)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO vulnerabilities (host_id, port, cve, description, severity)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(host_id, port, cve) DO UPDATE SET
                description = excluded.description,
                severity = COALESCE(excluded.severity, severity)
        """, (host_id, port, cve, description, severity))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Failed to add vulnerability: {str(e)}")
        return False


def get_vulnerabilities(host_id: int = None) -> list:
    """
    Get vulnerabilities for a specific host or all hosts in active workspace.
    
    Args:
        host_id: ID of the host (None for all hosts in workspace)
        
    Returns:
        list: List of vulnerability records
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if host_id:
            # Get vulnerabilities for specific host
            cursor.execute("""
                SELECT v.*, h.ip_address, h.hostname
                FROM vulnerabilities v
                JOIN hosts h ON v.host_id = h.id
                WHERE v.host_id = ?
                ORDER BY v.severity DESC, v.cve
            """, (host_id,))
        else:
            # Get vulnerabilities for all hosts in active workspace
            workspace = get_active_workspace()
            if not workspace:
                return []
            
            cursor.execute("""
                SELECT v.*, h.ip_address, h.hostname
                FROM vulnerabilities v
                JOIN hosts h ON v.host_id = h.id
                WHERE h.workspace_id = ?
                ORDER BY h.ip_address, v.port, v.severity DESC
            """, (workspace['id'],))
        
        vulnerabilities = cursor.fetchall()
        conn.close()
        return vulnerabilities
        
    except Exception as e:
        print_error(f"Failed to retrieve vulnerabilities: {str(e)}")
        return []

