from pico2d import *

from state_machine import StateMachine

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
        pass
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
                self.IDLE : {},
                self.PLACING : {},
                self.DECIDE : {}
            }
        )


    def update(self):
        pass

    def draw(self):
        self.k_p_image.clip_draw(0, 0, 1022, 1022, self.k_p_x, self.p_y, 100, 100)
