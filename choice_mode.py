import game_framework
from pico2d import *
import play_mode

image = None
running = True
logo_start_time = 0.0

def init():
    global image
    global running
    global logo_start_time
    image = load_image('choice.png')
    running = True
    logo_start_time = get_time()

def finish():
    global image
    del image

def update():

   pass

def draw():
    clear_canvas()
    image.clip_draw(0, 0, 4380,3504, 500,400, 1000,800)
    draw_rectangle(0,130,320,800)
    draw_rectangle(0, 470, 320, 800)

    draw_rectangle(320, 130, 700, 800)
    draw_rectangle(320, 470, 700, 800)

    draw_rectangle(700, 130, 1000, 800)
    draw_rectangle(700, 470, 1000, 800)
    update_canvas()

def handle_events():
    # 현재 이벤트들을 소비
    events = get_events()