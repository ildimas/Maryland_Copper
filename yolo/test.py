import cv2
from ultralytics import YOLO
from mss import mss
import numpy as np

# Load the YOLO model (specify the path to your weights file)
model = YOLO('weights.pt')

# Set up screen capture using mss
sct = mss()
monitor = sct.monitors[1]  # Assuming you want to capture the first monitor; adjust if needed

# Define the function to capture screen and process with YOLO
def detect_screen():
    while True:
        # Capture screen data
        sct_img = sct.grab(monitor)

        # Convert the captured screen to a NumPy array (RGB format)
        img = np.array(sct_img)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # Pass the image to the YOLO model and get results
        results = model(img)

        # Draw bounding boxes and labels on the image
        annotated_img = results[0].plot()

        # Display the result in a separate window
        cv2.imshow('YOLOv8 Detection', annotated_img)

        # Break the loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_screen()
