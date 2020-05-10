from evdev import UInput, ecodes as e


class Mouse:
    def __init__(self, start, mul):
        cap = {
            e.EV_REL: (e.REL_X, e.REL_Y),
            e.EV_KEY: (e.BTN_LEFT, e.BTN_RIGHT),
        }
        self.ui = UInput(cap)  # , name='Microsoft X-Box pad v1 (US)', product=0x0202, vendor=0x045e)
        self.prev = start
        self.mul = mul

    def callback(self, data):
        euler = data['eulerData']
        self.ui.write(e.EV_REL, e.REL_X, int((euler[0] - self.prev[0]) * self.mul[0]))
        self.ui.write(e.EV_REL, e.REL_Y, int((euler[1] - self.prev[1]) * self.mul[1]))

        self.ui.write(e.EV_KEY, e.BTN_LEFT, data['trigger'] == 2)
        self.ui.write(e.EV_KEY, e.BTN_RIGHT, data['trigger'] == 4)

        self.prev = data
        self.ui.syn()
