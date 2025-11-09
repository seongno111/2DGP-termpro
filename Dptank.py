from pico2d import load_image

from state_machine import StateMachine


class Idle:
    def __init__(self, Dptank):
        self.dptank = Dptank
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        pass
    def draw(self):
        x = self.dptank.x
        y = self.dptank.y + 50
        # face_dir == 0 -> 오른쪽, 1 -> 왼쪽(수평 반전)
        if getattr(self.dptank, 'face_dir', 0) == 0:
            self.dptank.image.clip_draw(0, 0, 100, 100, x, y, 150, 160)
        else:
            # 'h' 플래그로 수평 반전
            self.dptank.image.clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)


class Dptank:
    image = None
    def __init__(self):
        self.depth = 0
        self.x, self.y = 0, 0
        self.frame = 0
        self.face_dir = 0
        self.Hp = 1500
        self.Def = 50
        self.Atk = 60
        self.number = 4
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        if self.image is None:
            self.image = load_image('Dptank_01.png')
        self.IDLE = Idle(self)

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE : {}
             }
        )
    def get_at_bound(self):
        if self.face_dir == 0:
            return self.x-50, self.y - 50, self.x + 50, self.y + 50
        elif self.face_dir == 1:
            return self.x+50, self.y - 50, self.x - 50, self.y + 50
        elif self.face_dir == 2:
            return self.x -50, self.y -50, self.x +50, self.y + 50
        else:
            return self.x -50, self.y +50, self.x +50, self.y - 50
    def draw(self):
        self.state_machine.draw()
    def update(self):
        self.state_machine.update()
    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT',event))
