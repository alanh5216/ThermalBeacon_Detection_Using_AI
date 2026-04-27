import cv2
import numpy as np

def main():
    # You confirmed the Topdon is at index 1 on your Windows machine
    camera_index = 1
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

    # 1. Force the standard video resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 192)
    
    # 2. Force Windows to use the raw YUY2 format
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUY2'))
    
    # 3. Tell OpenCV NOT to try and guess the colors. Just give us the raw bytes.
    cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("Camera opened successfully! Press 'q' to close the window.")

    while True:
        ret, frame = cap.read()

        if not ret or frame is None:
            continue
            
        try:
            # The raw YUY2 frame shape should be (192, 256, 2). 
            # The actual thermal image is hidden in the first channel (index 0).
            if len(frame.shape) == 3 and frame.shape[2] == 2:
                # Extract the clean grayscale thermal image
                clean_frame = frame[:, :, 0]
            elif len(frame.shape) == 2:
                # If Windows already flattened it to 2D
                clean_frame = frame
            else:
                # Fallback just in case OpenCV ignored our commands
                clean_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Apply a thermal color map to the grayscale image so it looks awesome
            thermal_color_mapped = cv2.applyColorMap(clean_frame, cv2.COLORMAP_INFERNO)

            # Resize the 256x192 image so it's actually large enough to see on your monitor
            # INTER_NEAREST keeps the pixels sharp instead of blurring them together
            display_frame = cv2.resize(clean_frame, (768, 576), interpolation=cv2.INTER_NEAREST)

            cv2.imshow("Topdon TC001 - Windows DirectShow", display_frame)
            
        except Exception as e:
            # If it fails, print the shape so we can see exactly what Windows handed us
            print(f"Error parsing frame. Raw shape was: {frame.shape} | Error: {e}")

        # Wait for the 'q' key to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()