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

tile_map = Tile()
open_canvas(1000,800)
while True:
    clear_canvas()
    tile_map.draw(stage)
    update_canvas()

close_canvas()
