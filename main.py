from pico2d import *

from Tile import Tile

stage = [2, 2, 2, 2, 2, 2, 2, 2,2,2
        ,2, 2, 2, 2, 2, 2, 2, 2,2,2
        ,1, 1, 2, 2, 2, 2, 2, 2,1,1
        ,2, 1, 1, 1, 1, 1, 1, 1,1,2
        ,2, 2, 2, 2, 2, 2, 2, 2,2,2
        ,2, 2, 2, 2, 2, 2, 2, 2,2,2
        ,2, 2, 2, 2, 2, 2, 2, 2,2,2
        ,2, 2, 2, 2, 2, 2, 2, 2,2,2]
def reset_stage():
    pass


def update_stage():
    pass


def render_stage():
    pass

open_canvas(1000,800)
reset_stage()
tile_map = Tile()
while True:
    clear_canvas()
    update_stage()
    tile_map.draw(stage)
    render_stage()
    delay(0.01)

close_canvas()
