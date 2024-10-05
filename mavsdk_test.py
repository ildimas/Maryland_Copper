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
        logging.info("Arming the drone...")
        await self.drone.action.arm()
        
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
            
if __name__ == "__main__":
    async def main():
        x = DroneControls(keyboard_mode=True, connection_string="udp://0.0.0.0:14540")
        await x.connect_to_px4()
        # await x.manual_gamepad_mode()
        await x.manual_keyboard_mode()
    asyncio.run(main())
