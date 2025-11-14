from pico2d import load_image, draw_rectangle

from state_machine import StateMachine


class Idle:
    def __init__(self, Archer):
        self.archer = Archer
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        pass
    def draw(self):
        x = self.archer.x
        y = self.archer.y + 50
        # face_dir == 0 -> 오른쪽, 1 -> 왼쪽(수평 반전)
        if getattr(self.archer, 'face_dir', 0) == 0:
            self.archer.image.clip_draw(0, 0, 100, 100, x, y+50, 150, 160)
        else:
            # 'h' 플래그로 수평 반전
            self.archer.image.clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y+50, 150, 160)

class Archer:
    image = None
    def __init__(self):
        self.depth = 1
        self.x, self.y = 0, 0
        self.frame = 0
        self.face_dir = 0
        self.Hp = 700
        self.Def = 10
        self.Atk = 120
        self.number = 2
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        if self.image is None:
            self.image = load_image('archer_01.png')
        self.IDLE = Idle(self)

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE : {}
             }
        )
    def get_at_bound(self):
        if self.face_dir == 0:
            return self.x - 50, self.y - 150, self.x + 350, self.y + 170
        elif self.face_dir == 1:
            return self.x + 50, self.y - 150, self.x - 350, self.y + 170
        elif self.face_dir == 2:
            return self.x - 150, self.y - 30, self.x + 150, self.y + 350
        else:
            return self.x - 150, self.y + 70, self.x + 150, self.y - 350
    def draw(self):
        self.state_machine.draw()
    def update(self):
        self.state_machine.update()
    def get_bb(self):
        return self.x - 20, self.y - 20, self.x + 20, self.y + 20
    def handle_collision(self, group, other):
        if group == 'ARCHER:MONSTER':
            pass
    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT',event))
