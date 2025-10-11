"""
Database Module - SQLite database management for FOU4.

This module provides functions to store scan results persistently,
including hosts, ports, and web findings.
"""
import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.console import console, print_success, print_error, print_warning, print_info


# Database file path (in the project root)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fou4.db')


def get_connection():
    """
    Get a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection object
        
    Raises:
        sqlite3.Error: If connection fails
    """
    try:
        # Enable foreign key support
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        conn.execute('PRAGMA foreign_keys = ON')  # Enable foreign key constraints
        return conn
    except sqlite3.Error as e:
        print_error(f"Database connection failed: {e}")
        raise
    except Exception as e:
        print_error(f"Unexpected error connecting to database: {e}")
        raise


def initialize_database():
    """
    Initialize the database and create tables if they don't exist.
    
    Creates the following tables:
    - workspaces: Stores workspace/project information
    - hosts: Stores scanned host information
    - ports: Stores open port information for each host
    - web_findings: Stores discovered web directories/files
    - scan_sessions: Stores scan session metadata
    - osint_emails: Stores discovered email addresses
    - osint_subdomains: Stores discovered subdomains
    - osint_ips: Stores discovered IP addresses
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create workspaces table (NEW!)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workspaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                target TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 0
            )
        ''')
        
        # Create hosts table (with workspace_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                ip_address TEXT NOT NULL,
                hostname TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
                UNIQUE(workspace_id, ip_address)
            )
        ''')
        
        # Create ports table (workspace_id inherited from host)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER NOT NULL,
                port INTEGER NOT NULL,
                protocol TEXT NOT NULL,
                service TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (host_id) REFERENCES hosts (id) ON DELETE CASCADE,
                UNIQUE(host_id, port, protocol)
            )
        ''')
        
        # Create web_findings table (workspace_id inherited from host)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS web_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                found_path TEXT NOT NULL,
                status_code INTEGER,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (host_id) REFERENCES hosts (id) ON DELETE CASCADE,
                UNIQUE(host_id, url, found_path)
            )
        ''')
        
        # Create scan_sessions table (with workspace_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                module_name TEXT NOT NULL,
                target TEXT NOT NULL,
                tool_name TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT DEFAULT 'running',
                results_count INTEGER DEFAULT 0,
                FOREIGN KEY (workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
            )
        ''')
        
        # Create OSINT emails table (with workspace_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS osint_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                domain TEXT NOT NULL,
                email TEXT NOT NULL,
                source TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
                UNIQUE(workspace_id, domain, email)
            )
        ''')
        
        # Create OSINT subdomains table (with workspace_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS osint_subdomains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                domain TEXT NOT NULL,
                subdomain TEXT NOT NULL,
                ip_address TEXT,
                source TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
                UNIQUE(workspace_id, domain, subdomain)
            )
        ''')
        
        # Create OSINT IPs table (with workspace_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS osint_ips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                domain TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                source TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
                UNIQUE(workspace_id, domain, ip_address)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_workspaces_name ON workspaces(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_workspaces_active ON workspaces(is_active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hosts_workspace ON hosts(workspace_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hosts_ip ON hosts(ip_address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ports_host ON ports(host_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_web_host ON web_findings(host_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_workspace ON scan_sessions(workspace_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_module ON scan_sessions(module_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_osint_emails_workspace ON osint_emails(workspace_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_osint_emails_domain ON osint_emails(domain)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_osint_subdomains_workspace ON osint_subdomains(workspace_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_osint_subdomains_domain ON osint_subdomains(domain)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_osint_ips_workspace ON osint_ips(workspace_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_osint_ips_domain ON osint_ips(domain)')
        
        conn.commit()
        conn.close()
        
        print_success(f"Database initialized successfully: {DB_PATH}")
        return True
        
    except sqlite3.Error as e:
        print_error(f"Database initialization error: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


# ==================== WORKSPACE MANAGEMENT ====================

def create_workspace(name, description=None, target=None):
    """
    Create a new workspace.
    
    Args:
        name (str): Workspace name
        description (str, optional): Workspace description
        target (str, optional): Primary target (IP, domain, range)
        
    Returns:
        int: Workspace ID if successful, None otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO workspaces (name, description, target, created_at, last_used)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (name, description, target))
        
        workspace_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        print_success(f"Workspace created: {name} (ID: {workspace_id})")
        return workspace_id
        
    except sqlite3.IntegrityError:
        print_error(f"Workspace '{name}' already exists!")
        return None
    except sqlite3.Error as e:
        print_error(f"Workspace creation error: {e}")
        return None


