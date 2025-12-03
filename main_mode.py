import game_framework
from pico2d import *
import choice_mode
import stage01
import stage02
import stage03
from sdl2 import SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT, SDL_QUIT, SDL_GetMouseState
from ctypes import c_int

image = None
running = True
logo_start_time = 0.0

def init():
    global image
    global running
    global logo_start_time
    image = load_image('main_back.png')
    running = True
    logo_start_time = get_time()

def finish():
    global image
    del image

def update():
    pass

def draw():
    clear_canvas()
    image.clip_draw(0, 0, 219,304, 500,400, 1000,800)
    draw_rectangle(500, 100, 600, 200)
    draw_rectangle(450, 400, 550, 500)
    draw_rectangle(400, 600, 500, 700)
    update_canvas()

def _get_mouse_pos_from_event(ev):
    if ev is None:
        return 0, 0
    if hasattr(ev, 'button') and getattr(ev.button, 'x', None) is not None and getattr(ev.button, 'y', None) is not None:
        mx = int(ev.button.x); my_raw = int(ev.button.y)
    elif getattr(ev, 'x', None) is not None and getattr(ev, 'y', None) is not None:
        mx = int(getattr(ev, 'x')); my_raw = int(getattr(ev, 'y'))
    else:
        x = c_int(); y = c_int()
        try:
            SDL_GetMouseState(x, y)
            mx, my_raw = x.value, y.value
        except Exception:
            return 0, 0
    try:
        my = get_canvas_height() - my_raw
    except Exception:
        my = my_raw
    return mx, my

def handle_events():
    global running
    events = get_events()
    for event in events:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            mx, my = _get_mouse_pos_from_event(event)
            # 클릭 영역: x 500~600, y 100~200 -> choice_mode로, 기본적으로 stage01로 이어짐
            if 500 <= mx <= 600 and 100 <= my <= 200:
                choice_mode.next_stage = stage01
                game_framework.change_mode(choice_mode)
            # 클릭 영역: x 450~550, y 400~500 -> choice_mode로, 이후 stage02로 이어지게 설정
            elif 450 <= mx <= 550 and 400 <= my <= 500:
                choice_mode.next_stage = stage02
                game_framework.change_mode(choice_mode)
            elif 400 <= mx <= 500 and 600 <= my <= 700:
                choice_mode.next_stage = stage03
                game_framework.change_mode(choice_mode)