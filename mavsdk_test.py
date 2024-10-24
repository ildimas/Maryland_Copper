from mavsdk import System
from mavsdk.offboard import OffboardError, Attitude, PositionNedYaw, VelocityBodyYawspeed
import asyncio
from dualsense_controller import DualSenseController
from controller_funcs import Controller_funcs
import logging
from keyboard_controll_module import Key_binds
from coordinates import *
from mavsdk.camera import (CameraError, Mode)
import cv2
from ultralytics import YOLO
from multiprocessing import Queue
from mss import mss
import numpy as np

class DroneControls:
    logging.basicConfig(level=logging.INFO)
    def __init__(self, connection_string, frame_queue : Queue, gamepad_mode=False, keyboard_mode=False, ):
        if gamepad_mode and keyboard_mode:
            raise ValueError("Only one mode can be set to True: either gamepad_mode or keyboard_mode.")
        if not gamepad_mode and not keyboard_mode:
            raise ValueError("At least one mode must be set to True: either gamepad_mode or keyboard_mode.")
        self.gamepad_mode = gamepad_mode
        self.keyboard_mode = keyboard_mode
        self.conn_string = connection_string
        self.manual_mode = False
        self.drone = System()
        self.pid_x = PIDController(Kp=0.1, Ki=0.0, Kd=0.05)
        self.pid_y = PIDController(Kp=0.1, Ki=0.0, Kd=0.05)
        self.error_x = 0.0
        self.error_y = 0.0
        self.cv = CVDetect(frame_queue)
        self.alignment_event = asyncio.Event()
        self.alignment_active = False
        self.x_threshold = 320
        self.y_threshold = 160
        self.state = "horizontal_alignment"
        self.controls = [0.0, 0.0, 0.0, 0.0]
        
    async def connect_to_px4(self):
        logging.info("connetcting...")
        await self.drone.connect(system_address=self.conn_string)
        async for state in self.drone.core.connection_state():
            logging.info(f"Drone connected: {state}")
            break
        
        try:
            logging.info("Starting video stream...")
            await self.drone.camera.start_video_streaming(stream_id=0)
            print("Video streaming started.")
        except Exception as e:
            logging.info(f"Failed to start video streaming: {e}")
        
        logging.info("Waiting for drone to have a global position estimate...")
        async for health in self.drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                logging.info("-- Global position state is good enough for flying.")
                break

        logging.info("Fetching amsl altitude at home location....")
        async for terrain_info in self.drone.telemetry.home():
            self.absolute_altitude = terrain_info.absolute_altitude_m
            self.absolute_longtitute = terrain_info.longitude_deg
            self.absolute_latitude = terrain_info.latitude_deg
            break

        logging.info("Arming the drone...")
        await self.drone.action.arm()
        self.is_armed = True
        
    async def _safe_start_offboard(self):
        try:
            await self.drone.offboard.start()
            self.manual_mode = True
            logging.info("Offboard mode started")
        except OffboardError as e:
            logging.info(f"Offboard mode failed to start: {e._result.result}")
            
    async def _safe_stop_offboard(self):
        logging.info("Stopping offboard mode...")
        try:
            await self.drone.offboard.stop()
            self.manual_mode = False
        except OffboardError as e:
            logging.info(f"Offboard mode failed to stop: {e._result.result}")
                
    async def manual_gamepad_mode(self):
        await self.drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))
        await self._safe_start_offboard()
        if self.gamepad_mode and self.manual_mode:
            
            device_infos = DualSenseController.enumerate_devices()
            if len(device_infos) < 1:
                raise Exception('No DualSense Controller available.')   
            else:
                logging.info("DualSense Controller founded !!!")
                controller = DualSenseController() 
            logging.info("Starting manual gamepad mode...")
            con_func = Controller_funcs()
            try:
                controller.activate()
                while self.manual_mode:
                    
                    if controller.btn_ps._get_value():
                            self.alignment_active = not self.alignment_active
                            await asyncio.sleep(0.2)
                            
                    if self.alignment_active:
                        await self.autonomous_alignment()
                    else:
                        ned = await self.drone.telemetry.position_velocity_ned().__anext__()
                        current_yaw = await self.drone.telemetry.attitude_euler().__anext__()
                        #! logging.info(f"{current_yaw}, {type(current_yaw)}")
                        #! logging.info(f"{ned}, {type(ned)}")
                        current_yaw = current_yaw.yaw_deg
                        
                        
                            
                        
                        pitch_deg, roll_deg = con_func.pitch_roll_picker(float(controller.left_stick.value.y), float(controller.left_stick.value.x))
                        yaw_deg = current_yaw + con_func.yaw_picker(controller.btn_r1._get_value(), controller.btn_l1._get_value()) 
                        thrust_value = controller.right_trigger.value
                        logging.info(f"TV {thrust_value}")
                        #! logging.info(f"LRL {controller.btn_l1._get_value()}, {controller.btn_r1._get_value()}")
                        #! logging.info(f"LS {controller.left_stick.value.x}, {controller.left_stick.value.y}" )
                        
                        await self.drone.offboard.set_attitude(Attitude(roll_deg=roll_deg, pitch_deg=pitch_deg, yaw_deg=yaw_deg, thrust_value=thrust_value))
                    await asyncio.sleep(0.01)  
                    
                controller.deactivate()
                self._safe_stop_offboard()
                logging.info("Manual gamepad controll stoped")
            except OffboardError as e:
                logging.warning(f"Failed to send offboard commands: {e._result.result}")  
        else:
            logging.warning("The manual gamepad mode was used without gamepad_mode setted")
            
    async def manual_keyboard_mode(self):
        await self.drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))
        await self._safe_start_offboard()
        if self.keyboard_mode and self.manual_mode:
            try:
                keyboard = Key_binds()
                while self.manual_mode:
                    self.manual_mode = keyboard.exit()
                    ned = await self.drone.telemetry.position_velocity_ned().__anext__()
                    current_yaw = await self.drone.telemetry.attitude_euler().__anext__()
                    logging.info(f"{current_yaw}, {type(current_yaw)}")
                    logging.info(f"{ned}, {type(ned)}")
                    pitch_deg, roll_deg = keyboard.roll_pitch_keyboard_controll()
                    yaw_deg = keyboard.yaw_keyboard_controll()
                    thrust_value = keyboard.trottle_keyboard_controll()
                    await self.drone.offboard.set_attitude(Attitude(roll_deg=roll_deg, pitch_deg=pitch_deg, yaw_deg=yaw_deg, thrust_value=thrust_value))
                    await asyncio.sleep(0.01)  
                self._safe_stop_offboard()
                logging.info("Manual keyboard controll stoped")
            except OffboardError as e:
                logging.warning(f"Failed to send offboard commands: {e._result.result}")  
        else:
            logging.warning("The manual keyboard mode was used without keyboard_mode setted")
            
    async def random_positioning(self, height, angle):
        print(self.absolute_altitude, self.absolute_latitude, self.absolute_longtitute)
        logging.info("Start positioning")
        new_latitude, new_longtitude = get_coordinates(self.absolute_latitude, self.absolute_longtitute, pifagor_triangle_distance(height=height))
        await self.drone.action.takeoff()
        #!!!
        #!!!
        await asyncio.sleep(5)
        await self.drone.action.goto_location(latitude_deg=new_latitude, longitude_deg=new_longtitude, absolute_altitude_m=self.absolute_altitude + height, yaw_deg=0)
        while True:
            logging.info(await self.drone.camera.capture_info().__anext__())
            logging.info(await self.drone.camera.current_settings().__anext__())
            #logging.info(f"Широта от начала координат: {position.latitude_deg} \n Долгота от начала координат {position.longitude_deg} \n Высота относительно начала координат {position.relative_altitude_m}")
    
    async def autonomous_alignment(self):
        self.error_x, self.error_y, isZone = await self.cv.detect_screen()
        
        dt = 0.05
        # logging.info(await self.drone.telemetry.altitude().__anext__())
        alt = await self.drone.telemetry.altitude().__anext__()
        if abs(self.error_x) < 10:
            self.state = 'approaching'
        
        if isZone:
            if self.state == 'horizontal_alignment':
                if self.error_x < 0:
                    self.controls = [0.0, 0.0, 0.0, -10.0]
                elif self.error_x > 0:
                    self.controls = [0.0, 0.0, 0.0, 10.0]
            elif self.state == 'approaching':
                if alt.altitude_local_m < 8:
                    self.controls = [4.0, 0.0, 1.0, 0.0]
                    self.state = 'landing'
                    dt = 2.0 
                elif self.error_x < 0:
                    self.controls = [15.0, 0.0, 30.0, -10.0]
                elif self.error_x > 0:
                    self.controls = [15.0, 0.0, 30.0, 10.0]
                dt = 0.5
            elif self.state == 'landing':
                await self.drone.action.land()
        else:
            self.controls = [0.0, 0.0, 0.0, 30.0]
        
        logging.info(self.controls)
        await self.drone.offboard.set_velocity_body(
            velocity_body_yawspeed=VelocityBodyYawspeed(*self.controls)
        )
        
        await asyncio.sleep(dt)

