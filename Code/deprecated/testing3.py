import cv2
import numpy as np

def main():
    camera_index = 1
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 192)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUY2'))
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
            # Expecting (192, 256, 2)
            if len(frame.shape) == 3 and frame.shape[2] == 2:

                # Extract the raw 2 channels
                hi = frame[:, :, 0].astype(np.uint16)
                lo = frame[:, :, 1].astype(np.uint16)

                # Reconstruct 16-bit thermal values
                raw = (lo << 8) | hi

                # Convert to temperature (Celsius)
                temp_map = (raw / 64.0) - 273.15

                # Normalize for display (so it looks good)
                norm = cv2.normalize(raw, None, 0, 255, cv2.NORM_MINMAX)
                norm = norm.astype(np.uint8)

                # Apply colormap
                display = cv2.applyColorMap(norm, cv2.COLORMAP_INFERNO)

                # Get center temperature
                h, w = temp_map.shape
                cy, cx = h // 2, w // 2
                center_temp = temp_map[cy, cx]

                # Draw crosshair
                cv2.drawMarker(display, (cx, cy), (255, 255, 255), markerType=cv2.MARKER_CROSS, thickness=1)

                # Show temperature
                cv2.putText(display, f"{center_temp:.2f} C",
                            (cx + 10, cy - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (255, 255, 255), 1)

            else:
                display = frame

            # Resize for visibility
            display = cv2.resize(display, (768, 576), interpolation=cv2.INTER_NEAREST)

            cv2.imshow("Thermal Camera", display)
            print(center_temp)

        except Exception as e:
            print(f"Error: {e}, shape={frame.shape}")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()