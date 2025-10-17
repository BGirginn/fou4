# Testing Checklist - Interactive Mode Fix

## Pre-Testing Setup

- [ ] Fresh Kali Linux VM or Linux system with penetration testing tools
- [ ] Python 3.8+ installed
- [ ] Git installed
- [ ] Root/sudo access available

---

## Installation Test

```bash
# Clone or pull latest
cd /path/to/fou4
git pull origin main

# Install dependencies
pip3 install -r requirements.txt

# Verify no syntax errors
python3 -m py_compile fou4.py
python3 -m py_compile modules/osint_module.py
```

**Expected Result:** No errors

---

## Module Testing Checklist

### ✅ Test 1: Main Menu Display
```bash
python3 fou4.py
```

**Expected:**
- [ ] ASCII banner displays
- [ ] Main menu shows all 8 options (0-7)
- [ ] No "Under construction" messages in menu
- [ ] Workspace status shown (if any)

---

### ✅ Test 2: Wi-Fi Module (Option 1)

**Steps:**
1. Run `sudo python3 fou4.py`
2. Select option `1` (Wi-Fi Attacks)
3. Should check for aircrack-ng tools
4. Display Wi-Fi submenu with 5 options

**Expected:**
- [ ] Tool check runs
- [ ] Submenu displays (not "Under construction")
- [ ] Options: Monitor Mode, Scan, Handshake, Crack, Back

**Test Sub-option 1 (Enable Monitor Mode):**
- [ ] Lists wireless interfaces
- [ ] Prompts for interface selection
- [ ] Attempts to enable monitor mode (may require wireless card)

---

### ✅ Test 3: Network Module (Option 2)

**Steps:**
1. Select option `2` (Network Analysis)
2. Should check for nmap
3. Display network submenu

**Test Port Scan:**
- [ ] Select option `1` (Port Scan)
- [ ] Prompts for target: Enter `scanme.nmap.org`
- [ ] Prompts for port range: Enter `80,443,22`
- [ ] Executes nmap scan
- [ ] Shows results
- [ ] Returns to menu (not main menu immediately)

**Expected Result:** Nmap output displayed with open ports

---

### ✅ Test 4: Web Module (Option 3)

**Steps:**
1. Select option `3` (Web Exploitation)
2. Should check for gobuster/dirb
3. Display web submenu

**Test Directory Enum:**
- [ ] Select option `1` (Directory Enumeration)
- [ ] Prompts for URL: Enter `http://testphp.vulnweb.com`
- [ ] Asks about custom wordlist (select No)
- [ ] Executes gobuster/dirb
- [ ] Shows discovered directories
- [ ] Returns to menu

**Expected Result:** Directory enumeration runs and shows results

---

### ✅ Test 5: OSINT Module (Option 4) - NEW!

**Steps:**
1. Select option `4` (OSINT Tools)
2. Check for theHarvester and subfinder
3. Display OSINT submenu with 6 options

**Test Domain Lookup with theHarvester:**
- [ ] Select option `1` (Domain Lookup)
- [ ] Enter domain: `example.com`
- [ ] Choose tool: `theHarvester`
- [ ] Executes theHarvester
- [ ] Shows gathered information
- [ ] Returns to OSINT menu (not main menu)

**Test Subdomain Enum with subfinder:**
- [ ] Select option `3` (Subdomain Enumeration)  
- [ ] Enter domain: `example.com`
- [ ] Choose tool: `subfinder`
- [ ] Executes subfinder
- [ ] Shows subdomains
- [ ] Returns to OSINT menu

**Expected Result:** Both tools execute without "Under construction" message

---

### ✅ Test 6: Reporting Module (Option 5)

**Steps:**
1. Select option `5` (Reporting)
2. Display reporting submenu
3. Select option `1` (View Vulnerability Report)

**Expected:**
- [ ] Shows vulnerability summary
- [ ] Displays vulnerability table
- [ ] No crash or "Under construction"

---

### ✅ Test 7: Workspace Module (Option 6)

**Steps:**
1. Select option `6` (Workspace Management)
2. Display workspace submenu

**Test Create Workspace:**
- [ ] Select option `1` (Create Workspace)
- [ ] Enter name: `test-workspace`
- [ ] Enter description: `Test workspace`
- [ ] Enter target: `192.168.1.0/24`
- [ ] Workspace created successfully

