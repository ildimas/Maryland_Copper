import os
import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from PIL import Image
from selenium.webdriver.common.by import By
import io
import time
import logging
import asyncio

class Webrtc_parser:
    def __init__(self, frame_queue: asyncio.Queue):
        self.is_active = True 
        self.fq = frame_queue
        logging.info("initial pixi")
    async def main(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run headless for no browser window
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        user_home_dir = os.path.expanduser("~")
        chrome_binary_path = os.path.join(user_home_dir, "chrome-linux64", "chrome")
        chromedriver_path = os.path.join(user_home_dir, "chromedriver-linux64", "chromedriver")

        chrome_options.binary_location = chrome_binary_path
        service = Service(chromedriver_path)
        logging.info("pre browser pixi")
        with webdriver.Chrome(service=service, options=chrome_options) as browser:
            
            browser.get("http://192.168.96.1:80")
            logging.info("page getted pixi")
            video_element = browser.find_element(By.ID, "connectButton")
            video_element.click()  
            logging.info("waiting... pixi")
            await asyncio.sleep(5)
            logging.info("starting loop pixi")
            while self.is_active:
                screenshot = browser.get_screenshot_as_png()
                image = Image.open(io.BytesIO(screenshot))
                frame = np.array(image)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                await self.fq.put(frame)
                logging.info("Frame is in queue")
                await asyncio.sleep(0.01)
                
    async def stop(self):
        self.is_active = False
        logging.info("Active stopped")
        
if __name__ == "__main__":
    y = asyncio.Queue(1000000)
    x = Webrtc_parser(y)
    x.main()
    