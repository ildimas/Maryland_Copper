class Controller_funcs:
    def __init__(self):
        pass

    def yaw_picker(self, bool1 : bool, bool2 : bool):
        if bool1 == bool2:
            return 0.0
        elif bool1 == True and bool2 == False:
            return 25
        else:
            return -25

    def pitch_roll_picker(self, float_x : float, float_y : float):
        return float_x * -45, float_y * 45