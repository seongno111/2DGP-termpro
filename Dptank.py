from pico2d import load_image, load_font

import game_framework
import game_world
from state_machine import StateMachine


TIME_PER_ACTION = 0.8
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION_ac = 3

class Idle:
    def __init__(self, dptank):
        self.dptank = dptank
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        # 필요하면 아이들 애니메이션 처리
        self.dptank.frame = (self.dptank.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 2
    def draw(self):
        x = self.dptank.x
        y = self.dptank.y + 50
        if getattr(self.dptank, 'face_dir', 0) == 0:
            self.dptank.image[int(self.dptank.frame)].clip_draw(0, 0, 100, 100, x, y, 150, 160)
        else:
            self.dptank.image[int(self.dptank.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)

class Attack:
    def __init__(self, dptank):
        self.dptank = dptank
        self.attack_timer = 0.0
    def enter(self, e):
        self.dptank.frame = 0
        self.attack_timer = 0.0
        if isinstance(e, tuple) and len(e) >= 3:
            self.dptank.target = e[2]
    def exit(self, e):
        self.dptank.frame = 0
        self.attack_timer = 0.0
    def do(self):
        self.dptank.frame = (self.dptank.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 4
        target = getattr(self.dptank, 'target', None)
        # 타겟 없거나 범위 밖이면 복귀
        if target is None or not game_world.in_attack_range(self.dptank, target):
            self.dptank.state_machine.handle_state_event(('SEPARATE', None))
            return
        ATTACK_INTERVAL = 0.8
        self.attack_timer += game_framework.frame_time
        if self.attack_timer >= ATTACK_INTERVAL:
            self.attack_timer -= ATTACK_INTERVAL
            dmg = max(0, self.dptank.Atk - getattr(target, 'Def', 0))
            target.Hp -= dmg
            print(f'Dptank attacked Monster dmg={dmg} target_hp={getattr(target, "Hp", "?")}')
            if getattr(target, 'Hp', 1) <= 0:
                print(f'{target.__class__.__name__} died by Dptank.')
                try:
                    game_world.remove_object(target)
                    target.die()
                except Exception:
                    pass
                try:
                    game_world.remove_collision_object(target)
                except Exception:
                    pass
                # 타겟 정리 및 상태 복귀
                self.dptank.target = None
                self.dptank.state_machine.handle_state_event(('SEPARATE', None))
    def draw(self):
        # Dptank에 별도 공격 이미지가 없으므로 기본 draw 사용
        x = self.dptank.x
        y = self.dptank.y + 50
        if getattr(self.dptank, 'face_dir', 0) == 0:
            self.dptank.image[int(self.dptank.frame)+2].clip_draw(0, 0, 100, 100, x, y, 150, 160)
            self.dptank.at_image[int(self.dptank.frame)+1].clip_draw(0, 0, 123, 107, x+50, y, 150, 160)
        else:
            self.dptank.image[int(self.dptank.frame)+2].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)
            self.dptank.at_image[int(self.dptank.frame)+1].clip_composite_draw(0, 0, 123, 107,0, 'h', x-50, y, 150, 160)

class Dptank:
    image = []
    for i in range(7):
        image.append(None)
    at_image = []
    for i in range(6):
        at_image.append(None)
    def __init__(self):
        self.depth = 0
        self.x, self.y = 0, 0
        self.frame = 0
        self.face_dir = 0
        self.max_hp = 1500
        self.Hp = 1500
        self.Def = 30
        self.Atk = 60
        self.number = 4
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        self.font = load_font('ENCR10B.TTF', 30)
        if self.image[0] is None:
            self.image[0] = load_image('ext01_01.png')
            self.image[1] = load_image('ext01_02.png')
            self.image[2] = load_image('ext01_03.png')
            self.image[3] = load_image('ext01_04.png')
            self.image[4] = load_image('ext01_05.png')
            self.image[5] = load_image('ext01_06.png')
            self.at_image[0] = load_image('dp_at_ef_01.png')
            self.at_image[1] = load_image('dp_at_ef_02.png')
            self.at_image[2] = load_image('dp_at_ef_03.png')
            self.at_image[3] = load_image('dp_at_ef_04.png')
            self.at_image[4] = load_image('dp_at_ef_05.png')
        self.IDLE = Idle(self)
        self.ATK = Attack(self)

        def _on_collide(ev):
            return isinstance(ev, tuple) and len(ev) >= 3 and ev[0] == 'COLLIDE' and isinstance(ev[2], object)
        def _on_separate(ev):
            return isinstance(ev, tuple) and len(ev) >= 1 and ev[0] == 'SEPARATE'

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: { _on_collide: self.ATK },
                self.ATK : { _on_separate: self.IDLE }
            }
        )
        self.target = None

    def get_at_bound(self):
        if self.face_dir == 0:
            x1, y1, x2, y2 = self.x - 50, self.y - 50, self.x + 50, self.y + 50
        elif self.face_dir == 1:
            x1, y1, x2, y2 = self.x - 50, self.y - 50, self.x + 50, self.y + 50
        elif self.face_dir == 2:
            x1, y1, x2, y2 = self.x - 50, self.y - 50, self.x + 50, self.y + 50
        else:
            x1, y1, x2, y2 = self.x - 50, self.y - 50, self.x + 50, self.y + 50
        left = min(x1, x2)
        bottom = min(y1, y2)
        right = max(x1, x2)
        top = max(y1, y2)
        return left, bottom, right, top

    def draw(self):
        self.state_machine.draw()
        for i in range(int((self.Hp / 1500) * 100 // 10)):
            self.font.draw(self.x - 50 + i * 10, self.y + 80, f'/', (100, 250, 100))

    def update(self):
        self.state_machine.update()

    def get_bb(self):
        return self.x - 50, self.y - 40, self.x + 50, self.y + 40

    def handle_collision(self, group, other):
        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()
        if (left == 'DPTANK' and right == 'MONSTER') or (left == 'MONSTER' and right == 'DPTANK'):
            # 동일 타겟이면 중복 방지
            if getattr(self, 'target', None) is other:
                return
            self.target = other
            self.state_machine.handle_state_event(('COLLIDE', group, other))
            return
        # fallback
        self.target = other
        self.state_machine.handle_state_event(('COLLIDE', group, other))

    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))