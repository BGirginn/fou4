"""
Wi-Fi Analysis Module - Performs wireless network scanning and analysis.
Requires aircrack-ng suite and wireless network adapter.
"""
import subprocess
import sys
import os
import re
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import checker, installer, ui
from utils.console import console, print_success, print_error, print_warning, print_info
from rich.panel import Panel
from rich.table import Table
from rich import box


def get_wireless_interfaces():
    """
    Detect wireless network interfaces on the system.
    
    Returns:
        list: List of wireless interface names (e.g., ['wlan0', 'wlan1'])
    """
    wireless_interfaces = []
    
    try:
        # Try iwconfig first
        result = subprocess.run(
            ['iwconfig'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Parse iwconfig output
        lines = result.stdout.split('\n')
        for line in lines:
            # Look for lines starting with interface names
            if line and not line.startswith(' ') and 'no wireless extensions' not in line.lower():
                # Extract interface name (first word)
                interface = line.split()[0]
                if interface and interface != 'lo':
                    wireless_interfaces.append(interface)
        
        # If iwconfig didn't work, try ip command
        if not wireless_interfaces:
            result = subprocess.run(
                ['ip', 'a'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Look for wlan interfaces
            wlan_pattern = re.compile(r'^\d+:\s+(wlan\d+|wlp\d+s\d+):')
            for line in result.stdout.split('\n'):
                match = wlan_pattern.match(line)
                if match:
                    wireless_interfaces.append(match.group(1))
    
    except Exception as e:
        print_error(f"Error detecting network interfaces: {e}")
    
    return wireless_interfaces


def display_interface_menu(interfaces):
    """
    Display wireless interfaces menu.
    
    Args:
        interfaces (list): List of interface names
    """
    header_text = "📡 Wireless Network Interfaces"
    console.print(Panel.fit(header_text, border_style="cyan", box=box.DOUBLE))
    console.print()
    
    if not interfaces:
        print_warning("No wireless network interface found!")
    else:
        print("  {:<5} {:<15}".format("No", "Interface"))
        print("  " + "-" * 25)
        for idx, interface in enumerate(interfaces, 1):
            print("  {:<5} {:<15}".format(f"[{idx}]", interface))
    
    print()
    print("  [0] Back - Return to main menu")
    print("=" * 60)


def kill_conflicting_processes():
    """
    Kill processes that might interfere with monitor mode.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("\n⏳ Checking and closing conflicting processes...")
    
    try:
        result = subprocess.run(
            ['sudo', 'airmon-ng', 'check', 'kill'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print_success("Conflicting processes cleared.")
            return True
        else:
            print_warning(f"Some processes could not be closed. Code: {result.returncode}")
            return True  # Continue anyway
    
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def enable_monitor_mode(interface):
    """
    Enable monitor mode on the specified interface.
    
    Args:
        interface (str): Network interface name
        
    Returns:
        tuple: (success, monitor_interface_name)
    """
    print_info(f"Enabling monitor mode on '{interface}' interface...")
    
    try:
        result = subprocess.run(
            ['sudo', 'airmon-ng', 'start', interface],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print_error(f"Monitor mode could not be started! Code: {result.returncode}")
            return False, None
        
        # Extract monitor interface name from output
        # Usually it's interface + 'mon' (e.g., wlan0mon)
        monitor_interface = None
        
        # Look for "monitor mode enabled on [interface]"
        monitor_pattern = re.compile(r'monitor mode (?:enabled|vif enabled) on (\S+)', re.IGNORECASE)
        match = monitor_pattern.search(result.stdout)
        
        if match:
            monitor_interface = match.group(1)
        else:
            # Fallback: assume it's interface + 'mon'
            monitor_interface = interface + 'mon'
        
        print_success(f"Monitor mode enabled: {monitor_interface}")
        return True, monitor_interface
    
    except Exception as e:
        print_error(f"Error: {e}")
        return False, None


def disable_monitor_mode(monitor_interface):
    """
    Disable monitor mode and restore normal mode.
    
    Args:
        monitor_interface (str): Monitor mode interface name
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not monitor_interface:
        return True
    
    print(f"\n⏳ Disabling monitor mode: {monitor_interface}")
    
    try:
        result = subprocess.run(
            ['sudo', 'airmon-ng', 'stop', monitor_interface],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✓ Monitor mode disabled, interface returned to normal mode.")
            return True
        else:
            print(f"⚠ Warning: Monitor mode could not be disabled. Code: {result.returncode}")
            return False
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def scan_wifi_networks(monitor_interface, duration=15):
    """
    Scan for Wi-Fi networks using airodump-ng.
    
    Args:
        monitor_interface (str): Monitor mode interface name
        duration (int): Scan duration in seconds
        
    Returns:
        tuple: (success, networks_list)
    """
    print(f"\n⏳ Scanning Wi-Fi networks ({duration} seconds)...")
    print("Please wait, scan in progress...\n")
    
    try:
        # Create temporary file for airodump-ng output
        temp_file = '/tmp/fou4_wifi_scan'
        
        # Start airodump-ng
        process = subprocess.Popen(
            ['sudo', 'airodump-ng', monitor_interface, '-w', temp_file, '--output-format', 'csv'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Let it run for specified duration
        time.sleep(duration)
        
        # Terminate the process
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        
        print("\n✓ Scan completed!")
        
        # Parse the CSV output
        networks = []
        csv_file = temp_file + '-01.csv'
        
        try:
            if not os.path.exists(csv_file):
                print_warning(f"Scan file not found: {csv_file}")
                return False, []
            
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Find the access points section
            in_ap_section = False
            for line in lines:
                if 'BSSID' in line and 'PWR' in line:
                    in_ap_section = True
                    continue
                
                if in_ap_section and line.strip():
                    # Stop at station section
                    if 'Station MAC' in line:
                        break
                    
                    # Parse CSV line
                    parts = line.split(',')
                    if len(parts) >= 14:
                        bssid = parts[0].strip()
                        channel = parts[3].strip()
                        encryption = parts[5].strip()
                        power = parts[8].strip()
                        essid = parts[13].strip()
                        
                        if bssid and len(bssid) == 17:  # Valid MAC address
                            networks.append({
                                'bssid': bssid,
                                'essid': essid if essid else '<Hidden>',
                                'channel': channel,
                                'encryption': encryption,
                                'power': power
                            })
            
            # Clean up temporary files
            for ext in ['-01.csv', '-01.cap', '-01.kismet.csv', '-01.kismet.netxml', '-01.log.csv']:
                try:
                    os.remove(temp_file + ext)
                except:
                    pass
        
        except Exception as e:
            print_warning(f"Error parsing scan results: {e}")
            return False, []
        
        return True, networks
    
    except KeyboardInterrupt:
        print("\n✗ Scan cancelled by user.")
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
        return False, []
    
    except Exception as e:
        print(f"✗ Error during scan: {e}")
        return False, []


def display_wifi_networks(networks):
    """
    Display discovered Wi-Fi networks in a formatted table.
    
    Args:
        networks (list): List of network dictionaries
    """
    print("\n" + "=" * 80)
    print(" " * 25 + "Discovered Wi-Fi Networks")
    print("=" * 80)
    print()
    
    if not networks:
        print("  ⚠ No Wi-Fi networks found!")
    else:
        print("  {:<5} {:<20} {:<20} {:<8} {:<15} {:<8}".format(
            "No", "ESSID", "BSSID", "Channel", "Encryption", "Power"
        ))
        print("  " + "-" * 78)
        
        for idx, network in enumerate(networks, 1):
            print("  {:<5} {:<20} {:<20} {:<8} {:<15} {:<8}".format(
                f"[{idx}]",
                network['essid'][:20],
                network['bssid'],
                network['channel'],
                network['encryption'][:15],
                network['power']
            ))
    
    print()
    print("  [0] Back - Return to Wi-Fi module menu")
    print("=" * 80)


def print_wifi_menu():
    """
    Display the Wi-Fi Analysis Module menu.
    """
    print("=" * 60)
    print(" " * 15 + "Wi-Fi Analysis Module")
    print("=" * 60)
    print()
    print("  Wi-Fi Scanning and Analysis Options:")
    print()
    print("  [1] Scan Wi-Fi Networks")
    print("  [2] WPA/WPA2 Attack (Under Development)")
    print("  [3] WEP Attack (Under Development)")
    print("  [0] Back - Return to main menu")
    print()
    print("=" * 60)


def run_wifi_module():
    """
    Main function for the Wi-Fi Analysis Module.
    Handles interface selection, monitor mode, and Wi-Fi scanning.
    """
    monitor_interface = None
    
    try:
        while True:
            ui.clear_screen()
            print_wifi_menu()
            
            try:
                choice = input("\nMake your selection: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting module...")
                break
            
            # Return to main menu
            if choice == '0':
                break
            
            # Wi-Fi Network Scanning
            if choice == '1':
                # Check for required tools
                required_tools = ['airmon-ng', 'airodump-ng', 'iwconfig']
                missing_tools = []
                
                for tool in required_tools:
                    print(f"\nChecking '{tool}' tool...")
                    if not checker.check_tool(tool):
                        missing_tools.append(tool)
                
                if missing_tools:
                    print(f"\n⚠ Missing tools found: {', '.join(missing_tools)}")
                    print("Would you like to install Aircrack-ng suite?")
                    
                    if installer.install_package('aircrack-ng'):
                        print("✓ Installation successful!")
                    else:
                        print("✗ Installation failed or cancelled.")
                        input("Press Enter to continue...")
                        continue
                
                # Detect wireless interfaces
                print("\n⏳ Detecting wireless network interfaces...")
                interfaces = get_wireless_interfaces()
                
                if not interfaces:
                    print("\n✗ No wireless network interface found!")
                    print("Please make sure your wireless network card is connected and enabled.")
                    input("Press Enter to continue...")
                    continue
                
                # Display and select interface
                ui.clear_screen()
                display_interface_menu(interfaces)
                
                try:
                    if_choice = input("\nSelect interface to use: ").strip()
                except (KeyboardInterrupt, EOFError):
                    print("\nOperation cancelled.")
                    continue
                
                if if_choice == '0':
                    continue
                
                try:
                    if_idx = int(if_choice)
                    if 1 <= if_idx <= len(interfaces):
                        selected_interface = interfaces[if_idx - 1]
                    else:
                        print("\n✗ Invalid selection!")
                        input("Press Enter to continue...")
                        continue
                except ValueError:
                    print("\n✗ Enter a valid number!")
                    input("Press Enter to continue...")
                    continue
                
                print(f"\n✓ Selected interface: {selected_interface}")
                input("\nPress Enter to continue...")
                
                # Kill conflicting processes
                if not kill_conflicting_processes():
                    print("\n⚠ Could not clear conflicting processes, continuing...")
                
                # Enable monitor mode
                success, monitor_interface = enable_monitor_mode(selected_interface)
                
                if not success or not monitor_interface:
                    print("\n✗ Monitor mode could not be enabled!")
                    input("Press Enter to continue...")
                    monitor_interface = None
                    continue
                
                # Scan for Wi-Fi networks
                print("\n" + "=" * 60)
                scan_duration = input("Scan duration (seconds, default 15): ").strip()
                try:
                    scan_duration = int(scan_duration) if scan_duration else 15
                except ValueError:
                    scan_duration = 15
                
                success, networks = scan_wifi_networks(monitor_interface, scan_duration)
                
                if success and networks:
                    # Display networks
                    while True:
                        ui.clear_screen()
                        display_wifi_networks(networks)
                        
                        try:
                            net_choice = input("\nSelect a network (for detailed analysis) or 0 to go back: ").strip()
                        except (KeyboardInterrupt, EOFError):
                            break
                        
                        if net_choice == '0':
                            break
                        
                        try:
                            net_idx = int(net_choice)
                            if 1 <= net_idx <= len(networks):
                                selected_network = networks[net_idx - 1]
                                print(f"\n✓ Selected network: {selected_network['essid']} ({selected_network['bssid']})")
                                print("\n⚠ Detailed analysis features are under development...")
                                input("Press Enter to continue...")
                            else:
                                print("\n✗ Invalid selection!")
                                input("Press Enter to continue...")
                        except ValueError:
                            print("\n✗ Enter a valid number!")
                            input("Press Enter to continue...")
                
                else:
                    print("\n⚠ No Wi-Fi networks found or scan failed.")
                    input("Press Enter to continue...")
                
                # Disable monitor mode
                if monitor_interface:
                    disable_monitor_mode(monitor_interface)
                    monitor_interface = None
            
            elif choice in ['2', '3']:
                print(f"\n⚠ This feature is under development...")
                input("Press Enter to continue...")
            
            else:
                print("\n✗ Invalid selection! Please choose an option from the menu.")
                input("Press Enter to continue...")
    
    finally:
        # Ensure monitor mode is disabled when exiting
        if monitor_interface:
            print("\n⏳ Performing cleanup operations...")
            disable_monitor_mode(monitor_interface)


if __name__ == "__main__":
    # Test the module
    run_wifi_module()
