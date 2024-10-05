import sys
import termios
import tty

def get_key():
    """Read a single key press from stdin."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

class Key_binds:
    def __init__(self):
        self.yaw_factor = 0
        self.trottle_factor = 0
        self.pitch_factor, self.roll_factor = 0, 0
        
    def yaw_keyboard_controll(self):
        yaw = ord(get_key())
        match yaw:
            case 113:
                self.yaw_factor = -45
            case 101:
                self.yaw_factor = 45
        return self.yaw_factor
    
    def roll_pitch_keyboard_controll(self):
        pitch_roll = ord(get_key())
        match pitch_roll:
            case 119:
                self.pitch_factor = 45
            case 97:
                self.roll_factor = -45
            case 115:
                self.pitch_factor = -45
            case 100:
                self.roll_factor = 45
        return  self.pitch_factor, self.roll_factor
    
    def trottle_keyboard_controll(self):
        trottle = ord(get_key())
        match trottle:
            case 32:
                self.trottle_factor = 1
        return self.trottle_factor

    def exit(self):
        if ord(get_key()) == 27:
            return False
        return True