import cv2
import numpy as np

# Open camera (change index if needed)
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

# IMPORTANT: disable RGB conversion (keeps raw thermal data intact)
cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # Split frame into image + thermal data
    imdata, thdata = np.array_split(frame, 2)

    # Pick a pixel (example: center)
    y, x = 96, 128

    # Extract raw 16-bit value (stored as two 8-bit channels)
    hi = int(thdata[y][x][0])
    lo = int(thdata[y][x][1])

    lo = lo * 256
    rawtemp = hi+lo

    # Convert to Celsius
    temp = (rawtemp / 64) - 273.15

    print(f"Temp at ({x},{y}): {temp:.2f} °C")

    # Optional: show normal image for reference
    cv2.imshow("Preview", imdata)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()