class CVDetect:
    def __init__(self, frame_queue : asyncio.Queue):
        self.model = YOLO('weights.pt')
        self.frame_queue = frame_queue
        self.error_y = 0.0
        self.error_x = 0.0
        self.isZone = True 
    
    async def detect_screen(self):
        if not self.frame_queue.empty():
            img = await self.frame_queue.get()
            errors = await self.process_image(img)
            if errors:
                min_error = min(errors, key=lambda e: (e[0]**2 + e[1]**2)**0.5)
                self.error_x, self.error_y = min_error
                self.isZone = True 
            else:
                self.error_x, self.error_y = 0.0, 0.0
                self.isZone = False
        return self.error_x, self.error_y, self.isZone
        
    async def process_image(self, img):
        results = self.model(img)
        detections = results[0].boxes
        
        errors = []
        
        for detection in detections:
            
            x1, y1, x2, y2 = detection.xyxy[0]
            
            class_id = int(detection.cls[0])
            class_name = self.model.names[class_id]
            
            if class_name == 'safe-landing-zone':
                logging.info("Safe zone detected !!!")
                bbox_center_x = (x1 + x2) / 2
                bbox_center_y = (y1 + y2) / 2
                
                img_center_x = img.shape[1] / 2
                img_center_y = img.shape[0] / 2
                logging.info(f"x: {img_center_x}, y: {img_center_y}, y_end: {img.shape[0]}")
                error_x = bbox_center_x - img_center_x
                error_y = bbox_center_y - img_center_y
                
                errors.append([error_x, error_y])
        
        return errors

class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint=0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.integral = 0
        self.previous_error = 0

    def compute(self, measurement, dt):
        error = self.setpoint - measurement
        self.integral += error * dt
        derivative = (error - self.previous_error) / dt if dt > 0 else 0
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        self.previous_error = error
        return output

if __name__ == "__main__":
    async def main():
        x = DroneControls(gamepad_mode=True, connection_string="udp://0.0.0.0:14540")
        await x.connect_to_px4()
        await x.manual_gamepad_mode()
        # await x.manual_keyboard_mode()
        # await x.random_positioning(100, 20)
    asyncio.run(main())