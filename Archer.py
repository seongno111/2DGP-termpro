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
        if self.archer.skill_state is True:
            self.archer.skill_frame = (self.archer.skill_frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 5
    def draw(self):
        x = self.archer.x
        y = self.archer.y + 50
        if getattr(self.archer, 'face_dir', 0) == 0:
            self.archer.image[int(self.archer.frame)].clip_draw(0, 0, 100, 100, x, y+50, 150, 160)
        else:
            self.archer.image[int(self.archer.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y+50, 150, 160)
        if self.archer.skill_state is True:
            self.archer.image_sk[int(self.archer.skill_frame)].clip_draw(0, 0, 128, 55, x + 10, y - 30, 100, 40)


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
        if self.archer.skill_state is True:
            self.archer.skill_frame = (self.archer.skill_frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 5
            self.archer.frame = (self.archer.frame + (FRAMES_PER_ACTION_ac*4) * ACTION_PER_TIME * game_framework.frame_time) % 5
        target = getattr(self.archer, 'target', None)
        try:
            removed_from_world = not any(target in layer for layer in game_world.world) if target is not None else False
        except Exception:
            removed_from_world = True

        if (target is None) or (getattr(target, 'Hp', 1) <= 0) or removed_from_world or (not game_world.in_attack_range(self.archer, target)):
            self.archer.target = None
            self.archer.state_machine.handle_state_event(('SEPARATE', None))
            return

        ATTACK_INTERVAL = 0.9
        if self.archer.skill_state is True:
            ATTACK_INTERVAL = 0.9/4
        self.attack_timer += game_framework.frame_time
        if self.attack_timer >= ATTACK_INTERVAL:
            self.attack_timer -= ATTACK_INTERVAL

            # 즉시 데미지 적용 (화살 충돌 시와 동일한 계산)
            atk = getattr(self.archer, 'Atk', 120)
            dmg = max(0, int(atk) - getattr(target, 'Def', 0)) if hasattr(target, 'Hp') else 0
            if hasattr(target, 'Hp'):
                target.Hp -= dmg
            print(f'Archer attack applied to {getattr(target, "__class__", type(target)).__name__} dmg={dmg} target_hp={getattr(target, "Hp", "?")}')

            # 대상이 사망하면 월드에서 제거 시도 (원래 화살 처리와 동일하게)
            if getattr(target, 'Hp', 1) <= 0:
                print(f'{target.__class__.__name__} died by archer.')
                # 몬스터 제거 및 충돌 제거
                try:
                    game_world.remove_object(target)
                    target.die()
                except Exception:
                    pass
                try:
                    game_world.remove_collision_object(target)
                except Exception:
                    pass

            # 오버레이 이펙트 생성: 대상 위에 3프레임으로 표시
            try:
                overlay = Archer_Arrow(target=target, owner=self.archer, owner_atk=atk, life_frames=3, depth=7)
                # 기존 오버레이가 있으면 제거
                old = getattr(target, '_overlay', None)
                if old is not None:
                    try:
                        game_world.remove_object(old)
                    except Exception:
                        pass
                target._overlay = overlay
                game_world.add_object(overlay, overlay.depth)
            except Exception:
                pass

    def draw(self):
        x = self.archer.x
        y = self.archer.y + 50
        if getattr(self.archer, 'face_dir', 0) == 0:
            self.archer.image[int(self.archer.frame)+1].clip_draw(0, 0, 100, 100, x, y+50, 150, 160)
        else:
            self.archer.image[int(self.archer.frame)+1].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y+50, 150, 160)
        if self.archer.skill_state is True:
            self.archer.image_sk[int(self.archer.skill_frame)].clip_draw(0, 0, 128, 55, x + 10, y - 30, 100, 40)

class Archer:
    image = []
    image_sk = []
    for i in range(8):
        image.append(None)
    for i in range(6):
        image_sk.append(None)
    def __init__(self):
        self.depth = 1
        self.x, self.y = 0, 0
        self.frame = 0
        self.skill_frame = 0
        self.face_dir = 0
        self.max_hp = 700
        self.Hp = 700
        self.Def = 10
        self.Atk = 120
        self.number = 2
        self.skill = 10
        self._skill_timer = 0.0
        self.skill_state = False
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
        if self.image_sk[0] is None:
            self.image_sk[0] = load_image('tuar_skill01.png')
            self.image_sk[1] = load_image('tuar_skill02.png')
            self.image_sk[2] = load_image('tuar_skill03.png')
            self.image_sk[3] = load_image('tuar_skill04.png')
            self.image_sk[4] = load_image('tuar_skill05.png')
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
            self.font.draw(self.x - 50 + i * 10, self.y + 120, f'/', (100, 250, 100))
    def update(self):
        self.state_machine.update()
        try:
            dt = game_framework.frame_time
        except Exception:
            dt = 0.0

        if self.skill_state is True:
            self._skill_timer += dt
            while self._skill_timer >= 1.0 and self.skill > 0:
                self.skill = max(0, self.skill - 1)
                self._skill_timer -= 1.0
                if self.skill == 0:
                    self.skill_state = False

        else:
            self._skill_timer += dt
            while self._skill_timer >= 1.0 and self.skill < 10:
                self.skill = min(10, self.skill + 1)
                self._skill_timer -= 1.0
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

    def __init__(self, target=None, owner=None, owner_atk=0, life_frames=3, depth=7):
        self.target = target
        self.owner = owner
        self.owner_atk = owner_atk
        self.depth = depth
        self.removed = False

        # 애니메이션 상태: 0..life_frames-1
        self.life_frames = max(1, int(life_frames))
        self.frame_idx = 0
        self.frame_timer = 0.0
        # 각 프레임 지속시간 (초) — 필요시 조절
        self.frame_duration = 0.06

        if self.image[0] is None:
            self.image[0] = load_image('arrow_01_(1).png')
            self.image[1] = load_image('arrow_01_(2).png')
            self.image[2] = load_image('arrow_01_(3).png')

        # 초기 위치는 대상의 좌표를 따라가도록 설정
        try:
            if self.target is not None:
                self.x = self.target.x
                self.y = self.target.y
            else:
                self.x, self.y = 0, 0
        except Exception:
            self.x, self.y = 0, 0

    def update(self):
        if self.removed:
            return

        # 대상이 없거나 월드에 더 이상 없으면 제거
        try:
            if self.target is None or not any(self.target in layer for layer in game_world.world):
                # 참조 정리
                try:
                    if self.target is not None and getattr(self.target, '_overlay', None) is self:
                        self.target._overlay = None
                except Exception:
                    pass
                if not self.removed:
                    try:
                        game_world.remove_object(self)
                    except Exception:
                        pass
                    self.removed = True
                return
        except Exception:
            # 안전 제거
            try:
                if self.target is not None and getattr(self.target, '_overlay', None) is self:
                    self.target._overlay = None
            except Exception:
                pass
            if not self.removed:
                try:
                    game_world.remove_object(self)
                except Exception:
                    pass
                self.removed = True
            return

        # 위치 업데이트: 대상 위치를 따라감
        try:
            self.x = self.target.x
            self.y = self.target.y
        except Exception:
            pass

        # 프레임 타이머 증가 및 프레임 전환
        self.frame_timer += game_framework.frame_time
        if self.frame_timer >= (self.frame_idx + 1) * self.frame_duration:
            self.frame_idx += 1

        # 프레임이 지정된 수를 초과하면 제거
        if self.frame_idx >= self.life_frames:
            try:
                if self.target is not None and getattr(self.target, '_overlay', None) is self:
                    self.target._overlay = None
            except Exception:
                pass
            if not self.removed:
                try:
                    game_world.remove_object(self)
                except Exception:
                    pass
                self.removed = True

    def draw(self):
        # 이미지 인덱스 안전 계산 (세 장 이미지 반복 가능)
        idx = min(2, int(self.frame_idx))
        # y 오프셋을 프레임에 따라 아래로 이동 (프레임 0: 약 위, 마지막 프레임: 아래)
        # 예: 이동량 30 픽을 프레임 수로 나눔
        total_drop = 30
        drop_per_frame = total_drop / max(1, self.life_frames)
        y_offset = total_drop - (drop_per_frame * self.frame_idx)

        try:
            draw_x = self.x
            draw_y = self.y + 50 + y_offset
        except Exception:
            draw_x, draw_y = self.x, self.y + 50

        # 가로 반전은 원래 화살 방향 무시하고 대상 위에 고정으로 그리도록 함
        try:
            self.image[idx].clip_composite_draw(0, 0, 88, 16, math.radians(90),'h', draw_x, draw_y, 100, 20)
        except Exception:
            pass

    def get_bb(self):
        # 이 오버레이는 충돌 판정이 필요 없으므로 빈 박스 반환
        return self.x, self.y, self.x, self.y

    def _safe_remove(self):
        if self.removed:
            return
        self.removed = True
        try:
            game_world.remove_object(self)
        except Exception:
            pass