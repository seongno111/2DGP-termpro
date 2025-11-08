from pico2d import *
from sdl2 import SDL_BUTTON_LEFT, SDL_MOUSEBUTTONDOWN
from state_machine import StateMachine

def left_m_down(e):
    return e[0] == 'INPUT' and e[1].type == SDL_MOUSEBUTTONDOWN and e[1].button == SDL_BUTTON_LEFT

def left_m_up(e):

    return e[0] == 'INPUT' and e[1].type == SDL_MOUSEBUTTONUP and e[1].button == SDL_BUTTON_LEFT

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
        if left_m_down(e):
            self.character.check()
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

        def _left_up_if_placing(e):
            if left_m_up(e) and self.placing:
                # 한 번 전이시키고 플래그 리셋
                self.placing = False
                return True
            return False

        self.IDLE = Idle(self)
        self.PLACING = Place(self)
        self.DECIDE = Decide(self)
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {
                    left_m_down: self.IDLE,
                    _left_up_if_placing: self.PLACING
                },
                self.PLACING: {},
                self.DECIDE: {},
            }
        )



    def check(self):
        x = c_int()
        y = c_int()
        SDL_GetMouseState(x, y)

        mx, my = x.value, get_canvas_height() - y.value
        if  self.k_p_x - 50 <= mx <= self.k_p_x + 50 and self.p_y - 50 <= my <= self.p_y + 50:
            print('Character clicked!')
            self.ch_num += 1
            print(f'Character number is now: {self.ch_num}')
            self.placing = True

    def update(self):
        pass

    def draw(self):
        self.k_p_image.clip_draw(0, 0, 1022, 1022, self.k_p_x, self.p_y, 100, 100)

    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))
