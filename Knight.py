from pico2d import load_image

from state_machine import StateMachine


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
        x = self.knight.x
        y = self.knight.y + 50
        # face_dir == 0 -> 오른쪽, 1 -> 왼쪽(수평 반전)
        if getattr(self.knight, 'face_dir', 0) == 0:
            self.knight.image.clip_draw(0, 0, 100, 100, x, y, 150, 150)
        else:
            # 'h' 플래그로 수평 반전
            self.knight.image.clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 150)
        self.knight.p_image.clip_draw(0, 0, 1022, 1022, self.knight.p_x, self.knight.p_y, 100, 100)


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
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        if self.image is None:
            self.image = load_image('knight_01.png')
        if self.p_image is None:
            self.p_image = load_image('Knight_portrait.png')
        self.IDLE = Idle(self)

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE : {}
             }
        )

    def draw(self):
        self.state_machine.draw()
    def update(self):
        self.state_machine.update()
    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT',event))