**Test Load Workspace:**
- [ ] Select option `2` (Load/Switch Workspace)
- [ ] Shows list of workspaces
- [ ] Can select workspace by ID

**Expected:** Workspace operations work correctly

---

### ✅ Test 8: Password Module (Option 7)

**Steps:**
1. Select option `7` (Password Attacks)
2. Check for hydra
3. Display password attack submenu with 9 options

**Test SSH Attack (Simulation):**
- [ ] Select option `1` (SSH)
- [ ] Enter target: `192.168.1.100`
- [ ] Choose single username: `admin`
- [ ] Enter wordlist path (or use default)
- [ ] Shows hydra command execution
- [ ] Returns to menu

**Expected:** Hydra attack initiates without "Under construction"

---

### ✅ Test 9: Exit (Option 0)

**Steps:**
1. From main menu, select option `0`

**Expected:**
- [ ] Shows exit message: "Exiting Kali Tool. Stay safe! 🔒"
- [ ] Program terminates cleanly
- [ ] No errors or crashes

---

## Negative Tests

### Test: Invalid Input
- [ ] Enter invalid option (e.g., `99`, `abc`)
- [ ] Should show error and re-prompt

### Test: Missing Tools
- [ ] Try module without required tool installed
- [ ] Should prompt to install or show error message
- [ ] Should not crash

### Test: Ctrl+C Interrupt
- [ ] Press Ctrl+C during tool execution
- [ ] Should show "Operation cancelled by user"
- [ ] Should exit gracefully

---

## CLI Mode Tests (Bonus)

### Test CLI Port Scan:
```bash
python3 fou4.py --module network --tool port-scan --target scanme.nmap.org --ports 80,443
```
**Expected:** Runs port scan without interactive menu

### Test CLI Wi-Fi Scan:
```bash
sudo python3 fou4.py --module wifi --tool scan --interface wlan0mon --duration 10
```
**Expected:** Scans Wi-Fi networks (requires monitor mode)

### Test CLI Password Attack:
```bash
python3 fou4.py --module password --tool ssh --target 192.168.1.100 --username admin --wordlist /path/to/wordlist.txt
```
**Expected:** Initiates SSH brute force

---

## Success Criteria

### Must Pass:
- ✅ All 7 modules display menus (no placeholders)
- ✅ Each module can execute at least one operation
- ✅ No "Under construction" messages appear
- ✅ OSINT module fully functional with tool selection
- ✅ Tool checking and installation prompts work
- ✅ Returns to correct menu after each operation
- ✅ No Python syntax or runtime errors
- ✅ Graceful exit on Ctrl+C

### Optional (Tool Dependent):
- Some operations may require specific tools installed
- Wi-Fi operations require wireless card and monitor mode
- Some scans require root/sudo privileges

---

## Test Results Template

```
Test Date: _____________
Tester: _____________
OS: Kali Linux / Other: _____________
Python Version: _____________

Module Tests:
[ ] Main Menu - PASS/FAIL
[ ] Wi-Fi Module - PASS/FAIL
[ ] Network Module - PASS/FAIL
[ ] Web Module - PASS/FAIL
[ ] OSINT Module - PASS/FAIL
[ ] Reporting Module - PASS/FAIL
[ ] Workspace Module - PASS/FAIL
[ ] Password Module - PASS/FAIL

Overall Result: PASS / FAIL

Notes:
_________________________________
_________________________________
_________________________________
```

---

## Troubleshooting

### Issue: "Module not found"
**Solution:** Ensure you're in the correct directory and all files are present

### Issue: "Tool not found"
**Solution:** Install required tools or let the program install them

### Issue: Permission denied
**Solution:** Use `sudo` for Wi-Fi operations

### Issue: Import errors
**Solution:** Run `pip3 install -r requirements.txt`

---

## Quick Smoke Test (2 minutes)

```bash
# 1. Start tool
python3 fou4.py

# 2. Test OSINT (new feature)
Option 4 → Option 1 → example.com → theHarvester → Verify output

# 3. Test Network
Option 2 → Option 1 → scanme.nmap.org → 80,443 → Verify scan

# 4. Exit
Option 0 → Verify clean exit
```

If all three pass → ✅ **FIX CONFIRMED**
