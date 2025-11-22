# python
import game_framework
from pico2d import *
import play_mode
from sdl2 import SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT, SDL_QUIT, SDL_GetMouseState
from ctypes import c_int

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

    draw_rectangle(800, 0, 920, 120)
    draw_rectangle(100, 0, 220, 120)
    update_canvas()

def _get_mouse_pos_from_event(ev):
    if ev is None:
        return 0, 0
    # 버튼 속성이 있는 경우 우선 사용
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
            # 클릭 영역: (800,0) ~ (920,120)
            if 800 <= mx <= 920 and 0 <= my <= 120:
                game_framework.change_mode(play_mode)