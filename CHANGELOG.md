# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2025-10-10

### Added
- 🗂️ **Workspace System (Step 11)**
  - Workspace-based project management
  - Workspaces table with metadata (name, description, target, timestamps)
  - All data tied to workspaces (hosts, ports, web_findings, osint_*)
  - Separate data storage for multiple projects
  - Create, switch, and delete workspace functions
  - Active workspace tracking
  - Workspace isolation for security assessments

- 📄 **Professional Reporting Module**
  - `modules/report_module.py` - Automated report generation
  - Markdown format detailed reports
  - Workspace-based data collection
  - Comprehensive statistics (hosts, ports, web findings, OSINT)
  - Table-formatted organized presentation
  - Automatic file naming (report-{workspace}-{timestamp}.md)
  - Report preview (Rich tables)
  - Automatic file opening (Windows/macOS/Linux)

- 🔧 **Database Enhancements**
  - Workspace management functions:
    * `create_workspace()` - Create new workspace
    * `list_workspaces()` - List all workspaces
    * `set_active_workspace()` - Select active workspace
    * `get_active_workspace()` - Get active workspace info
    * `delete_workspace()` - Delete workspace and data (CASCADE)
  - All insert functions support workspace_id
  - Automatic active workspace usage

- 🎨 **User Interface Improvements**
  - Workspace selection/creation at startup
  - Workspace management menu ([9] Workspace)
  - Reporting menu ([5] Reports)
  - Workspace list table (with statistics)
  - Active workspace indicator
  - Colorful and user-friendly menus

- 🎨 **ASCII Banner**
  - Professional welcome screen with FOU4 logo
  - Version display
  - Usage instructions on startup

### Changed
- 🔧 `utils/db.py` - Workspace system + 10+ new functions
- 🔧 `fou4.py` - Workspace management at startup, new menu options
- 🔧 `utils/ui.py` - Workspace and report options in main menu, ASCII banner
- 📝 All table structures updated with workspace_id

### Database Changes
```sql
-- New table
CREATE TABLE workspaces (
    id, name UNIQUE, description, target,
    created_at, last_used, is_active
)

-- Updated tables (workspace_id added)
- hosts: workspace_id FOREIGN KEY
- scan_sessions: workspace_id FOREIGN KEY  
- osint_emails: workspace_id FOREIGN KEY
- osint_subdomains: workspace_id FOREIGN KEY
- osint_ips: workspace_id FOREIGN KEY

-- UNIQUE constraints updated with workspace_id
- hosts: UNIQUE(workspace_id, ip_address)
- osint_emails: UNIQUE(workspace_id, domain, email)
- osint_subdomains: UNIQUE(workspace_id, domain, subdomain)
- osint_ips: UNIQUE(workspace_id, domain, ip_address)
```

### Technical Details
- SQLite CASCADE delete (all data deleted when workspace deleted)
- LEFT JOINs for workspace statistics
- Rich Table and Panel for professional UI
- Markdown report format (GitHub compatible)
- Timestamp-based file naming
- Cross-platform file opening (Windows/macOS/Linux)

### Usage Flow
1. Program starts → Workspace selection required
2. User creates or selects workspace
3. All scans saved to active workspace
4. [9] to switch workspaces
5. [5] to generate report for active workspace
6. Report saved as Markdown file

---

## [1.3.0] - 2025-10-10

### Added
- 🤖 **Smart Automation - Module Chaining (Step 10)**
  - Contextual intelligence for cross-module smart transitions
  - Automatic web module suggestion after network scan
  - Automatic detection of web ports (80, 443, 8000, 8080, 8443, 8888, 3000, 5000)
  - User confirmation with `rich.prompt.Confirm`
  - Parameter passing between modules

- 🔗 **Module Chaining Features**
  - `check_web_ports()` - Web port detection function
  - `suggest_web_module()` - Smart web module suggestion
  - `run_web_module(target_host, detected_ports)` - Targeted execution
  - Automatic URL suggestion (http/https protocol selection)
  - Port-based smart defaults

- 🎨 **User Experience Improvements**
  - "🤖 Smart Automation Active!" notification
  - Display of detected ports
  - Auto-fill with suggested URL
  - Smooth module transitions
  - User-friendly confirmation mechanism

### Changed
- 🔧 `modules/network_module.py` - Web port check and module chaining added
- 🔧 `modules/web_module.py` - Target parameter support added
- 🔧 `print_web_menu()` function added (was missing)
- 📝 Module function signatures updated

### Technical Details
- Rich Confirm.ask() integration
- Dynamic import to prevent circular dependencies
- Optional parameters for backward compatibility
- HTTP/HTTPS protocol auto-selection (443, 8443 → https)
- Web port detection algorithm (port + service name check)

### User Flow
1. Network scan performed (Nmap/Masscan/RustScan)
2. Open ports found and saved to database
3. System auto-detects web ports (80, 443, etc.)
4. User asked "Would you like to run Web Discovery Module?"
5. If confirmed, target and ports auto-passed to web module
6. Web module opens with suggested URL (user can modify)
7. Returns to network module when complete

