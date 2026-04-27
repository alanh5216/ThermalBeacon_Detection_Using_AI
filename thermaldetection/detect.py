import cv2
import numpy as np
import math
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

def main():
    camera_index = 1
    cap = cv2.VideoCapture(camera_index, cv2.CAP_MSMF)

    # 1. Force the standard video resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 384)
    
    # 2. Force Windows to use the raw YUY2 format
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUY2'))
    
    # 3. Tell OpenCV NOT to try and guess the colors. Just give us the raw bytes.
    cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        try:
            reshaped_frame = frame.reshape((392, 256, 2))

            temp_data = reshaped_frame[0:192, :, :]
            
            image_data = reshaped_frame[196:388, :, :]

            image_luminance_only = image_data[:,:,0]

            display_frame = cv2.resize(image_luminance_only, (768, 576), interpolation=cv2.INTER_NEAREST)

            box_corners = get_boundingbox_corners(image_luminance_only)
            
            if box_corners:
                display_frame = cv2.cvtColor(display_frame, cv2.COLOR_GRAY2BGR)
                for corners in box_corners:
                    # Unpack all 5 variables now
                    x1, y1, x2, y2, track_id = corners
                    
                    # Draw the bounding box
                    cv2.rectangle(display_frame, (x1 * 3, y1 * 3), (x2 * 3, y2 * 3), (0, 255, 0), 2)
                    
                    # --- NEW: Draw the ID text floating above the box ---
                    # cv2.putText takes (image, text, coordinates, font, scale, color, thickness)
                    label = f"ID: {track_id}"
                    cv2.putText(display_frame, label, (x1 * 3, (y1 * 3) - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    # Calculate and print the temperature associated with that specific ID
                    max_raw_temp = max_temp_in_box(x1, y1, x2, y2, temp_data)
                    max_celsius_temp = raw_to_celsius_hightemp_mode(max_raw_temp)
                    print(f"Person ID {track_id}: {max_celsius_temp:.1f} C")
            
            cv2.imshow("Topdon TC001 - Windows DirectShow", display_frame)
            
        except Exception as e:
            # If it fails, print the shape so we can see exactly what Windows handed us
            print(f"Error parsing frame. Raw shape was: {frame.shape} | Error: {e}")
        
        # Wait for the 'q' key to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def raw_to_celsius_hightemp_mode(raw_temp):
    a = 0.0335732
    two_a = 0.0671464
    four_a = 0.1342928
    b = 5.69897
    neg_b = -5.69897
    b_squared = 32.478259
    c = 2228.67448

    d = c - raw_temp
    temp_in_celsius = (neg_b + math.sqrt(b_squared - (four_a * d))) / two_a
    return temp_in_celsius

def raw_to_celsius_lowtemp_mode(raw_temp):
    a = 0.379761
    two_a = 0.759522
    four_a = 1.519044
    b = 9.81632
    neg_b = -9.81632
    b_squared = 96.3601383
    c = 4324.32514

    d = c - raw_temp
    temp_in_celsius = (neg_b + math.sqrt(b_squared - (four_a * d))) / two_a
    return temp_in_celsius

def get_boundingbox_corners(frame):
    box_coords = []
    yolo_input = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    
    results = model.track(yolo_input, classes=[0], persist=True, verbose=False)

    if results[0].boxes.id is not None:
        # Extract the boxes and the IDs as lists
        boxes = results[0].boxes.xyxy.tolist()
        track_ids = results[0].boxes.id.tolist()

        # Zip them together so we can loop through both at the same time
        for box, track_id in zip(boxes, track_ids):
            coords = [int(c) for c in box]
            
            # Append the 4 coordinates PLUS the new track_id
            box_coords.append((coords[0], coords[1], coords[2], coords[3], int(track_id)))
    
    return box_coords

def max_temp_in_box(x1, y1, x2, y2, temp_data):
    # 1. Safety Clamp: Ensure YOLO doesn't ask for a pixel outside our array bounds
    max_y = temp_data.shape[0] - 1
    max_x = temp_data.shape[1] - 1
    
    x1 = max(0, min(x1, max_x))
    x2 = max(0, min(x2, max_x))
    y1 = max(0, min(y1, max_y))
    y2 = max(0, min(y2, max_y))

    # 2. Slice the exact bounding box out of the temperature array using [Y, X]
    roi_data = temp_data[y1:y2, x1:x2, :]

    # 3. If the box is somehow empty (width or height is 0), return 0 to avoid a crash
    if roi_data.size == 0:
        return 0

    # 4. Instant NumPy calculation (No for-loops!)
    low_bytes = roi_data[:, :, 0].astype(np.uint16)
    high_bytes = roi_data[:, :, 1].astype(np.uint16)
    
    raw_temps = (high_bytes << 8) + low_bytes
    
    # Return the absolute maximum value inside this array
    return np.max(raw_temps)

if __name__ == "__main__":
    main()