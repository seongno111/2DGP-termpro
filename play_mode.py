from pico2d import *

import game_world
from Knight import *
from Tile import Tile
import game_framework

stage_temp = [2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,1, 1, 1, 1, 1, 1, 1, 1,1,1
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2]

def handle_events():
    global running

    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False


def init():
    tile = []
    for i in range(len(stage_temp)):
        tile.append(Tile(i, stage_temp[i]-1))
        game_world.add_object(tile[i], stage_temp[i]-1)




def update():
   game_world.update()


def draw():
    clear_canvas()
    game_world.render()
    update_canvas()


