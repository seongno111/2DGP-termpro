from pico2d import load_image, load_font

import game_framework
import game_world
from state_machine import StateMachine



TIME_PER_ACTION = 0.8
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 2
FRAMES_PER_ACTION_ac = 5

class Idle:
    def __init__(self, vanguard):
        self.vanguard = vanguard
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        self.vanguard.frame = (self.vanguard.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 2
    def draw(self):
        x = self.vanguard.x
        y = self.vanguard.y + 50
        if getattr(self.vanguard, 'face_dir', 0) == 0 or getattr(self.vanguard, 'face_dir', 0) == 2:
            idx = int(self.vanguard.frame) % len(self.vanguard.image)
            self.vanguard.image[idx].clip_draw(0, 0, 100, 100, x, y, 150, 160)
        else:
            idx = int(self.vanguard.frame) % len(self.vanguard.image)
            self.vanguard.image[idx].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)

class Attack:
    def __init__(self, vanguard):
        self.vanguard = vanguard
        self.attack_timer = 0.0
    def enter(self, e):
        self.vanguard.frame = 0
        self.attack_timer = 0.0
        if isinstance(e, tuple) and len(e) >= 3:
            self.vanguard.target = e[2]
    def exit(self, e):
        self.vanguard.frame = 0
        self.attack_timer = 0.0
    def do(self):
        self.vanguard.frame = (self.vanguard.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 5
        target = getattr(self.vanguard, 'target', None)
        if target is None or not game_world.in_attack_range(self.vanguard, target):
            self.vanguard.state_machine.handle_state_event(('SEPARATE', None))
            return
        ATTACK_INTERVAL = 0.8
        self.attack_timer += game_framework.frame_time
        if self.attack_timer >= ATTACK_INTERVAL:
            self.attack_timer -= ATTACK_INTERVAL
            dmg = max(0, self.vanguard.Atk - getattr(target, 'Def', 0))
            target.Hp -= dmg
            print(f'Vanguard attacked {target.__class__.__name__} dmg={dmg} target_hp={getattr(target, "Hp", "?")}')
            if getattr(target, 'Hp', 1) <= 0:
                print(f'{target.__class__.__name__} died by Vanguard.')
                try:
                    game_world.remove_object(target)
                except Exception:
                    pass
                try:
                    game_world.remove_collision_object(target)
                except Exception:
                    pass
                self.vanguard.target = None
                self.vanguard.state_machine.handle_state_event(('SEPARATE', None))
    def draw(self):
        x = self.vanguard.x
        y = self.vanguard.y + 50
        if getattr(self.vanguard, 'face_dir', 0) == 0 or getattr(self.vanguard, 'face_dir', 0) == 2:
            self.vanguard.image[int(self.vanguard.frame)+1].clip_draw(0, 0, 100, 100, x, y, 150, 160)
            # optional attack effect draw if image_at exists
            if hasattr(self.vanguard, 'image_at') and self.vanguard.frame >= 3 and len(self.vanguard.image_at) > 0:
                idx = min(len(self.vanguard.image_at)-1, int(self.vanguard.frame)-3)
                self.vanguard.image_at[idx].clip_draw(0, 0, 124, 117, x + 50, y-20, 100, 160)
        else:
            self.vanguard.image[int(self.vanguard.frame)+1].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)
            if hasattr(self.vanguard, 'image_at') and self.vanguard.frame >= 3 and len(self.vanguard.image_at) > 0:
                idx = min(len(self.vanguard.image_at)-1, int(self.vanguard.frame)-3)
                self.vanguard.image_at[idx].clip_composite_draw(0, 0, 124, 117, 0, 'h', x-50, y-20, 150, 160)

class Vanguard:
    image = []
    image_at = []
    for i in range(8):
        image.append(None)
    for i in range(3):
        image_at.append(None)

    def __init__(self):
        self.depth = 0
        self.x, self.y = 0, 0
        self.frame = 0
        self.face_dir = 0
        self.max_hp = 700
        self.Hp = 700
        self.Def = 10
        self.Atk = 110
        self.number = 6
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        self.font = load_font('ENCR10B.TTF', 30)

        if self.image[0] is None:
            # 기존 스프라이트 이름에 맞게 수정하세요 (파일 없으면 에러 방지 위해 try/except 할 것)
            try:
                self.image[0] = load_image('asha01_01.png')
                self.image[1] = load_image('asha01_02.png')
                self.image[2] = load_image('asha01_03.png')
                self.image[3] = load_image('asha01_04.png')
                self.image[4] = load_image('asha01_05.png')
                self.image[5] = load_image('asha01_06.png')
                self.image[6] = load_image('asha01_07.png')
            except Exception:
                pass

        if self.image_at[0] is None:
            try:
                self.image_at[0] = load_image('va_at_ef_01.png')
                self.image_at[1] = load_image('va_at_ef_02.png')
                self.image_at[2] = load_image('va_at_ef_03.png')
            except Exception:
                # 파일이 없으면 비어둠
                self.image_at = []

        self.IDLE = Idle(self)
        self.ATK = Attack(self)

        def _on_collide(ev):
            return isinstance(ev, tuple) and len(ev) >= 3 and ev[0] == 'COLLIDE' and isinstance(ev[2], object)
        def _on_separate(ev):
            return isinstance(ev, tuple) and len(ev) >= 1 and ev[0] == 'SEPARATE'

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {
                    _on_collide: self.ATK
                },
                self.ATK: {
                    _on_separate: self.IDLE
                }
            }
        )
        self.target = None

    def get_at_bound(self):
        if self.face_dir == 0:
            x1, y1, x2, y2 = self.x - 50, self.y - 50, self.x + 150, self.y + 50
        elif self.face_dir == 1:
            x1, y1, x2, y2 = self.x - 150, self.y - 50, self.x + 50, self.y + 50
        elif self.face_dir == 2:
            x1, y1, x2, y2 = self.x - 50, self.y - 50, self.x + 50, self.y + 150
        else:
            x1, y1, x2, y2 = self.x - 50, self.y - 150, self.x + 50, self.y + 50

        left = min(x1, x2)
        bottom = min(y1, y2)
        right = max(x1, x2)
        top = max(y1, y2)
        return left, bottom, right, top

    def draw(self):
        self.state_machine.draw()
        for i in range(int((self.Hp/self.max_hp)*100//10)):
            self.font.draw(self.x-50+i*10, self.y+80, f'/', (100, 250, 100))

    def update(self):
        self.state_machine.update()

    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50

    def handle_collision(self, group, other):
        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()

        # VANGUARD와 MONSTER 간 충돌인 경우에만 특별 처리 (양방향 허용)
        if (left == 'VANGUARD' and right == 'MONSTER') or (left == 'MONSTER' and right == 'VANGUARD') \
           or (left == 'VANGAURD' and right == 'MONSTER') or (left == 'MONSTER' and right == 'VANGAURD'):
            self.target = other
            self.state_machine.handle_state_event(('COLLIDE', group, other))
            return

        # 기본 폴백
        self.target = other
        self.state_machine.handle_state_event(('COLLIDE', group, other))

    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))