def list_workspaces():
    """
    List all workspaces.
    
    Returns:
        list: List of workspace dictionaries
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                w.id, 
                w.name, 
                w.description, 
                w.target,
                w.created_at,
                w.last_used,
                w.is_active,
                COUNT(DISTINCT h.id) as host_count,
                COUNT(DISTINCT p.id) as port_count,
                COUNT(DISTINCT wf.id) as web_finding_count
            FROM workspaces w
            LEFT JOIN hosts h ON w.id = h.workspace_id
            LEFT JOIN ports p ON h.id = p.host_id
            LEFT JOIN web_findings wf ON h.id = wf.host_id
            GROUP BY w.id
            ORDER BY w.last_used DESC
        ''')
        
        workspaces = []
        for row in cursor.fetchall():
            workspaces.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'target': row[3],
                'created_at': row[4],
                'last_used': row[5],
                'is_active': row[6],
                'host_count': row[7],
                'port_count': row[8],
                'web_finding_count': row[9]
            })
        
        conn.close()
        return workspaces
        
    except sqlite3.Error as e:
        print_error(f"Workspace listing error: {e}")
        return []


def set_active_workspace(workspace_id):
    """
    Set a workspace as active and deactivate others.
    
    Args:
        workspace_id (int): ID of the workspace to activate
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Deactivate all workspaces
        cursor.execute('UPDATE workspaces SET is_active = 0')
        
        # Activate the selected workspace
        cursor.execute('''
            UPDATE workspaces 
            SET is_active = 1, last_used = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (workspace_id,))
        
        if cursor.rowcount == 0:
            print_error(f"Workspace not found: ID {workspace_id}")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        
        return True
        
    except sqlite3.Error as e:
        print_error(f"Workspace activation error: {e}")
        return False


def get_active_workspace():
    """
    Get the currently active workspace.
    
    Returns:
        dict: Active workspace info, or None if no active workspace
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, description, target, created_at, last_used
            FROM workspaces
            WHERE is_active = 1
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'target': row[3],
                'created_at': row[4],
                'last_used': row[5]
            }
        return None
        
    except sqlite3.Error as e:
        print_error(f"Active workspace query error: {e}")
        return None


def delete_workspace(workspace_id):
    """
    Delete a workspace and all its data (CASCADE).
    
    Args:
        workspace_id (int): ID of the workspace to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM workspaces WHERE id = ?', (workspace_id,))
        
        if cursor.rowcount == 0:
            print_error(f"Workspace not found: ID {workspace_id}")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        
        print_success(f"Workspace deleted: ID {workspace_id}")
        return True
        
    except sqlite3.Error as e:
        print_error(f"Workspace deletion error: {e}")
        return False


# ==================== HOST MANAGEMENT ====================

def add_host(ip_address, hostname=None, workspace_id=None):
    """
    Add or update a host in the database.
    
    Args:
        ip_address (str): IP address of the host
        hostname (str, optional): Hostname if available
        workspace_id (int, optional): Workspace ID (uses active if not provided)
        
    Returns:
        int: Host ID if successful, None otherwise
    """
    try:
        # Get active workspace if not provided
        if workspace_id is None:
            active_ws = get_active_workspace()
            if not active_ws:
                print_error("No active workspace! Please select a workspace.")
                return None
            workspace_id = active_ws['id']
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Try to insert, if exists update last_seen
        cursor.execute('''
            INSERT INTO hosts (workspace_id, ip_address, hostname, first_seen, last_seen)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(workspace_id, ip_address) DO UPDATE SET
                hostname = COALESCE(excluded.hostname, hostname),
                last_seen = CURRENT_TIMESTAMP
        ''', (workspace_id, ip_address, hostname))
        
        # Get the host ID
        cursor.execute('SELECT id FROM hosts WHERE workspace_id = ? AND ip_address = ?', (workspace_id, ip_address))
        host_id = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        return host_id
        
    except sqlite3.Error as e:
        print_error(f"Host addition error: {e}")
        return None





def add_port(host_id, port, protocol, service=None):
    """
    Add a port to the database for a specific host.
    
    Args:
        host_id (int): ID of the host
        port (int): Port number
        protocol (str): Protocol (tcp/udp)
        service (str, optional): Service name
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO ports (host_id, port, protocol, service)
            VALUES (?, ?, ?, ?)
        ''', (host_id, port, protocol, service))
        
        conn.commit()
        conn.close()
        
        return True
        
    except sqlite3.Error as e:
        print_error(f"Port addition error: {e}")
        return False


