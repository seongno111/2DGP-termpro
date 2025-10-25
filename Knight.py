from pico2d import load_image
from sdl2 import SDL_KEYDOWN, SDLK_SPACE, SDLK_RIGHT, SDL_KEYUP, SDLK_LEFT, SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT

from state_machine import StateMachine

def m_right_down(e):
    return e[0] == 'INPUT' and e[1].type == SDL_MOUSEBUTTONDOWN and e[1].key == SDL_BUTTON_LEFT

class Non_appear:
    def __init__(self, knight):
        self.knight = knight
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        pass
    def draw(self):
        self.knight.p_image.clip_draw(0, 0, 1022, 1022, self.knight.p_x, self.knight.p_y, 100, 100)
        pass

class Idle:
    def __init__(self, knight):
        self.knight = knight
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        pass
    def draw(self):
        self.knight.p_image.clip_draw(0, 0, 1022, 1022, self.knight.p_x, self.knight.p_y, 100, 100)
        pass


class Ready_to_appear:
    def __init__(self, knight):
        self.knight = knight
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        pass
    def draw(self):
        self.knight.p_image.clip_draw(0, 0, 1022, 1022, self.knight.p_x, self.knight.p_y, 100, 100)
        pass



class Knight:
    image = None
    p_image = None
    def __init__(self):
        self.x, self.y = 0, 0
        self.p_x, self.p_y = 0, 0
        self.frame = 0
        self.face_dir = 0
        self.Hp = 1000
        self.Def = 10
        self.Atk = 100
        self.number = 1
        if self.image is None:
            self.image = load_image('knight_01.png')
        if self.p_image is None:
            self.p_image = load_image('Knight_portrait.png')

        self.NON_APPEAR = Non_appear(self)
        self.READY_TO_APPEAR = Ready_to_appear(self)
        self.IDLE = Idle(self)
        self.state_machine = StateMachine(
            self.NON_APPEAR,
            {
                self.NON_APPEAR : {m_right_down: self.READY_TO_APPEAR},
                self.READY_TO_APPEAR : {},
                self.IDLE : {}
             }
        )

    def draw(self):
        self.state_machine.draw()
        #self.image.clip_draw(0, 0, 100, 100, self.x, self.y)
    def set_number(self, number):
        self.number = number
        self.p_x, self.p_y = (number-1)*100+50, 50
    def update(self):
        self.state_machine.update()
    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT',event))