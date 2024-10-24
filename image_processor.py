import asyncio
import logging
import torch
import cv2
from PIL import Image
from torchvision.transforms import Compose, Resize, ToTensor
from ultralytics import YOLO  # Assuming YOLOv8
import numpy as np

class CVDetect:
    def __init__(self, frame_queue: asyncio.Queue):
        self.model = YOLO('weights.pt')  # YOLO model for object detection
        self.frame_queue = frame_queue
        
        # Load the MiDaS model for monocular depth estimation
        self.midas_model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
        self.midas_model.eval()  # Set the model to evaluation mode

        # Define the transformation needed for the MiDaS input
        self.transform = Compose([Resize((384, 384)), ToTensor()])
    
    async def detect_screen(self):
        while True:
            img = await self.frame_queue.get()  # Get the image frame from the queue
            
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
                    logging.info(f"Center coordinates: {x_center, y_center}")
                    
                    # Estimate depth using MiDaS model
                    depth_at_center = self.estimate_depth(img, x_center, y_center)
                    logging.info(f"Estimated depth: {depth_at_center} meters")
    
    def estimate_depth(self, img, x_center, y_center):
        """
        Estimate the depth of the object at the given center coordinates (x_center, y_center).
        """
        # Convert the image to the appropriate format for MiDaS
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert to RGB (MiDaS expects RGB)
        img_pil = Image.fromarray(img_rgb)

        # Apply the transformation
        input_tensor = self.transform(img_pil).unsqueeze(0)   # Apply transform and add batch dimension
        
        # Run the depth estimation model
        with torch.no_grad():
            depth_map = self.midas_model(input_tensor)

        # Convert depth map to a NumPy array and squeeze the batch dimension
        depth_map = depth_map.squeeze().cpu().numpy()

        # Resize depth map back to original image dimensions (optional, depending on requirement)
        original_height, original_width, _ = img.shape
        depth_map_resized = cv2.resize(depth_map, (original_width, original_height))

        # Normalize coordinates to ensure they fit within the resized depth map
        x_center = np.clip(x_center, 0, original_width - 1)
        y_center = np.clip(y_center, 0, original_height - 1)
        
        # Get the depth value at the center of the bounding box from the resized depth map
        depth_at_center = depth_map_resized[int(y_center), int(x_center)]
        
        return depth_at_center
