import cv2
import numpy as np
import subprocess as sp

# --- CONFIGURATION ---
# Replace this with the exact name output by the ffmpeg -list_devices command
CAMERA_NAME = "Topdon TC001" 
SCALE_FACTOR = 3  

clicked_x = -1
clicked_y = -1

def mouse_callback(event, x, y, flags, param):
    global clicked_x, clicked_y
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_x = x // SCALE_FACTOR
        clicked_y = y // SCALE_FACTOR

def main():
    # The exact command to rip the raw 256x384 yuyv422 stream bypassing Windows color-correction
    command = [
        'ffmpeg',
        '-hide_banner',
        '-loglevel', 'error',       # Suppress ffmpeg console spam
        '-f', 'dshow',              # Windows DirectShow input
        '-video_size', '256x384',   # Force the double-height payload
        '-pixel_format', 'yuyv422', # Force the raw pixel format
        '-i', f'video={CAMERA_NAME}',
        '-f', 'image2pipe',         # Pipe the output directly to Python
        '-pix_fmt', 'yuyv422',      # Maintain the raw format in the pipe
        '-vcodec', 'rawvideo',      # Do not compress the stream
        '-'                         # Output to stdout
    ]

    print(f"Launching FFmpeg to capture raw stream from '{CAMERA_NAME}'...")
    
    # Launch the process
    try:
        pipe = sp.Popen(command, stdout=sp.PIPE, stderr=sp.DEVNULL, bufsize=10**8)
    except FileNotFoundError:
        print("ERROR: ffmpeg is not installed or not in your system PATH.")
        return

    window_name = "Topdon TC001 - FFmpeg Raw Pipe"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback)

    print("Success! Data pipe open. Click anywhere for temperatures.")

    # A 256x384 YUYV422 frame is exactly 2 bytes per pixel
    bytes_per_frame = 256 * 384 * 2 

    while True:
        try:
            # Read exactly one frame's worth of bytes directly from the ffmpeg pipe
            raw_bytes = pipe.stdout.read(bytes_per_frame)
            
            if len(raw_bytes) != bytes_per_frame:
                print("Stream ended or camera disconnected.")
                break

            # 1. Fold the raw bytes into the 384x256x2 matrix
            frame = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((384, 256, 2))

            # 2. Extract the Visual Image (Top 192 rows, 1st byte of the YUYV pair is Luminance)
            video_half = frame[0:192, :, 0]

            # Normalize for crisp white-hot / black-cold YOLO contrast
            normalized_visual = cv2.normalize(video_half, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            display_frame = cv2.resize(normalized_visual, (256 * SCALE_FACTOR, 192 * SCALE_FACTOR), interpolation=cv2.INTER_NEAREST)
            display_frame = cv2.cvtColor(display_frame, cv2.COLOR_GRAY2BGR)

            # 3. Extract the Telemetry (Bottom 192 rows)
            telemetry_half = frame[192:384, :, :]
            
            # Use the exact 16-bit Little-Endian casting method from the forum
            temp_data_16bit = telemetry_half.copy().view(np.uint16).reshape(192, 256)

            # 4. Handle Mouse Clicks and Temperature Math
            if clicked_x >= 0 and clicked_y >= 0:
                if clicked_y < 192 and clicked_x < 256:
                    
                    # Grab the 16-bit combined high/low value
                    raw_val = temp_data_16bit[clicked_y, clicked_x]
                    
                    # Apply the LeoDJ InfiRay formula
                    celsius = (raw_val / 64.0) - 273.15
                    fahrenheit = (celsius * 1.8) + 32.0
                    
                    draw_x = clicked_x * SCALE_FACTOR
                    draw_y = clicked_y * SCALE_FACTOR
                    
                    cv2.drawMarker(display_frame, (draw_x, draw_y), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
                    text = f"{celsius:.1f} C / {fahrenheit:.1f} F"
                    cv2.putText(display_frame, text, (draw_x + 10, draw_y - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow(window_name, display_frame)

            # Important: When piping data, we use a very short waitKey to keep the buffer empty
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        except Exception as e:
            print(f"Pipeline error: {e}")
            break

    # Cleanup
    pipe.terminate()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()