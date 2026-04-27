import cv2
import numpy as np
import math
import time
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

# --- NEW: The State Machine Class ---
class BeaconDecoder:
    def __init__(self):
        self.history = []          # Stores tuples of (timestamp, temp)
        self.bit_stream = []       # Stores the decoded 0s and 1s
        self.state = "IDLE"        # "IDLE" (seeking preamble) or "READING" (seeking ID)
        self.decoded_id = None     # The final confirmed Beacon ID
        
        self.bit_duration = 0.8    # 800ms per bit (matches your Arduino)
        self.threshold = 47      # Temps above this are a 1, below are a 0

    def add_reading(self, current_time, temp):
        self.history.append((current_time, temp))

        # Check if 800ms has passed since the oldest frame in our buffer
        oldest_time = self.history[0][0]
        if current_time - oldest_time >= self.bit_duration:
            
            # 1. Average the temperatures over the last 800ms to filter out noise
            avg_temp = sum(t for _, t in self.history) / len(self.history)
            
            # 2. Reset the buffer for the next 800ms window
            self.history = [(current_time, temp)] 

            # 3. Threshold the average into a binary bit
            bit = 1 if avg_temp > self.threshold else 0
            self.bit_stream.append(bit)

            # 4. Run the State Machine
            self._process_state_machine()

    def _process_state_machine(self):
        if self.state == "IDLE":
            # Keep the stream from getting infinitely long to save memory
            if len(self.bit_stream) > 5:
                self.bit_stream.pop(0)

            # Check for our 5-bit Barker Code Preamble
            if self.bit_stream == [1, 1, 1, 0, 1]:
                print("\n[+] PREAMBLE FOUND! Locking onto packet...")
                self.state = "READING"
                self.bit_stream = [] # Clear the stream to receive the payload

        elif self.state == "READING":
            # Wait until we have 5 bits (4-bit ID + 1-bit Even Parity)
            if len(self.bit_stream) == 5:
                id_bits = self.bit_stream[0:4]
                parity_bit = self.bit_stream[4]

                # Check Even Parity Safety Net
                num_ones = sum(id_bits)
                expected_parity = 1 if num_ones % 2 != 0 else 0

                if parity_bit == expected_parity:
                    # Convert the 4-bit binary list into an integer ID
                    beacon_id = int("".join(str(b) for b in id_bits), 2)
                    
                    # Check against the reserved forbidden ID (e.g., 14)
                    if beacon_id != 14:
                        self.decoded_id = beacon_id
                        print(f"[SUCCESS] Beacon ID {beacon_id} confirmed!")
                    else:
                        print("[ERROR] Reserved ID detected. Dropping packet.")
                else:
                    print(f"[ERROR] Parity mismatch. False sync. Dropping packet. {id_bits}")
                
                # Reset back to IDLE to wait for the next looped transmission
                self.state = "IDLE"
                self.bit_stream = []


def main():
    camera_index = 1
    cap = cv2.VideoCapture(camera_index, cv2.CAP_MSMF)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 384)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUY2'))
    cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    # --- NEW: Dictionary to hold our decoders ---
    active_trackers = {}
    
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        try:
            current_time = time.time()
            reshaped_frame = frame.reshape((392, 256, 2))
            temp_data = reshaped_frame[0:192, :, :]
            image_data = reshaped_frame[196:388, :, :]
            image_luminance_only = image_data[:,:,0]

            display_frame = cv2.resize(image_luminance_only, (768, 576), interpolation=cv2.INTER_NEAREST)
            box_corners = get_boundingbox_corners(image_luminance_only)
            
            if box_corners:
                display_frame = cv2.cvtColor(display_frame, cv2.COLOR_GRAY2BGR)
                for corners in box_corners:
                    x1, y1, x2, y2, track_id = corners
                    
                    # --- NEW: Fetch or create the state machine for this YOLO ID ---
                    if track_id not in active_trackers:
                        active_trackers[track_id] = BeaconDecoder()
                    
                    decoder = active_trackers[track_id]

                    # Get max temp and feed it into the decoder
                    max_raw_temp = max_temp_in_box(x1, y1, x2, y2, temp_data)
                    max_celsius_temp = raw_to_celsius_hightemp_mode(max_raw_temp)
                    
                    # Feed the time and temp to our state machine
                    decoder.add_reading(current_time, max_celsius_temp)

                    # --- NEW: Dynamic Visuals ---
                    # If we successfully decoded them, turn their box Cyan and show Beacon ID
                    if decoder.decoded_id is not None:
                        box_color = (255, 255, 0) # Cyan in BGR
                        label = f"BEACON ID: {decoder.decoded_id} ({max_celsius_temp:.1f}C)"
                    else:
                        # Otherwise, leave it Green and show the temp and YOLO ID
                        box_color = (0, 255, 0) # Green in BGR
                        label = f"Detecting... Y_ID:{track_id} ({max_celsius_temp:.1f}C)"

                    cv2.rectangle(display_frame, (x1 * 3, y1 * 3), (x2 * 3, y2 * 3), box_color, 2)
                    cv2.putText(display_frame, label, (x1 * 3, (y1 * 3) - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
            
            cv2.imshow("Topdon TC001 - Windows DirectShow", display_frame)
            
        except Exception as e:
            print(f"Error parsing frame. Raw shape was: {frame.shape} | Error: {e}")
        
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