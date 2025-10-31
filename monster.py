from pico2d import load_image, get_canvas_height
from Tile import Tile
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
        x = self.monster.x
        y = self.monster.y + 50
        face = getattr(self.monster, 'face_dir', 0)
        # face == 0: 오른쪽(정방향), 그 외: 좌우 반전
        if face == 0:
            self.monster.image.clip_draw(0, 0, 100, 100, x, y, 150, 150)
        else:
            self.monster.image.clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 150)

class Monster:
    image = None
    def __init__(self, num):
        self.num = num
        col = num % 10
        row = num // 10
        tw, th = Tile.TILE_W, Tile.TILE_H
        canvas_h = get_canvas_height()
        tile_cx = col * tw + tw // 2
        tile_cy = canvas_h - (row * th + th // 2)

        self.x, self.y = tile_cx, tile_cy
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

