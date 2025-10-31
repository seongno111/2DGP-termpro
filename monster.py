from pico2d import load_image
from state_machine import StateMachine


class Idle:
    def __init__(self, monster):
        self.monster = monster
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        pass
    def draw(self):
        pass

class Monster:
    image = None
    def __init__(self, num):
        self.num = num
        self.x, self.y = 0, 0
        self.Hp = 500
        self.Def = 5
        self.Atk = 50
        self.frame = 0
        self.face_dir = 1  # 1: right, -1: left
        if self.image is None:
            self.image = load_image('asha01_01.png') #임시 이미지
        self.IDLE = Idle(self)
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {}
            }
        )
    def draw(self):
        self.state_machine.draw()
    def update(self):
        self.state_machine.update()
    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))

