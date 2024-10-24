from ultralytics import YOLO
import asyncio
import logging
import cv2
class CVDetect:
    def __init__(self, frame_queue : asyncio.Queue):
        self.model = YOLO('weights.pt')
        self.frame_queue = frame_queue
        
        # self.error_y = 0.0
        # self.error_x = 0.0
        # self.isZone = True
    
    async def detect_screen(self):
        while True:
            img = await self.frame_queue.get()
            
            # Run YOLO detection on the image
            results = self.model(img)
            
            # Extract the first result (since we're processing one frame at a time)
            result = results[0]
            
            # Get the boxes, classes, and confidences
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                class_name = self.model.names[class_id]
                conf = float(box.conf)  # Confidence score
                xyxy = box.xyxy.cpu().numpy().flatten()
                x_center = (xyxy[0] + xyxy[2]) / 2
                y_center = (xyxy[1] + xyxy[3]) / 2
                if class_name == 'safe-landing-zone':
                    # Log or print the detected information
                    logging.info(f"Detected class: {class_name} with confidence: {conf}")
                    logging.info(f"center coordinates {x_center, y_center}")
                    # If you only want to log object class and coordinates:
                