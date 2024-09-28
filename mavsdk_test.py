from mavsdk import System
from mavsdk.offboard import OffboardError, Attitude, PositionNedYaw
import asyncio
from time import sleep
from dualsense_controller import DualSenseController

def on_left_triger(value):
    print(f"Йоу тригер {value}")
    return value

def stop():
    global is_manual_mode
    is_manual_mode = False
    
def on_ps_btn_pressed():
    print('PS button released -> stop')
    stop()

def yaw_picker(bool1 : bool, bool2 : bool):
    if bool1 == bool2:
        return 0.0
    elif bool1 == True and bool2 == False:
        return 45.0
    else:
        return -45.0
    
def pitch_roll_picker(float_x : float, float_y : float):
    return float_x * -45, float_y * 45


async def connect_to_px4():
    is_manual_mode = False
    drone = System()
    await drone.connect(system_address="udp://0.0.0.0:14540")
    
    async for state in drone.core.connection_state():
        print(f"Drone connected: {state}")
        break
    
    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone connected!")
            break


    # Arm the drone
    print("Arming the drone...")
    await drone.action.arm()

    # Start offboard mode
    print("Starting offboard mode...")
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))
    try:
        await drone.offboard.start()
        device_infos = DualSenseController.enumerate_devices()
        if len(device_infos) < 1:
            raise Exception('No DualSense Controller available.')
        is_manual_mode = True
        controller = DualSenseController()

    except OffboardError as e:
        print(f"Offboard mode failed to start: {e._result.result}")
        print("Disarming the drone...")
        await drone.action.disarm()
        return

    print("Offboard mode started")

    try:
        controller.activate()
        while is_manual_mode:
            
            controller.btn_ps.on_down(on_ps_btn_pressed)
            
            pitch_deg, roll_deg = pitch_roll_picker(float(controller.left_stick.value.y), float(controller.left_stick.value.x))
            yaw_deg = yaw_picker(controller.btn_r1._get_value(), controller.btn_l1._get_value())
            thrust_value = controller.right_trigger.value  
            print("TV", thrust_value)
            print("LRL",controller.btn_l1._get_value(), controller.btn_r1._get_value())
            print("LS", controller.left_stick.value.x, controller.left_stick.value.y )
            
            
            await drone.offboard.set_attitude(Attitude(roll_deg=roll_deg, pitch_deg=pitch_deg, yaw_deg=yaw_deg, thrust_value=thrust_value))
            await asyncio.sleep(0.01)  
            
        controller.deactivate()
    except OffboardError as e:
        print(f"Failed to send offboard commands: {e._result.result}")

    # Stop offboard mode
    print("Stopping offboard mode...")
    try:
        await drone.offboard.stop()
    except OffboardError as e:
        print(f"Offboard mode failed to stop: {e._result.result}")

    # Disarm the drone
    print("Disarming the drone...")
    await drone.action.disarm()

asyncio.run(connect_to_px4())