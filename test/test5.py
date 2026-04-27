import cv2
import numpy as np

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

    min_raw_temp = 18000
    average_min_raw_temp = 0
    count = 0

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

                    if raw_temp < min_raw_temp:
                        min_raw_temp = raw_temp

            
            if count == 19:
                average_min_raw_temp += min_raw_temp
                average_min_raw_temp /= 20
                count = 0
                print(f"Average Min Raw Temp: {average_min_raw_temp}")
                average_min_raw_temp = 0
            else:
                average_min_raw_temp += min_raw_temp
                count += 1

            min_raw_temp = 18000
            
            image_data = reshaped_frame[196:388, :, :]

            image_luminance_only = image_data[:,:,0]

            display_frame = cv2.resize(image_luminance_only, (768, 576), interpolation=cv2.INTER_NEAREST)
            
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
    
