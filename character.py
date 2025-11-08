from pico2d import *
from sdl2 import SDL_BUTTON_LEFT, SDL_MOUSEBUTTONDOWN
from state_machine import StateMachine

def left_m_down(e):
    return e[0] == 'INPUT' and e[1].type == SDL_MOUSEBUTTONDOWN and e[1].button == SDL_BUTTON_LEFT

def mouse_pos_poll():
    """폴링으로 현재 마우스 위치 얻기"""
    x = c_int()
    y = c_int()
    SDL_GetMouseState(x, y)
    mx, my = x.value, y.value
    # 필요하면 Y 반전
    try:
        canvas_h = get_canvas_height()
        my = canvas_h - my
    except Exception:
        pass
    return mx, my

class Decide:
    def __init__(self, character):
        self.character = character
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        pass
    def draw(self):
        self.character.draw()

class Place:
    def __init__(self, character):
        self.character = character
    def enter(self, e):
        print('Placing State Entered')
        pass
    def exit(self, e):
        pass
    def do(self):
        pass
    def draw(self):
        self.character.draw()

class Idle:
    def __init__(self, character):
        self.character = character
    def enter(self, e):
        pass
    def exit(self, e):
        print(mouse_pos_poll())
    def do(self):
        pass
    def draw(self):
        self.character.draw()


class Character:
    k_p_image = None
    ch_num = 0
    placing = False

    def __init__(self):
        self.p_y = 50
        self.k_p_x = 50
        if self.k_p_image is None:
            self.k_p_image = load_image('Knight_portrait.png')

        self.IDLE = Idle(self)
        self.PLACING = Place(self)
        self.DECIDE = Decide(self)
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {
                    left_m_down: self.IDLE
                },
                self.PLACING: {},
                self.DECIDE: {},
            }
        )

    def update(self):
        pass

    def draw(self):
        self.k_p_image.clip_draw(0, 0, 1022, 1022, self.k_p_x, self.p_y, 100, 100)

    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))
