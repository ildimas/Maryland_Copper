from time import sleep

from dualsense_controller import DualSenseController

class DSControl:
    def __init__(self):
        device_infos = DualSenseController.enumerate_devices()
        if len(device_infos) < 1:
            raise Exception('No DualSense Controller available.')
        self.is_running = True
        self.controller = DualSenseController()
        self.controller.activate()

    def stop(self):
        self.is_running = False
        self.controller.deactivate()

    def get_value(value):
        return value        
    
    
