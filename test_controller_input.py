from time import sleep

from dualsense_controller import DualSenseController

device_infos = DualSenseController.enumerate_devices()
if len(device_infos) < 1:
    raise Exception('No DualSense Controller available.')

is_running = True
controller = DualSenseController()

def stop():
    global is_running
    is_running = False

def on_cross_btn_pressed():
    print('cross button pressed')
    controller.left_rumble.set(255)
    controller.right_rumble.set(255)
    
def on_cross_btn_released():
    print('cross button released')
    controller.left_rumble.set(0)
    controller.right_rumble.set(0)

def on_square_btn_pressed():
    print('square button pressed')
    controller.left_rumble.set(255)
    controller.right_rumble.set(255)
    
def on_square_btn_released():
    print('square button released')
    controller.left_rumble.set(0)
    controller.right_rumble.set(0)

def on_ps_btn_pressed():
    print('PS button released -> stop')
    stop()

def on_error(error):
    print(f'Opps! an error occured: {error}')
    stop()


def on_analog(value):
    print("ЙОУ", value)
    
    
def on_left_triger(value):
    print(f"Йоу тригер {value}")

# register the button callbacks
controller.btn_cross.on_down(on_cross_btn_pressed)
controller.btn_cross.on_up(on_cross_btn_released)
controller.btn_ps.on_down(on_ps_btn_pressed)
controller.btn_square.on_down(on_square_btn_pressed)
controller.btn_square.on_up(on_square_btn_released)
controller.left_stick.on_change(on_analog)
controller.left_trigger.on_change(on_left_triger)




# register the error callback
controller.on_error(on_error)

# enable/connect the device
controller.activate()

# start keep alive loop, controller inputs and callbacks are handled in a second thread
while is_running:
    sleep(0.001)

# disable/disconnect controller device
controller.deactivate()