def add_web_finding(host_id, url, found_path, status_code=None):
    """
    Add a web finding (discovered directory/file) to the database.
    
    Args:
        host_id (int): ID of the host
        url (str): Base URL
        found_path (str): Discovered path
        status_code (int, optional): HTTP status code
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO web_findings (host_id, url, found_path, status_code)
            VALUES (?, ?, ?, ?)
        ''', (host_id, url, found_path, status_code))
        
        conn.commit()
        conn.close()
        
        return True
        
    except sqlite3.Error as e:
        print_error(f"Web finding addition error: {e}")
        return False


def create_scan_session(module_name, target, tool_name=None):
    """
    Create a new scan session record.
    
    Args:
        module_name (str): Name of the module (wifi/network/web)
        target (str): Scan target (IP, URL, etc.)
        tool_name (str, optional): Tool used for scanning
        
    Returns:
        int: Session ID if successful, None otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scan_sessions (module_name, target, tool_name)
            VALUES (?, ?, ?)
        ''', (module_name, target, tool_name))
        
        session_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return session_id
        
    except sqlite3.Error as e:
        print_error(f"Scan session creation error: {e}")
        return None


def update_scan_session(session_id, status='completed', results_count=0):
    """
    Update a scan session with completion info.
    
    Args:
        session_id (int): ID of the session
        status (str): Session status (completed/failed/cancelled)
        results_count (int): Number of results found
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE scan_sessions
            SET completed_at = CURRENT_TIMESTAMP,
                status = ?,
                results_count = ?
            WHERE id = ?
        ''', (status, results_count, session_id))
        
        conn.commit()
        conn.close()
        
        return True
        
    except sqlite3.Error as e:
        print_error(f"Scan session update error: {e}")
        return False


