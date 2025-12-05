import game_framework
from pico2d import *
import stage01
import stage02
import stage03
from sdl2 import SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT, SDL_QUIT, SDL_GetMouseState
from ctypes import c_int

image = None
running = True
logo_start_time = 0.0
party = [0,0,0,0]
now_people = 0

# next_stage: None 이면 기본으로 stage01 사용. main_mode가 클릭한 버튼에 따라 여기로 stage 모듈을 설정함.
next_stage = None

def init():
    global image
    global running
    global logo_start_time
    global next_stage
    image = load_image('ui/choice.png')
    running = True
    logo_start_time = get_time()
    # 기본값은 stage01로 설정
    if next_stage is None:
        next_stage = stage01

def finish():
    global image
    del image

def update():
    pass

def draw():
    global party
    clear_canvas()
    image.clip_draw(0, 0, 4380,3504, 500,400, 1000,800)

    # party에 들어있는 숫자만 태두리(강조) 표시
    if check_rec(1):
        draw_rectangle(0, 470, 320, 800)
    if check_rec(6):
        draw_rectangle(0, 130, 320, 470)
    if check_rec(2):
        draw_rectangle(320, 470, 700, 800)
    if check_rec(4):
        draw_rectangle(320, 130, 700, 470)
    if check_rec(3):
        draw_rectangle(700, 470, 1000, 800)
    if check_rec(5):
        draw_rectangle(700, 130, 1000, 470)

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
    global running, now_people, party, next_stage
    events = get_events()
    for event in events:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            # 선택한 스테이지로 start_party 전달 후 해당 스테이지로 전환
            mx, my = _get_mouse_pos_from_event(event)
            # 클릭 영역: (800,0) ~ (920,120) 시작 버튼
            if 800 <= mx <= 920 and 0 <= my <= 120 and now_people == 4:
                target_stage = next_stage if next_stage is not None else stage01
                try:
                    target_stage.start_party = party
                except Exception:
                    # 안전 처리: 무시
                    pass
                # 사용 후 초기화
                next_stage = None
                game_framework.change_mode(target_stage)
            elif 0<= mx <=320 and 470 <= my <=800:
               check_party(now_people, 1)
            elif 0<= mx <=320 and 130 <= my <=470:
               check_party(now_people, 6)
            elif 320<= mx <=700 and 470 <= my <=800:
                check_party(now_people, 2)
            elif 320<= mx <=700 and 130 <= my <=470:
                check_party(now_people, 4)
            elif 700<= mx <=1000 and 470 <= my <=800:
                check_party(now_people, 3)
            elif 700<= mx <=1000 and 130 <= my <=800:
                check_party(now_people, 5)
            print(f'now_people: {now_people}, party: {party}')

def check_party(m, num):
    global now_people
    for i in range(4):
        if party[i] == num:
            party[i]=0
            now_people -= 1
            return
    for i in range(4):
        if party[i] == 0 and now_people <4:
            party[i] = num
            now_people += 1
            return

def check_rec(num):
    for i in range(4):
        if party[i] == num:
            return True
    return False