---

## [1.2.0] - 2025-10-10

### Added
- 🕵️ **OSINT Module (Step 9)**
  - `modules/osint_module.py` - Passive information gathering module
  - theHarvester tool integration
  - Email address discovery
  - Subdomain enumeration
  - IP address collection
  - Multiple source support (Google, Bing, Anubis, CRTsh, etc.)

- 🗄️ **OSINT Database Tables**
  - `osint_emails` - Email addresses
  - `osint_subdomains` - Subdomains (with IPs)
  - `osint_ips` - IP addresses
  - Domain-based query support

- 📊 **OSINT Functions (db.py)**
  - `add_osint_email()` - Save email
  - `add_osint_subdomain()` - Save subdomain
  - `add_osint_ip()` - Save IP
  - `get_osint_results()` - Get domain-based results

- 🎨 **Rich UI Integration**
  - Panel menu (source selection guide)
  - 3 separate table formats (Emails, Subdomains, IPs)
  - Colorful result display
  - Counter badges

- 🔍 **Smart Parsing**
  - Regex-based email extraction
  - IP address validation (0-255)
  - Subdomain + IP matching
  - Version number filtering

### Changed
- 🔧 `utils/db.py` - 3 new tables + 5 functions added
- 🔧 `utils/ui.py` - OSINT option added to main menu
- 🔧 `fou4.py` - OSINT module import and dispatcher added
- 📝 Main menu updated ([4] OSINT Module)

### Technical Details
- theHarvester subprocess integration
- Timeout protection (5 minutes)
- Real-time output display
- Duplicate record prevention (UNIQUE constraint)
- Timestamp-based record tracking
- Source-based data storage

---

## [1.1.0] - 2025-10-10

### Added
- 🗄️ **SQLite Database Integration (Step 8)**
  - `utils/db.py` - Database management module
  - Persistent storage of scan results
  - Host, port, and web findings tables
  - Scan session tracking
  - Database statistics

- 📊 **Data Model**
  - `hosts` table - IP address, hostname, first/last seen
  - `ports` table - Port, protocol, service information
  - `web_findings` table - URL, found path, status code
  - `scan_sessions` table - Scan metadata

- 🔄 **Automatic Data Saving**
  - Network scan results auto-saved
  - Web findings parsed and saved in real-time
  - Host and port relationships

- 📈 **Statistics Functions**
  - Total host/port/finding counts
  - Last scan dates
  - Scan history queries

### Changed
- 🔧 `network_module.py` - DB integration added
- 🔧 `web_module.py` - Finding parsing and DB saving added
- 🔧 `fou4.py` - DB initialization at startup added
- 📝 Documentation updated (STATUS.md, CHANGELOG.md)

### Technical Details
- SQLite3 standard library usage
- FOREIGN KEY and UNIQUE constraints
- Performance optimization with indexes
- ON CONFLICT DO UPDATE (upsert) support
- Row factory for dict access

---

## [1.0.0] - 2025-10-10

### Added
- 🎉 **Initial Release!**

- ✨ **Wi-Fi Analysis Module**
  - Automatic wireless interface detection
  - Monitor mode management
  - Wi-Fi network scanning (airodump-ng)
  - BSSID, ESSID, channel information

- ✨ **Network Scanning Module**
  - Nmap port scanning support
  - Masscan fast scanning
  - Netdiscover ARP discovery
  - RustScan ultra-fast scanning
  - Interactive port analysis
  - Detailed service detection

- ✨ **Web Discovery Module**
  - Gobuster directory scanning
  - Dirb classic scanning
  - Feroxbuster modern scanning
  - Real-time output

- 🛠️ **Utility Tools**
  - Tool availability checker (checker.py)
  - Automatic package installer (installer.py)
  - User interface helpers (ui.py)

- 📚 **Comprehensive Documentation**
  - README.md
  - requirements.txt
  - In-code docstrings

- 🔒 **Security Features**
  - Root privilege check
  - Try-except error handling
  - Finally blocks for cleanup guarantees
  - Input validation

### Changed
- 🎨 PEP 8 compliant code formatting
- 📝 Enhanced user feedback
- 🔧 Optimized error handling

### Security
- ⚠️ Root/sudo privilege requirement
- 🛡️ Safe subprocess calls
- 🔐 Timeout protections

---

## [Future Releases]

### [1.5.0] - Planned
- Export capabilities (JSON/PDF/HTML)
- Scan result comparison over time
- Graphical statistics dashboard
- CLI data query commands
- PostgreSQL/MySQL support

### [1.6.0] - Planned
- WPA/WPA2 handshake capture
- Automatic password cracking
- Exploit database integration
- Metasploit framework integration

---

## Legend
- ✨ New feature
- 🔧 Fix
- 🎨 Style/format change
- 📚 Documentation
- 🔒 Security
- 🛠️ Infrastructure
- ⚡ Performance improvement
- 🐛 Bug fix
- 🗄️ Database
- 🤖 Automation
- 🕵️ Intelligence gathering
