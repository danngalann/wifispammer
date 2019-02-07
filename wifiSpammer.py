import random, os, argparse, sys
try:
    from scapy.all import ( Dot11,
                            Dot11Beacon,
                            Dot11Elt,
                            RadioTap,
                            sendp)
except ImportError:
    print("Scapy could not be imported.")
    print("Make sure to 'pip3 install scapy'")
    sys.exit(0)


# Generates a random MAC from vendor
def randomMACVendor(vendor):
    generated = ""
    for i in range(0,3):
        generated += ":" + hex(random.randint(0,255))[2:]

    return vendor + generated

# Generates a random MAC
def randomMAC():
    generated = ""
    for i in range(0,6):
        generated += ":" + hex(random.randint(0,255))[2:]

    return generated[1:]

# Gets SSID list from file
def getSSIDs(file):
    SSIDs = []
    ssidList = open(file)
    for line in ssidList.readlines():
        SSIDs.append(line[:-1])
    ssidList.close()

    return SSIDs

# Sets interface in monitor mode
def setMonitor(interface):
    exitValue = 0
    print(f"Setting {interface} in monitor mode...")
    os.system(f"ifconfig {interface} down")
    exitValue = os.system(f"iwconfig {interface} mode monitor")
    os.system(f"ifconfig {interface} up")

    if exitValue != 0:
        print("")
        print("Something went wrong setting monitor mode.")
        print("Are you sure your card supports monitor mode?")
        sys.exit(0)

# Sets interface in managed mode
def setManaged(interface):
    os.system(f"ifconfig {interface} down")
    os.system(f"iwconfig {interface} mode managed")
    os.system(f"ifconfig {interface} up")

vendors = {"Nokia":"C0:41:21", "Apple":"BC:92:6B", 
        "Arduino":"A8:61:0A", "Motorola":"00:E0:0C", "Google":"54:60:09"}
beacon = Dot11Beacon(cap="ESS", timestamp=1)

rsn = Dot11Elt(ID='RSNinfo', info=(
'\x01\x00'              #RSN Version 1
'\x00\x0f\xac\x02'      #Group Cipher Suite : 00-0f-ac TKIP
'\x02\x00'              #2 Pairwise Cipher Suites (next two lines)
'\x00\x0f\xac\x04'      #AES Cipher
'\x00\x0f\xac\x02'      #TKIP Cipher
'\x01\x00'              #1 Authentication Key Managment Suite (line below)
'\x00\x0f\xac\x02'      #Pre-Shared Key
'\x00\x00'))            #RSN Capabilities (no extra capabilities)

# Parse arguments
DESCRIPTION = "Another silly beacon spammer ;)"
parser = argparse.ArgumentParser(description=DESCRIPTION)
parser.add_argument("-f", "--file", default="wifi.lst", help="File to import the SSIDs from (default wifi.lst)")
parser.add_argument("-v", "--vendor", default="Apple", help="Vendor to spoof (-l to list available vendors)")
parser.add_argument("-i", "--interface", help="Interface used to spam SSIDs")
parser.add_argument("-l", "--list-vendors",action="store_true", help="List vendors")
parser.add_argument("-r", "--random-mac",action="store_true", help="Uses a fully random BSSID instead of using a vendor")
args = parser.parse_args()

# Check OS
if sys.platform.lower() != "linux":
    print("This script only works in Linux!")
    sys.exit(0)

# Check root
if os.getuid() != 0:
    print("Must run as root!")
    sys.exit(0)

# List vendors if -l is present
if args.list_vendors:
    print("Vendors to choose (default Apple):\n")
    for vendor in vendors:
        print(vendor)
    sys.exit(0)

# Check interface
if not args.interface:
    print("Interface not specified. Extiting...")
    sys.exit(0)
else:
    interfaces = os.listdir("/sys/class/net/")
    if args.interface not in interfaces:
        print("Interface not found")
        sys.exit(0)

# Set interface in monitor mode
setMonitor(args.interface)

# Main loop
try:
    SSIDs=getSSIDs(args.file)
    iface = args.interface
    while True:
        
        #For each SSID
        for SSID in SSIDs:

            # Set MAC
            if args.random_mac:
                sender=randomMAC
            else:
                sender = randomMACVendor(vendors[args.vendor])
            
            # Create paquet
            dot11 = Dot11(type=0, subtype=8, addr1='ff:ff:ff:ff:ff:ff',
            addr2=sender, addr3=sender)
            essid = Dot11Elt(ID='SSID',info=SSID, len=len(SSID))
            frame = RadioTap()/dot11/beacon/essid/rsn
            print("Sending paquet with SSID: " + SSID)
            print("MAC: " + sender)

            #Switch channel
            channel = random.randint(1,11)
            os.system(f"iw dev {args.interface} set channel {channel}")
            print("Channel " + str(channel))

            # Send beacons
            sendp(frame, iface=iface, inter=0.010, loop=0, verbose=1, count=8)
            print("\n")
except KeyboardInterrupt:
    print(f"\n\nWifiSpammer stopped. Setting {args.interface} in managed mode")
    setManaged(args.interface)
    print("Done")
