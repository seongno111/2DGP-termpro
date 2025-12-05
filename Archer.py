from pico2d import load_image, draw_rectangle, load_font

import game_framework
import game_world
from state_machine import StateMachine
from link_helper import update_link_states_for_knight_archer
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
        if self.archer.skill_state is True:
            self.archer.skill_frame = (self.archer.skill_frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 5
        try:
            # Archer는 이제 하나의 target만 고집하지 않고, Idle 상태에서는 단순히 애니메이션만 유지
            # 실제 공격 대상 선택/타격은 Attack 상태에서 "범위 내 모든 몬스터/보스"를 순회하면서 처리한다.
            pass
        except Exception:
            pass


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
        # 더 이상 단일 target을 고정하지 않음

    def exit(self, e):
        self.archer.frame = 0
        self.attack_timer = 0.0

    def do(self):
        self.archer.frame = (self.archer.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 5
        if self.archer.skill_state is True:
            self.archer.skill_frame = (self.archer.skill_frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 5
            self.archer.frame = (self.archer.frame + (FRAMES_PER_ACTION_ac*4) * ACTION_PER_TIME * game_framework.frame_time) % 5

        # Archer는 이제 공격 범위 안에 있는 모든 Monster/Boss를 대상으로 공격한다.
        ATTACK_INTERVAL_BASE = 0.9
        ATTACK_INTERVAL = ATTACK_INTERVAL_BASE / 4 if self.archer.skill_state else ATTACK_INTERVAL_BASE
        self.attack_timer += game_framework.frame_time
        if self.attack_timer < ATTACK_INTERVAL:
            return
        self.attack_timer -= ATTACK_INTERVAL

        atk = getattr(self.archer, 'Atk', 120)

        # 이번 프레임에 실제로 타격한 대상이 있는지 / 살아있는 대상이 남아있는지 트래킹
        last_hit_target = None
        hit_any = False
        alive_any = False

        try:
            for layer in list(game_world.world):
                for obj in list(layer):
                    # Monster / Boss 필터링
                    try:
                        from monster import Monster
                        from boss import Boss
                        if not isinstance(obj, (Monster, Boss)):
                            continue
                    except Exception:
                        name = obj.__class__.__name__
                        if name not in ('Monster', 'Boss'):
                            continue

                    # 이미 죽은(또는 제거 대상인) 객체는 월드/콜리전에서 한 번 더 정리 후 스킵
                    if getattr(obj, 'Hp', 0) <= 0:
                        try:
                            game_world.remove_object(obj)
                        except Exception:
                            pass
                        try:
                            game_world.remove_collision_object(obj)
                        except Exception:
                            pass
                        continue

                    # 여기까지 왔으면 아직 살아있는 몬스터/보스
                    alive_any = True

                    # 공격 범위 안인지 체크
                    try:
                        if not game_world.in_attack_range(self.archer, obj):
                            continue
                    except Exception:
                        continue

                    # 데미지 적용
                    dmg = max(0, int(atk) - getattr(obj, 'Def', 0)) if hasattr(obj, 'Hp') else 0
                    if hasattr(obj, 'Hp'):
                        obj.Hp -= dmg
                    print(f'Archer multi-hit -> {obj.__class__.__name__} dmg={dmg} target_hp={getattr(obj, "Hp", "?")}')

                    # 사망 처리
                    if getattr(obj, 'Hp', 1) <= 0:
                        print(f'{obj.__class__.__name__} died by archer.')
                        try:
                            game_world.remove_object(obj)
                            obj.die()
                        except Exception:
                            pass
                        try:
                            game_world.remove_collision_object(obj)
                        except Exception:
                            pass
                    else:
                        last_hit_target = obj

                    hit_any = True
        except Exception:
            pass

        # 더 이상 살아있는 Monster/Boss 가 하나도 없으면 Idle 로 복귀
        if not alive_any:
            try:
                self.archer.state_machine.handle_state_event(('SEPARATE', None))
            except Exception:
                pass
            return

        # 이번 프레임에 범위 안에서 맞춘 대상이 하나도 없으면 Idle 로 복귀
        if not hit_any:
            try:
                self.archer.state_machine.handle_state_event(('SEPARATE', None))
            except Exception:
                pass

        # 시각적인 Arrow 오버레이는 마지막으로 맞은 대상에게만 표시
        if last_hit_target is not None:
            try:
                overlay = Archer_Arrow(target=last_hit_target, owner=self.archer, owner_atk=atk, life_frames=3, depth=7)
                old = getattr(last_hit_target, '_overlay', None)
                if old is not None:
                    try:
                        game_world.remove_object(old)
                    except Exception:
                        pass
                last_hit_target._overlay = overlay
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
    image_l = None
    for i in range(8):
        image.append(None)
    for i in range(6):
        image_sk.append(None)
    def __init__(self):
        self.depth = 1
        self.x, self.y = 0, 0
        self.frame = 0
        self.linked = False
        self.skill_frame = 0
        self.face_dir = 0
        self.max_hp = 700
        self.Hp = 700
        self.Def = 10
        self.Atk = 120
        self.number = 2
        # 스킬 게이지/상태: 게이지 0~10, 상태 및 지속시간 별도 관리
        self.skill = 0
        self._skill_timer = 0.0
        self.skill_state = False
        self.skill_state_time = 0.0
        self.skill_state_duration = 10.0
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        self.font = load_font('ENCR10B.TTF', 30)
        if self.image[0] is None:
            self.image[0] = load_image('char/isli01_01.png')
            self.image[1] = load_image('char/isli01_02.png')
            self.image[2] = load_image('char/isli01_03.png')
            self.image[3] = load_image('char/isli01_04.png')
            self.image[4] = load_image('char/isli01_05.png')
            self.image[5] = load_image('char/isli01_06.png')
            self.image[6] = load_image('char/isli01_07.png')
        if self.image_sk[0] is None:
            self.image_sk[0] = load_image('char/isli_skill01.png')
            self.image_sk[1] = load_image('char/isli_skill02.png')
            self.image_sk[2] = load_image('char/isli_skill03.png')
            self.image_sk[3] = load_image('char/isli_skill04.png')
            self.image_sk[4] = load_image('char/isli_skill05.png')
        if self.image_l is None:
            self.image_l = load_image('char/isli_link.png')
        self.IDLE = Idle(self)
        self.ATK = Attack(self)

        def _on_collide(ev):
            # 충돌 그 자체로 공격 상태로 들어가지만, 특정 몬스터를 고정 타깃으로 삼지는 않는다.
            return isinstance(ev, tuple) and len(ev) >= 3 and ev[0] == 'COLLIDE' and isinstance(ev[2], object)

        def _on_separate(ev):
            return isinstance(ev, tuple) and len(ev) >= 1 and ev[0] == 'SEPARATE'

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {_on_collide: self.ATK},
                self.ATK: {_on_separate: self.IDLE, _on_collide: self.ATK}
            }
        )
        # Archer는 더 이상 self.target을 단일 타깃으로 사용하지 않으므로 None으로만 유지
        self.target = None
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

        # Knight-Archer 링크 상태 자동 갱신
        try:
            update_link_states_for_knight_archer()
        except Exception:
            pass

        # 링크 상태에 따른 공격력 기본값 조정
        self.Atk = 150 if self.linked else 120

        # 1) 스킬 발동 중이면 10초 유지 (화력/공속 증가는 Attack.do 에서 skill_state를 보고 처리)
        if self.skill_state:
            self.skill_state_time += dt
            if self.skill_state_time >= self.skill_state_duration:
                self.skill_state = False
                self.skill_state_time = 0.0
                self.skill = 0
        else:
            # 2) 스킬이 꺼져 있을 때만 게이지 충전 (10초 동안 0→10)
            self._skill_timer += dt
            while self._skill_timer >= 1.0 and self.skill < 10:
                self.skill = min(10, self.skill + 1)
                self._skill_timer -= 1.0
    def get_bb(self):
        return self.x - 20, self.y - 20, self.x + 20, self.y + 20

    def handle_collision(self, group, other):
        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()

        if (left == 'ARCHER' and right == 'MONSTER') or (left == 'MONSTER' and right == 'ARCHER'):
            # 다른 유닛이 이미 막고 있더라도, Archer는 "막는" 개념이 없고 단순히 공격 상태로만 전환하면 된다.
            try:
                self.state_machine.handle_state_event(('COLLIDE', group, other))
            except Exception:
                pass
            return


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
        # 각 프레임 지속시간
        self.frame_duration = 0.06

        if self.image[0] is None:
            self.image[0] = load_image('char/arrow_01_(1).png')
            self.image[1] = load_image('char/arrow_01_(2).png')
            self.image[2] = load_image('char/arrow_01_(3).png')

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

        try:
            if self.target is None or not any(self.target in layer for layer in game_world.world):
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

        try:
            self.x = self.target.x
            self.y = self.target.y
        except Exception:
            pass

        self.frame_timer += game_framework.frame_time
        if self.frame_timer >= (self.frame_idx + 1) * self.frame_duration:
            self.frame_idx += 1

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
        idx = min(2, int(self.frame_idx))
        total_drop = 30
        drop_per_frame = total_drop / max(1, self.life_frames)
        y_offset = total_drop - (drop_per_frame * self.frame_idx)

        try:
            draw_x = self.x
            draw_y = self.y + 50 + y_offset
        except Exception:
            draw_x, draw_y = self.x, self.y + 50

        try:
            self.image[idx].clip_composite_draw(0, 0, 88, 16, math.radians(90),'h', draw_x, draw_y, 100, 20)
        except Exception:
            pass

    def get_bb(self):
        return self.x, self.y, self.x, self.y

    def _safe_remove(self):
        if self.removed:
            return
        self.removed = True
        try:
            game_world.remove_object(self)
        except Exception:
            pass