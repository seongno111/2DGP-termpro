from pico2d import *

stage = [1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1]

open_canvas()

class Tile:
    image_first = None
    image_second = None
    def __init__(self):
        if self.image_first is None and self.image_second is None:
            self.image_first = load_image('ground.png')
            self.image_second = load_image('floor_nd.png')
    def draw(self, stage):
        for i in range(12):
            if stage[i] == 1:
                self.image_first.clip_draw(0, 0, 32, 32, i*32+16, 16)
            elif stage[i] == 2:
                self.image_second.clip_draw(0, 0, 32, 32, i*32+16, 16)

tile_map = Tile()

while True:
    clear_canvas()
    tile_map.draw(stage)
    update_canvas()