def get_host_by_ip(ip_address):
    """
    Get host information by IP address.
    
    Args:
        ip_address (str): IP address to lookup
        
    Returns:
        dict: Host information or None if not found
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM hosts WHERE ip_address = ?', (ip_address,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
        
    except sqlite3.Error as e:
        print_error(f"Host query error: {e}")
        return None


def get_ports_by_host(host_id):
    """
    Get all ports for a specific host.
    
    Args:
        host_id (int): ID of the host
        
    Returns:
        list: List of port dictionaries
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM ports
            WHERE host_id = ?
            ORDER BY port
        ''', (host_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
        
    except sqlite3.Error as e:
        print_error(f"Port query error: {e}")
        return []


def get_web_findings_by_host(host_id):
    """
    Get all web findings for a specific host.
    
    Args:
        host_id (int): ID of the host
        
    Returns:
        list: List of web finding dictionaries
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM web_findings
            WHERE host_id = ?
            ORDER BY discovered_at DESC
        ''', (host_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
        
    except sqlite3.Error as e:
        print_error(f"Web findings query error: {e}")
        return []


def get_all_hosts():
    """
    Get all hosts from the database.
    
    Returns:
        list: List of host dictionaries
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM hosts ORDER BY last_seen DESC')
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
        
    except sqlite3.Error as e:
        print_error(f"Host list query error: {e}")
        return []


def get_scan_history(module_name=None, limit=10):
    """
    Get scan session history.
    
    Args:
        module_name (str, optional): Filter by module name
        limit (int): Maximum number of results
        
    Returns:
        list: List of scan session dictionaries
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if module_name:
            cursor.execute('''
                SELECT * FROM scan_sessions
                WHERE module_name = ?
                ORDER BY started_at DESC
                LIMIT ?
            ''', (module_name, limit))
        else:
            cursor.execute('''
                SELECT * FROM scan_sessions
                ORDER BY started_at DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
        
    except sqlite3.Error as e:
        print_error(f"Scan history query error: {e}")
        return []


def get_database_stats():
    """
    Get database statistics (counts of hosts, ports, findings).
    
    Returns:
        dict: Statistics dictionary
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Count hosts
        cursor.execute('SELECT COUNT(*) FROM hosts')
        stats['total_hosts'] = cursor.fetchone()[0]
        
        # Count ports
        cursor.execute('SELECT COUNT(*) FROM ports')
        stats['total_ports'] = cursor.fetchone()[0]
        
        # Count web findings
        cursor.execute('SELECT COUNT(*) FROM web_findings')
        stats['total_web_findings'] = cursor.fetchone()[0]
        
        # Count scan sessions
        cursor.execute('SELECT COUNT(*) FROM scan_sessions')
        stats['total_scans'] = cursor.fetchone()[0]
        
        # Most recent scan
        cursor.execute('SELECT started_at FROM scan_sessions ORDER BY started_at DESC LIMIT 1')
        row = cursor.fetchone()
        stats['last_scan'] = row[0] if row else None
        
        conn.close()
        
        return stats
        
    except sqlite3.Error as e:
        print_error(f"Statistics query error: {e}")
        return {}


def add_osint_email(domain, email, source=None, workspace_id=None):
    """
    Add an email address found during OSINT.
    
    Args:
        domain (str): Target domain
        email (str): Email address found
        source (str, optional): Source where it was found
        workspace_id (int, optional): Workspace ID (uses active if not provided)
        
    Returns:
        int: Email ID if successful, None otherwise
    """
    try:
        # Get active workspace if not provided
        if workspace_id is None:
            active_ws = get_active_workspace()
            if not active_ws:
                print_error("No active workspace!")
                return None
            workspace_id = active_ws['id']
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO osint_emails (workspace_id, domain, email, source, discovered_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(workspace_id, domain, email) DO UPDATE SET
                discovered_at = CURRENT_TIMESTAMP
        ''', (workspace_id, domain, email, source))
        
        email_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return email_id
        
    except sqlite3.Error as e:
        print_error(f"Email save error: {e}")
        return None


def add_osint_subdomain(domain, subdomain, ip_address=None, source=None, workspace_id=None):
    """
    Add a subdomain found during OSINT.
    
    Args:
        domain (str): Target domain
        subdomain (str): Subdomain found
        ip_address (str, optional): IP address of subdomain
        source (str, optional): Source where it was found
        workspace_id (int, optional): Workspace ID (uses active if not provided)
        
    Returns:
        int: Subdomain ID if successful, None otherwise
    """
    try:
        # Get active workspace if not provided
        if workspace_id is None:
            active_ws = get_active_workspace()
            if not active_ws:
                print_error("No active workspace!")
                return None
            workspace_id = active_ws['id']
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO osint_subdomains (workspace_id, domain, subdomain, ip_address, source, discovered_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(workspace_id, domain, subdomain) DO UPDATE SET
                ip_address = COALESCE(?, ip_address),
                discovered_at = CURRENT_TIMESTAMP
        ''', (workspace_id, domain, subdomain, ip_address, source, ip_address))
        
        subdomain_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return subdomain_id
        
    except sqlite3.Error as e:
        print_error(f"Subdomain save error: {e}")
        return None


def add_osint_ip(domain, ip_address, source=None, workspace_id=None):
    """
    Add an IP address found during OSINT.
    
    Args:
        domain (str): Target domain
        ip_address (str): IP address found
        source (str, optional): Source where it was found
        workspace_id (int, optional): Workspace ID (uses active if not provided)
        
    Returns:
        int: IP ID if successful, None otherwise
    """
    try:
        # Get active workspace if not provided
        if workspace_id is None:
            active_ws = get_active_workspace()
            if not active_ws:
                print_error("No active workspace!")
                return None
            workspace_id = active_ws['id']
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO osint_ips (workspace_id, domain, ip_address, source, discovered_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(workspace_id, domain, ip_address) DO UPDATE SET
                discovered_at = CURRENT_TIMESTAMP
        ''', (workspace_id, domain, ip_address, source))
        
        ip_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return ip_id
        
    except sqlite3.Error as e:
        print_error(f"IP save error: {e}")
        return None





def get_osint_results(domain):
    """
    Get all OSINT results for a domain.
    
    Args:
        domain (str): Target domain
        
    Returns:
        dict: Dictionary with emails, subdomains, and IPs
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        results = {
            'emails': [],
            'subdomains': [],
            'ips': []
        }
        
        # Get emails
        cursor.execute('''
            SELECT email, source, discovered_at
            FROM osint_emails
            WHERE domain = ?
            ORDER BY discovered_at DESC
        ''', (domain,))
        results['emails'] = [dict(row) for row in cursor.fetchall()]
        
        # Get subdomains
        cursor.execute('''
            SELECT subdomain, ip_address, source, discovered_at
            FROM osint_subdomains
            WHERE domain = ?
            ORDER BY discovered_at DESC
        ''', (domain,))
        results['subdomains'] = [dict(row) for row in cursor.fetchall()]
        
        # Get IPs
        cursor.execute('''
            SELECT ip_address, source, discovered_at
            FROM osint_ips
            WHERE domain = ?
            ORDER BY discovered_at DESC
        ''', (domain,))
        results['ips'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return results
        
    except sqlite3.Error as e:
        print_error(f"OSINT results query error: {e}")
        return {'emails': [], 'subdomains': [], 'ips': []}


if __name__ == "__main__":
    # Test the database module
    print_info("Testing database module...")
    
    # Initialize database
    if initialize_database():
        print_success("Database initialized!")
        
        # Test adding a host
        host_id = add_host("192.168.1.1", "router.local")
        if host_id:
            print_success(f"Host added, ID: {host_id}")
            
            # Test adding ports
            add_port(host_id, 22, "tcp", "ssh")
            add_port(host_id, 80, "tcp", "http")
            print_success("Ports added!")
            
            # Test adding web finding
            add_web_finding(host_id, "http://192.168.1.1", "/admin", 200)
            print_success("Web finding added!")
            
            # Get stats
            stats = get_database_stats()
            print_info(f"Statistics: {stats}")
    else:
        print_error("Database initialization failed!")
