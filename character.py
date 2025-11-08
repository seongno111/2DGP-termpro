from pico2d import *

class Character:
    k_p_image = None
    ch_num = 0
    def __init__(self):
        self.p_y = 50
        self.k_p_x = 50
        if self.k_p_image is None:
            self.k_p_image = load_image('Knight_portrait.png')
    def update(self):
        pass

    def draw(self):
        self.k_p_image.clip_draw(0, 0, 1022, 1022, self.k_p_x, self.p_y, 100, 100)
