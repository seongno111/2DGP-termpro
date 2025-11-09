from pico2d import load_image

from state_machine import StateMachine


class Idle:
    def __init__(self, Healer):
        self.healer = Healer
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        pass
    def draw(self):
        x = self.healer.x
        y = self.healer.y + 50
        # face_dir == 0 -> 오른쪽, 1 -> 왼쪽(수평 반전)
        if getattr(self.healer, 'face_dir', 0) == 0:
            self.healer.image.clip_draw(0, 0, 100, 100, x, y+50, 150, 160)
        else:
            # 'h' 플래그로 수평 반전
            self.healer.image.clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y+50, 150, 160)


class Healer:
    image = None
    def __init__(self):
        self.depth = 1
        self.x, self.y = 0, 0
        self.frame = 0
        self.face_dir = 0
        self.Hp = 800
        self.Def = 10
        self.Atk = 200
        self.number = 5
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        if self.image is None:
            self.image = load_image('Healer_01.png')
        self.IDLE = Idle(self)

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE : {}
             }
        )
    def get_at_bound(self):
        if self.face_dir == 0:
            return self.x - 150, self.y - 150, self.x + 250, self.y + 170
        elif self.face_dir == 1:
            return self.x + 150, self.y - 150, self.x - 250, self.y + 170
        elif self.face_dir == 2:
            return self.x - 150, self.y - 120, self.x + 150, self.y + 250
        else:
            return self.x - 150, self.y + 170, self.x + 150, self.y - 250
    def draw(self):
        self.state_machine.draw()
    def update(self):
        self.state_machine.update()
    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT',event))
