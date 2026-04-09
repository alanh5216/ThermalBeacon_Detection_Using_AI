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

    max_raw_temp = 0
    average_max_raw_temp = 0
    count = 0
    average_max_temp_celsius = 0

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        try:
            reshaped_frame = frame.reshape((392, 256, 2))

            temp_data = reshaped_frame[0:191, :, :]

            for x in range(70,122):
                for y in range(102,154):
                    temp_channel0 = int(temp_data[x][y][0])
                    temp_channel1 = int(temp_data[x][y][1])

                    raw_temp = (temp_channel1 << 8) + temp_channel0

                    if raw_temp > max_raw_temp:
                        max_raw_temp = raw_temp

            
            if count == 19:
                average_max_raw_temp += max_raw_temp
                average_max_raw_temp /= 20
                count = 0
                average_max_temp_celsius = raw_to_celsius_hightemp_mode(average_max_raw_temp)
                print(f"Average Max Temp(Celsius): {average_max_temp_celsius}")
                average_max_raw_temp = 0
            else:
                average_max_raw_temp += max_raw_temp
                count += 1

            max_raw_temp = 0
            
            image_data = reshaped_frame[196:388, :, :]

            image_luminance_only = image_data[:,:,0]

            display_frame = cv2.resize(image_luminance_only, (768, 576), interpolation=cv2.INTER_NEAREST)

            box_corners = get_boundingbox_corners(image_luminance_only)
            
            if box_corners:
                display_frame = cv2.cvtColor(display_frame, cv2.COLOR_GRAY2BGR)
                for corners in box_corners:
                    x1, y1, x2, y2 = corners
                    cv2.rectangle(display_frame, (x1 * 3, y1 * 3), (x2 * 3, y2 * 3), (0, 255, 0), 2)
            
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
    results = model(yolo_input, classes=[0], verbose=False)

    for box in results[0].boxes:
        coords = box.xyxy[0].tolist()
        coords = [int(c) for c in coords]
        box_coords.append(coords)
    
    return box_coords


if __name__ == "__main__":
    main()