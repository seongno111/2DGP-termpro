import game_framework
from pico2d import *
import main_mode
from sdl2 import SDL_QUIT

image = None
running = True
logo_start_time = 0.0

def init():
    global image
    global running
    global logo_start_time
    image = load_image('ui/back.png')
    running = True
    logo_start_time = get_time()

def finish():
    global image
    del image

def update():
    global logo_start_time
    if get_time() - logo_start_time >= 2.0:
        logo_start_time = get_time()
        game_framework.change_mode(main_mode)

def draw():
    clear_canvas()
    image.clip_draw(0, 0, 87,82, 500,400, 1000,800)
    update_canvas()

def handle_events():
    global running
    events = get_events()
    for event in events:
        if event.type == SDL_QUIT:
            running = False
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
            game_framework.quit()
        # 로고 화면은 나머지 입력은 무시하고 자동으로 main_mode로 넘어감
