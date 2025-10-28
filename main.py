from pico2d import *
from Knight import *
from Tile import Tile

stage_temp = [2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,1, 1, 2, 2, 2, 2, 2, 2,1,1
             ,2, 1, 1, 1, 1, 1, 1, 1,1,2
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
        else:
            knight.handle_event(event)



def reset_stage():
    global stage
    global knight
    stage = []

    tile = Tile()
    stage.append(tile)

    knight = Knight()
    stage.append(knight)
    stage[1].set_number(1)


def update_stage():
    for o in stage:
        o.update()
    pass


def render_stage():
    clear_canvas()
    stage[0].draw(stage_temp)
    stage[1].draw()
    update_canvas()
    pass

running = True

open_canvas(1000,800)
reset_stage()

while running:
    handle_events()
    update_stage()
    render_stage()
    delay(0.01)

close_canvas()
