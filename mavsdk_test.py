from mavsdk import System
from mavsdk.offboard import OffboardError, Attitude, PositionNedYaw, PositionGlobalYaw
from mavsdk.telemetry import EulerAngle
import asyncio
from time import sleep
from dualsense_controller import DualSenseController
from controller_funcs import Controller_funcs
import logging
from keyboard_controll_module import Key_binds
from sshkeyboard import listen_keyboard, stop_listening
from coordinates import *
from mavsdk.camera import (CameraError, Mode)

class DroneControls:
    logging.basicConfig(level=logging.INFO)
    def __init__(self, connection_string, gamepad_mode=False, keyboard_mode=False):
        if gamepad_mode and keyboard_mode:
            raise ValueError("Only one mode can be set to True: either gamepad_mode or keyboard_mode.")
        if not gamepad_mode and not keyboard_mode:
            raise ValueError("At least one mode must be set to True: either gamepad_mode or keyboard_mode.")
        self.gamepad_mode = gamepad_mode
        self.keyboard_mode = keyboard_mode
        self.conn_string = connection_string
        self.manual_mode = False
        self.drone = System()
        
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
                    ned = await self.drone.telemetry.position_velocity_ned().__anext__()
                    current_yaw = await self.drone.telemetry.attitude_euler().__anext__()
                    logging.info(f"{current_yaw}, {type(current_yaw)}")
                    logging.info(f"{ned}, {type(ned)}")
                    current_yaw = current_yaw.yaw_deg
                    self.manual_mode = not controller.btn_ps._get_value()
                    pitch_deg, roll_deg = con_func.pitch_roll_picker(float(controller.left_stick.value.y), float(controller.left_stick.value.x))
                    yaw_deg = current_yaw + con_func.yaw_picker(controller.btn_r1._get_value(), controller.btn_l1._get_value()) 
                    thrust_value = controller.right_trigger.value  
                    logging.info(f"TV {thrust_value}")
                    logging.info(f"LRL {controller.btn_l1._get_value()}, {controller.btn_r1._get_value()}")
                    logging.info(f"LS {controller.left_stick.value.x}, {controller.left_stick.value.y}" )
                    
                    
                    await self.drone.offboard.set_attitude(Attitude(roll_deg=roll_deg, pitch_deg=pitch_deg, yaw_deg=yaw_deg, thrust_value=thrust_value))
                    # drone.offboard.set_position_global(position_global_yaw=PositionGlobalYaw(0.0, 0.0, 0.0, yaw_deg))
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
        print_mode_task = asyncio.ensure_future(self.print_mode(self.drone))
        print_status_task = asyncio.ensure_future(self.print_status(self.drone))
        running_tasks = [print_mode_task, print_status_task]

        print("Setting mode to 'PHOTO'")
        try:
            await self.drone.camera.set_mode(Mode.PHOTO)
        except CameraError as error:
            print(f"Setting mode failed with error code: {error._result.result}")

        await asyncio.sleep(2)

        print("Taking a photo")
        try:
            await self.drone.camera.take_photo()
        except CameraError as error:
            print(f"Couldn't take photo: {error._result.result}")

        # Shut down the running coroutines (here 'print_mode()' and
        # 'print_status()')
        for task in running_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await asyncio.get_event_loop().shutdown_asyncgens()
        #!!!
        await asyncio.sleep(5)
        await self.drone.action.goto_location(latitude_deg=new_latitude, longitude_deg=new_longtitude, absolute_altitude_m=self.absolute_altitude + height, yaw_deg=0)
        while True:
            logging.info(await self.drone.camera.capture_info().__anext__())
            logging.info(await self.drone.camera.current_settings().__anext__())
            #logging.info(f"Широта от начала координат: {position.latitude_deg} \n Долгота от начала координат {position.longitude_deg} \n Высота относительно начала координат {position.relative_altitude_m}")
            
    async def print_mode(self, drone):
        async for mode in drone.camera.mode():
            print(f"Camera mode: {mode}")

    async def print_status(self, drone):
        async for status in drone.camera.status():
            print(status)
        
if __name__ == "__main__":
    async def main():
        x = DroneControls(gamepad_mode=True, connection_string="udp://0.0.0.0:14540")
        await x.connect_to_px4()
        # await x.manual_gamepad_mode()
        # await x.manual_keyboard_mode()
        await x.random_positioning(100, 20)
    asyncio.run(main())


# 47.64138 -122.1400654
# 47.64636 122.13243