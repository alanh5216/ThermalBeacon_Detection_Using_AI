import usb.core
import usb.util
import sys

VID = 11231
PID = 258

def main():
    print("Searching for Topdon TC001...")
    dev = usb.core.find(idVendor=VID, idProduct=PID)

    if dev is None:
        print("Camera not found. Check the connection!")
        sys.exit()

    print("Camera found! Configuring USB device...")

    # Set the active configuration. With no arguments, the first
    # configuration will be the active one.
    try:
        dev.set_configuration()
    except usb.core.USBError as e:
        print(f"Warning on set_configuration: {e}")
        # Sometimes macOS throws an error here even if it succeeds, so we continue

    # We need to claim Interface 1, where Endpoint 0x81 lives
    interface_number = 1
    
    try:
        print(f"Attempting to claim Interface {interface_number}...")
        usb.util.claim_interface(dev, interface_number)
        print("Interface claimed successfully!")
    except usb.core.USBError as e:
        print(f"Failed to claim interface: {e}")
        print("macOS might be holding onto the device tightly (Resource Busy).")
        sys.exit()

    # The exact address and packet size from your probe
    endpoint_address = 0x81
    packet_size = 512

    print(f"\nListening to Endpoint {hex(endpoint_address)}...")
    
    try:
        # Let's try to pull 10 packets of raw data
        for i in range(10):
            # read(endpoint, size, timeout_in_ms)
            data = dev.read(endpoint_address, packet_size, timeout=2000)
            
            # Print the total length and the first 10 bytes in raw hex format
            hex_data = " ".join([hex(b) for b in data[:10]])
            print(f"Packet {i+1} | Received {len(data)} bytes -> [{hex_data} ...]")
            
    except usb.core.USBError as e:
        print(f"\nUSB Read Error/Timeout: {e}")
        print("The camera might be waiting for a specific initialization command before streaming.")
        
    finally:
        # Always release the interface when done so we don't crash the USB bus
        usb.util.release_interface(dev, interface_number)
        print("\nInterface released safely.")

if __name__ == '__main__':
    main()