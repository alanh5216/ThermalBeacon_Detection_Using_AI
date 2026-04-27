import cv2
import time

def main():
    camera_index = 0
    
    # Initialize natively
    cap = cv2.VideoCapture(camera_index)

    # Your theory: Ask for the exact full payload size
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 384)
    
    # Crucial: Tell Metal NOT to try and apply RGB color correction to the telemetry half
    cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)

    print("Camera initialized. Waiting for USB handshake...")
    time.sleep(2)

    if not cap.isOpened():
        print("Error: AVFoundation refused to open the camera with these parameters.")
        return

    print("Success! AVFoundation accepted the parameters. Attempting to pull the raw payload...")
    
    frames_grabbed = 0
    while frames_grabbed < 5:
        ret, frame = cap.read()
        
        if not ret or frame is None or frame.size == 0:
            print("Dropped frame (Shutter calibration?)")
            time.sleep(0.1)
            continue
            
        print(f"Payload received! Shape: {frame.shape}")
        frames_grabbed += 1
        time.sleep(0.1)

    cap.release()
    print("Test finished without crashing!")

if __name__ == "__main__":
    main()