import cv2
import numpy as np

# Global variables to store the last clicked coordinates
clicked_x = -1
clicked_y = -1
scale_factor = 3  # We are scaling 256x192 up to 768x576 (which is 3x)

def mouse_callback(event, x, y, flags, param):
    global clicked_x, clicked_y
    # When the left mouse button is clicked, record the coordinates
    if event == cv2.EVENT_LBUTTONDOWN:
        # Divide by our scale_factor to map the click on the large 768x576 window
        # back to the exact pixel on the small 256x192 raw array
        clicked_x = x // scale_factor
        clicked_y = y // scale_factor

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

    # Create the window and attach the mouse listener BEFORE the loop starts
    window_name = "Topdon TC001 - Windows DirectShow"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback)

    print("Camera opened successfully! Click anywhere to see the value. Press 'q' to close.")

    while True:
        ret, frame = cap.read()
        
        if not ret or frame is None:
            continue
            
        try:
            if len(frame.shape) == 3 and frame.shape[2] == 2:
                clean_frame = frame[:, :, 0]
            elif len(frame.shape) == 2:
                clean_frame = frame
            else:
                clean_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Resize the 256x192 image so it's large enough to see
            display_frame = cv2.resize(clean_frame, (768, 576), interpolation=cv2.INTER_NEAREST)
            
            # CRITICAL ADDITION: Convert the 1-channel grayscale to 3-channel BGR.
            # The image still looks grayscale, but now we can draw red text on it!
            display_frame = cv2.cvtColor(display_frame, cv2.COLOR_GRAY2BGR)

            # If the user has clicked the screen, draw the data
            if clicked_x >= 0 and clicked_y >= 0:
                # 1. Grab the data value from the original, unscaled 256x192 frame
                if clicked_y < clean_frame.shape[0] and clicked_x < clean_frame.shape[1]:
                    value = clean_frame[clicked_y, clicked_x]
                    
                    # 2. Calculate where to draw the UI on the scaled-up display window
                    draw_x = clicked_x * scale_factor
                    draw_y = clicked_y * scale_factor
                    
                    # 3. Draw a red crosshair
                    cv2.drawMarker(display_frame, (draw_x, draw_y), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
                    
                    # 4. Draw the text slightly offset from the crosshair
                    text = f"Val: {value}"
                    cv2.putText(display_frame, text, (draw_x + 10, draw_y - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow(window_name, display_frame)
            
        except Exception as e:
            print(f"Error parsing frame. Raw shape was: {frame.shape} | Error: {e}")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()