from pico2d import load_image, draw_rectangle, load_font

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
        self.archer.frame = (self.archer.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 2
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

        # 타겟이 월드에서 제거되었는지 검사
        removed_from_world = False
        try:
            removed_from_world = not any(target in layer for layer in game_world.world) if target is not None else False
        except Exception:
            removed_from_world = True

        # 타겟이 없거나 사망했거나 월드에서 제거되었거나 범위 밖이면 공격 종료
        if (target is None) or (getattr(target, 'Hp', 1) <= 0) or removed_from_world or (
        not game_world.in_attack_range(self.archer, target)):
            self.archer.target = None
            self.archer.state_machine.handle_state_event(('SEPARATE', None))
            return

        ATTACK_INTERVAL = 0.9
        self.attack_timer += game_framework.frame_time
        if self.attack_timer >= ATTACK_INTERVAL:
            self.attack_timer -= ATTACK_INTERVAL
            # 발사
            arrow = Archer_Arrow(self.archer.face_dir)
            arrow.x = self.archer.x
            arrow.y = self.archer.y
            arrow.owner = self.archer
            arrow.owner_atk = getattr(self.archer, 'Atk', 120)

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
        self.max_hp = 700
        self.Hp = 700
        self.Def = 10
        self.Atk = 120
        self.number = 2
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        self.font = load_font('ENCR10B.TTF', 30)
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

            # ATK 상태에서도 COLLIDE 이벤트를 자기 자신으로 매핑하여 "처리되지 않은 이벤트" 로그를 방지

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {_on_collide: self.ATK},
                self.ATK: {_on_separate: self.IDLE, _on_collide: self.ATK}  # 변경: _on_collide 추가
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
        for i in range(int((self.Hp / 700) * 100 // 10)):
            self.font.draw(self.x - 50 + i * 10, self.y + 80, f'/', (100, 250, 100))
    def update(self):
        self.state_machine.update()
    def get_bb(self):
        return self.x - 20, self.y - 20, self.x + 20, self.y + 20

    def handle_collision(self, group, other):
        try:
            if not any(other in layer for layer in game_world.world):
                return
        except Exception:
            return
        if getattr(other, 'Hp', 1) <= 0:
            return

        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()

        if (left == 'ARCHER' and right == 'MONSTER') or (left == 'MONSTER' and right == 'ARCHER'):
            if getattr(self, 'target', None) is other:
                return
            self.target = other
            self.state_machine.handle_state_event(('COLLIDE', group, other))
            return

        if getattr(self, 'target', None) is other:
            return
        self.target = other
        self.state_machine.handle_state_event(('COLLIDE', group, other))


class Archer_Arrow:
    image = []
    for i in range(4):
        image.append(None)
    def __init__(self, dir):
        self.face = dir
        self.depth = 1
        self.x, self.y = 0, 0
        self.frame = 0
        self.speed = 800
        self.vx = self.speed
        self.vy = 0
        self.owner = None
        self.owner_atk = 0
        self.removed = False
        if self.image[0] is None:
            self.image[0] = load_image('arrow_01_(1).png')
            self.image[1] = load_image('arrow_01_(2).png')
            self.image[2] = load_image('arrow_01_(3).png')
    def draw(self):
        if self.face == 0:
            self.image[int(self.frame)].clip_draw(0, 0, 88, 16, self.x, self.y, 50, 10)
        else:
            self.image[int(self.frame)].clip_composite_draw(0, 0, 88, 16,0, 'h', self.x, self.y, 50, 10)
    def update(self):
        self.frame = (self.frame + 3 * ACTION_PER_TIME * game_framework.frame_time) % 3
        if self.removed:
            return
        self.x += self.vx * game_framework.frame_time
        self.y += self.vy * game_framework.frame_time
        # 화면 밖이면 제거 시도
        if self.x < -100 or self.x > 1100 or self.y < -200 or self.y > 1200:
            self._safe_remove()
    def get_bb(self):
        return self.x - 12, self.y - 4, self.x + 12, self.y + 4
    def _safe_remove(self):
        if self.removed:
            return
        self.removed = True
        try:
            game_world.remove_object(self)
        except Exception:
            pass
        try:
            game_world.remove_collision_object(self)
        except Exception:
            pass
    def handle_collision(self, group, other):
        if self.removed:
            return
        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()
        if not ((left == 'ARCHER_ARROW' and right == 'MONSTER') or (left == 'MONSTER' and right == 'ARCHER_ARROW')):
            return
        try:
            atk = getattr(self, 'owner_atk', None)
            if atk is None and self.owner is not None:
                atk = getattr(self.owner, 'Atk', 0)
            if atk is None:
                atk = 0
            if hasattr(other, 'Hp'):
                dmg = max(0, int(atk) - getattr(other, 'Def', 0))
                other.Hp -= dmg
            else:
                dmg = 0
            print(f'Archer_Arrow hit {other.__class__.__name__} dmg={dmg} target_hp={getattr(other, "Hp", "?")}')
            if getattr(other, 'Hp', 1) <= 0:
                try:
                    game_world.remove_object(other)
                    other.die()
                except Exception:
                    pass
                try:
                    game_world.remove_collision_object(other)
                except Exception:
                    pass
                # owner가 타겟으로 잡고 있으면 해제하고 SEPARATE 이벤트 발생 (owner가 월드에 있을 때만)
                try:
                    if self.owner is not None and getattr(self.owner, 'target', None) is other:
                        self.owner.target = None
                        if any(self.owner in layer for layer in game_world.world):
                            try:
                                self.owner.state_machine.handle_state_event(('SEPARATE', None))
                            except Exception:
                                pass
                except Exception:
                    pass
            self._safe_remove()
        except Exception as e:
            print(f'Archer_Arrow.handle_collision error: {e}')
            self._safe_remove()