from pico2d import load_image, draw_rectangle

import game_framework
import game_world
from state_machine import StateMachine
import math

TIME_PER_ACTION = 0.8
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 2
FRAMES_PER_ACTION_ac = 5

class Idle:
    def __init__(self, archer):
        self.archer = archer
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        self.archer.frame = (self.archer.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 2
    def draw(self):
        x = self.archer.x
        y = self.archer.y + 50
        if getattr(self.archer, 'face_dir', 0) == 0:
            self.archer.image[int(self.archer.frame)].clip_draw(0, 0, 100, 100, x, y+50, 150, 160)
        else:
            self.archer.image[int(self.archer.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y+50, 150, 160)

class Attack:
    def __init__(self, archer):
        self.archer = archer
        self.attack_timer = 0.0
    def enter(self, e):
        self.archer.frame = 0
        self.attack_timer = 0.0
        if isinstance(e, tuple) and len(e) >= 3:
            self.archer.target = e[2]
    def exit(self, e):
        self.archer.frame = 0
        self.attack_timer = 0.0
    def do(self):
        self.archer.frame = (self.archer.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 5
        target = getattr(self.archer, 'target', None)
        if target is None or not game_world.in_attack_range(self.archer, target):
            self.archer.state_machine.handle_state_event(('SEPARATE', None))
            return

        ATTACK_INTERVAL = 0.9
        self.attack_timer += game_framework.frame_time
        if self.attack_timer >= ATTACK_INTERVAL:
            self.attack_timer -= ATTACK_INTERVAL
            # 발사
            arrow = Archer_Arrow()
            arrow.x = self.archer.x
            arrow.y = self.archer.y
            # 방향 벡터 계산
            dx = target.x - arrow.x
            dy = target.y - arrow.y
            dist = math.hypot(dx, dy)
            if dist == 0:
                vx, vy = arrow.speed, 0
            else:
                vx = dx / dist * arrow.speed
                vy = dy / dist * arrow.speed
            arrow.vx = vx
            arrow.vy = vy
            # add to world and collision pairs
            game_world.add_object(arrow, 7)
            # ensure group exists and register arrow
            game_world.add_collision_pair('ARCHER_ARROW:MONSTER', arrow, None)
    def draw(self):
        x = self.archer.x
        y = self.archer.y + 50
        if getattr(self.archer, 'face_dir', 0) == 0:
            self.archer.image[int(self.archer.frame)+1].clip_draw(0, 0, 100, 100, x, y+50, 150, 160)
        else:
            self.archer.image[int(self.archer.frame)+1].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y+50, 150, 160)

class Archer:
    image = []
    for i in range(8):
        image.append(None)
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
        if self.image[0] is None:
            self.image[0] = load_image('isli01_01.png')
            self.image[1] = load_image('isli01_02.png')
            self.image[2] = load_image('isli01_03.png')
            self.image[3] = load_image('isli01_04.png')
            self.image[4] = load_image('isli01_05.png')
            self.image[5] = load_image('isli01_06.png')
            self.image[6] = load_image('isli01_07.png')
        self.IDLE = Idle(self)
        self.ATK = Attack(self)

        def _on_collide(ev):
            return isinstance(ev, tuple) and len(ev) >= 3 and ev[0] == 'COLLIDE' and isinstance(ev[2], object)

        def _on_separate(ev):
            return isinstance(ev, tuple) and len(ev) >= 1 and ev[0] == 'SEPARATE'

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE : { _on_collide: self.ATK },
                self.ATK  : { _on_separate: self.IDLE }
             }
        )
        self.target = None
        # 화살-몬스터 충돌 그룹 미리 추가 (나중에 화살을 등록할 때 사용)
        game_world.add_collision_pair('ARCHER_ARROW:MONSTER', None, None)

    def get_at_bound(self):
        if self.face_dir == 0:
            x1, y1, x2, y2 = self.x - 50, self.y - 150, self.x + 350, self.y + 170
        elif self.face_dir == 1:
            x1, y1, x2, y2 = self.x + 50, self.y - 150, self.x - 350, self.y + 170
        elif self.face_dir == 2:
            x1, y1, x2, y2 = self.x - 150, self.y - 30, self.x + 150, self.y + 350
        else:
            x1, y1, x2, y2 = self.x - 150, self.y + 70, self.x + 150, self.y - 350

        left = min(x1, x2)
        bottom = min(y1, y2)
        right = max(x1, x2)
        top = max(y1, y2)
        return left, bottom, right, top

    def draw(self):
        self.state_machine.draw()
    def update(self):
        self.state_machine.update()
    def get_bb(self):
        return self.x - 20, self.y - 20, self.x + 20, self.y + 20

    def handle_collision(self, group, other):
        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()
        # 범위 판정으로 들어오면 타겟 설정 후 공격 상태로 전환
        if (left == 'ARCHER' and right == 'MONSTER') or (left == 'MONSTER' and right == 'ARCHER'):
            self.target = other
            self.state_machine.handle_state_event(('COLLIDE', group, other))
            return
        # fallback
        self.target = other
        self.state_machine.handle_state_event(('COLLIDE', group, other))

    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT',event))


class Archer_Arrow:
    image = []
    for i in range(4):
        image.append(None)
    def __init__(self):
        self.depth = 1
        self.x, self.y = 0, 0
        self.frame = 0
        self.speed = 800
        self.vx = self.speed
        self.vy = 0
        if self.image[0] is None:
            self.image[0] = load_image('arrow_01_(1).png')
            self.image[1] = load_image('arrow_01_(2).png')
            self.image[2] = load_image('arrow_01_(3).png')
    def draw(self):
        self.image[int(self.frame) % len(self.image)].clip_draw(0, 0, 88, 16, self.x, self.y, 50, 10)
    def update(self):
        self.x += self.vx * game_framework.frame_time
        self.y += self.vy * game_framework.frame_time
        # 화면 밖이면 제거 시도
        if self.x < -100 or self.x > 1100 or self.y < -200 or self.y > 1200:
            try:
                game_world.remove_object(self)
            except Exception:
                pass
            try:
                game_world.remove_collision_object(self)
            except Exception:
                pass
    def get_bb(self):
        return self.x - 12, self.y - 4, self.x + 12, self.y + 4
    def handle_collision(self, group, other):
        # ARCHER_ARROW:MONSTER 에 닿으면 데미지 주고 화살 제거
        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()
        if (left == 'ARCHER_ARROW' and right == 'MONSTER') or (left == 'MONSTER' and right == 'ARCHER_ARROW'):
            try:
                dmg = getattr(self, 'Atk', 0)
                # 화살의 공격력은 딜러(Archer)의 Atk를 직접 참조할 수 없으므로, 기본값으로 처리
                if hasattr(other, 'Hp'):
                    # 데미지는 Archer 기준으로 계산 (간단히 고정값 사용하거나 아처 참조를 저장해도 됨)
                    dmg = max(0, 120 - getattr(other, 'Def', 0))
                    other.Hp -= dmg
                print(f'Archer_Arrow hit Monster dmg={dmg} target_hp={getattr(other, "Hp", "?")}')
                # 몬스터 사망 처리
                if getattr(other, 'Hp', 1) <= 0:
                    try:
                        game_world.remove_object(other)
                    except Exception:
                        pass
                    try:
                        game_world.remove_collision_object(other)
                    except Exception:
                        pass
                # 화살 제거
                try:
                    game_world.remove_object(self)
                except Exception:
                    pass
                try:
                    game_world.remove_collision_object(self)
                except Exception:
                    pass
            except Exception:
                pass