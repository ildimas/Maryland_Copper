# main.py
import multiprocessing
from pixelstream import Webrtc_parser
from mavsdk_test import *
import logging

if __name__ == '__main__':
    
    frame_queue = asyncio.Queue()

    async def main():
        mavsdk = DroneControls(connection_string="udp://0.0.0.0:14540", frame_queue=frame_queue, gamepad_mode=True)
        await mavsdk.connect_to_px4()
        await mavsdk.manual_gamepad_mode()
        
    async def pixel():
        pixell =  Webrtc_parser(frame_queue=frame_queue)
        await pixell.main()
    
    async def main_loop():
        await asyncio.gather(
            main(),
            pixel()
        )

    asyncio.run(main_loop())