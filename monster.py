from pico2d import load_image, get_canvas_height

import game_framework
from Tile import Tile
from state_machine import StateMachine


TIME_PER_ACTION = 0.8
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 2

class Idle:
    def __init__(self, monster):
        self.monster = monster
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        self.monster.x += 1
        self.monster.frame = (self.monster.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 2
        pass
    def draw(self):
        x = self.monster.x
        y = self.monster.y + 50
        face = getattr(self.monster, 'face_dir', 0)
        # face == 0: 오른쪽(정방향), 그 외: 좌우 반전
        if face == 0:
            self.monster.image[int(self.monster.frame)].clip_draw(0, 0, 100, 100, x, y, 150, 150)
        else:
            self.monster.image[int(self.monster.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 150)

class Monster:
    image = []
    image.append(None)
    image.append(None)
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
        self.face_dir = 0  # 1: right, -1: left
        if self.image[0] is None:
            self.image[0] = load_image('brownbear_01.png')
            self.image[1] = load_image('brownbear_02.png')
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

