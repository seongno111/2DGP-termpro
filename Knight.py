from pico2d import load_image, draw_rectangle, load_font

import game_framework
from state_machine import StateMachine


TIME_PER_ACTION = 0.8
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 2
FRAMES_PER_ACTION_ac = 5

class Idle:
    def __init__(self, knight):
        self.knight = knight
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        self.knight.frame = (self.knight.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 2
        pass
    def draw(self):
        x = self.knight.x
        y = self.knight.y + 50
        # face_dir == 0 -> 오른쪽, 1 -> 왼쪽(수평 반전)
        if getattr(self.knight, 'face_dir', 0) == 0 or getattr(self.knight, 'face_dir', 0) == 2:
            self.knight.image[int(self.knight.frame)].clip_draw(0, 0, 100, 100, x, y, 150, 160)
        else:
            # 'h' 플래그로 수평 반전
            self.knight.image[int(self.knight.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)

class Knight:
    image = []
    for i in range(8):
        image.append(None)
    def __init__(self):
        self.depth = 0
        self.x, self.y = 0, 0
        self.frame = 0
        self.face_dir = 0 # 0오른쪽, 1왼쪽, 2위, 3아래
        self.Hp = 1000
        self.Def = 10
        self.Atk = 100
        self.number = 1
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        self.font = load_font('ENCR10B.TTF', 30)
        if self.image[0] is None:
            self.image[0] = load_image('tuar03_01.png')
            self.image[1] = load_image('tuar03_02.png')
            self.image[2] = load_image('tuar03_03.png')
            self.image[3] = load_image('tuar03_04.png')
            self.image[4] = load_image('tuar03_05.png')
            self.image[5] = load_image('tuar03_06.png')
            self.image[7] = load_image('tuar03_07.png')
        self.IDLE = Idle(self)
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE : {}
             }
        )
    def get_at_bound(self):
        if self.face_dir == 0:
            return self.x-50, self.y - 50, self.x + 150, self.y + 50
        elif self.face_dir == 1:
            return self.x+50, self.y - 50, self.x - 150, self.y + 50
        elif self.face_dir == 2:
            return self.x -50, self.y -50, self.x +50, self.y + 150
        else:
            return self.x -50, self.y +50, self.x +50, self.y - 150

    def draw(self):
        self.state_machine.draw()
        for i in range(int((self.Hp/1000)*100//10)):
            self.font.draw(self.x-50+i*10, self.y+80, f'/', (100, 250, 100))

    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50

    def update(self):
        self.state_machine.update()

    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT',event))

    def handle_collision(self, group, other):
        if group == 'KNIGHT:MONSTER':
            pass
