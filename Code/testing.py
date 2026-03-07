import usb.core
import usb.util
import sys

# Hardware IDs from your system_profiler output
VID = 11231
PID = 258

def main():
    print("Bypassing macOS drivers and scanning the raw USB bus...")
    
    # Find the device directly using its hardware ID
    dev = usb.core.find(idVendor=VID, idProduct=PID)

    if dev is None:
        print("Camera not found on the USB bus.")
        print("Please physically unplug and replug the camera, then try again.")
        sys.exit()

    print("\n--- Topdon TC001 Hardware Found! ---")
    
    # macOS aggressively locks UVC devices. We will try to read the 
    # configuration descriptors to map out the data endpoints.
    try:
        for cfg in dev:
            print(f"\nConfiguration: {cfg.bConfigurationValue}")
            for intf in cfg:
                print(f"  Interface: {intf.bInterfaceNumber} | Alt Setting: {intf.bAlternateSetting}")
                for ep in intf:
                    # We are looking for an "IN" endpoint (usually 0x81, 0x82, etc.)
                    # which is where the raw camera data actually flows out.
                    direction = "IN" if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN else "OUT"
                    print(f"    -> Endpoint: {hex(ep.bEndpointAddress)} ({direction}) | Max Packet: {ep.wMaxPacketSize} bytes")
                    
    except Exception as e:
        print(f"\nError mapping endpoints: {e}")

if __name__ == '__main__':
    main()