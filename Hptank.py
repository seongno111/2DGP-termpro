from pico2d import load_image, load_font

import game_framework
import game_world
from state_machine import StateMachine


TIME_PER_ACTION = 0.8
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION_ac = 5
FRAMES_PER_ACTION = 8

class Idle:
    def __init__(self, hptank):
        self.hptank = hptank
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        # 간단한 idle 애니메이션
        self.hptank.frame = (self.hptank.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 2
        if self.hptank.skill_state is True:
            self.hptank.skill_frame = (self.hptank.skill_frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 8
    def draw(self):
        x = self.hptank.x
        y = self.hptank.y + 50
        if getattr(self.hptank, 'face_dir', 0) == 0:
            self.hptank.image[int(self.hptank.frame)].clip_draw(0, 0, 100, 100, x, y, 150, 160)
        else:
            self.hptank.image[int(self.hptank.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)
        if self.hptank.skill_state is True:
            self.hptank.sk_image[int(self.hptank.skill_frame)].clip_draw(0, 0, 116, 86, x, y-20, 150, 160)

class Attack:
    def __init__(self, hptank):
        self.hptank = hptank
        self.attack_timer = 0.0

    def enter(self, e):
        self.hptank.frame = 0
        self.attack_timer = 0.0
        if isinstance(e, tuple) and len(e) >= 3:
            self.hptank.target = e[2]

    def _collect_objects(self):
        try:
            if hasattr(game_world, 'world'):
                return [o for layer in game_world.world for o in layer]
        except Exception:
            pass
        objs = None
        if hasattr(game_world, 'get_objects') and callable(getattr(game_world, 'get_objects')):
            try:
                objs = game_world.get_objects()
            except Exception:
                objs = None
        if objs is None and hasattr(game_world, 'objects'):
            objs = getattr(game_world, 'objects')
        if objs is None and hasattr(game_world, 'all_objects'):
            objs = getattr(game_world, 'all_objects')
        return objs

    def _find_blocked_target(self):
        objs = self._collect_objects()
        if not objs:
            return None
        for o in list(objs):
            if o is None or o is self.hptank:
                continue
            if getattr(o, '_blocked_by', None) is self.hptank and getattr(o, 'Hp', 1) > 0:
                if game_world.in_attack_range(self.hptank, o):
                    return o
        return None

    def _bb_overlap(self, a_bb, b_bb):
        la, ba, ra, ta = a_bb
        lb, bb, rb, tb = b_bb
        return not (ra < lb or la > rb or ta < bb or ba > tb)

    def _find_colliding_target(self):
        objs = self._collect_objects()
        if not objs:
            return None
        my_bb = None
        if hasattr(self.hptank, 'get_bb'):
            try:
                my_bb = self.hptank.get_bb()
            except Exception:
                my_bb = None
        for o in list(objs):
            if o is None or o is self.hptank:
                continue
            if getattr(o, 'Hp', 0) <= 0:
                continue
            if not hasattr(o, 'get_bb'):
                continue
            try:
                if my_bb is None:
                    my_bb = self.hptank.get_bb()
                if self._bb_overlap(my_bb, o.get_bb()) and game_world.in_attack_range(self.hptank, o):
                    return o
            except Exception:
                continue
        return None

    def exit(self, e):
        self.hptank.frame = 0
        self.attack_timer = 0.0

    def do(self):
        self.hptank.frame = (self.hptank.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 7
        if self.hptank.skill_state is True:
            self.hptank.skill_frame = (
                                                  self.hptank.skill_frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 8
        target = getattr(self.hptank, 'target', None)

        # 타겟이 없거나 범위 밖이면 후보 찾기
        if target is None or not game_world.in_attack_range(self.hptank, target):
            new_target = self._find_blocked_target()
            if new_target is None:
                new_target = self._find_colliding_target()
            if new_target is not None:
                self.hptank.target = new_target
                target = new_target
            else:
                self.hptank.state_machine.handle_state_event(('SEPARATE', None))
                return

        ATTACK_INTERVAL = 0.8
        self.attack_timer += game_framework.frame_time
        if self.attack_timer >= ATTACK_INTERVAL:
            self.attack_timer -= ATTACK_INTERVAL
            dmg = max(0, self.hptank.Atk - getattr(target, 'Def', 0))
            try:
                target.Hp -= dmg
            except Exception:
                pass
            print(f'Hptank attacked Monster dmg={dmg} target_hp={getattr(target, "Hp", "?")}')
            if getattr(target, 'Hp', 1) <= 0:
                print(f'{target.__class__.__name__} died by Hptank.')
                try:
                    if hasattr(target, 'die'):
                        target.die()
                    else:
                        try:
                            game_world.remove_object(target)
                        except Exception:
                            pass
                        try:
                            game_world.remove_collision_object(target)
                        except Exception:
                            pass
                        try:
                            if getattr(target, '_blocked_by', None) is self.hptank:
                                target._blocked_by = None
                                self.hptank.now_stop = max(0, self.hptank.now_stop - 1)
                        except Exception:
                            pass
                except Exception:
                    try:
                        if getattr(target, '_blocked_by', None) is self.hptank:
                            target._blocked_by = None
                            self.hptank.now_stop = max(0, self.hptank.now_stop - 1)
                    except Exception:
                        pass

                next_target = self._find_blocked_target()
                if next_target is None:
                    next_target = self._find_colliding_target()
                if next_target:
                    try:
                        if getattr(next_target, '_blocked_by', None) is None:
                            next_target._blocked_by = self.hptank
                            self.hptank.now_stop = min(self.hptank.stop, self.hptank.now_stop + 1)
                    except Exception:
                        pass
                    self.hptank.target = next_target
                    self.attack_timer = 0.0
                else:
                    self.hptank.target = None
                    self.hptank.state_machine.handle_state_event(('SEPARATE', None))
    def draw(self):
        x = self.hptank.x
        y = self.hptank.y + 50
        if getattr(self.hptank, 'face_dir', 0) == 0:
            self.hptank.image[int(self.hptank.frame)].clip_draw(0, 0, 100, 100, x, y, 150, 160)
            if self.hptank.frame >= 4:
                self.hptank.at_image[int(self.hptank.frame)-4].clip_draw(0, 0, 157, 158, x, y, 150, 160)
        else:
            self.hptank.image[int(self.hptank.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)
            if self.hptank.frame >= 4:
                self.hptank.at_image[int(self.hptank.frame)-4].clip_composite_draw(0, 0, 157, 158, 0, 'h', x, y, 150, 160)
        if self.hptank.skill_state is True:
            self.hptank.sk_image[int(self.hptank.skill_frame)].clip_draw(0, 0, 116, 86, x, y-20, 150, 160)

class Hptank:
    image = []
    at_image = []
    sk_image = []
    for i in range(8):
        image.append(None)
    for i in range(3):
        at_image.append(None)
    for i in range(9):
        sk_image.append(None)
    def __init__(self):
        self.depth = 0
        self.x, self.y = 0, 0
        self.frame = 0
        self.skill_frame = 0
        self.face_dir = 0
        self.stop = 4
        self.now_stop = 0
        self.max_hp = 2000
        self.Hp = 2000
        self.Def = 30
        self.Atk = 60
        self.number = 3
        self.skill = 10
        self._skill_timer = 0.0
        self.skill_state = False
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        self.font = load_font('ENCR10B.TTF', 30)
        if self.image[0] is None:
            self.image[0] = load_image('klat01_01.png')
            self.image[1] = load_image('klat01_02.png')
            self.image[2] = load_image('klat01_03.png')
            self.image[3] = load_image('klat01_04.png')
            self.image[4] = load_image('klat01_05.png')
            self.image[5] = load_image('klat01_06.png')
            self.image[6] = load_image('klat01_07.png')
            self.at_image[0] = load_image('hp_at_ef_01.png')
            self.at_image[1] = load_image('hp_at_ef_02.png')
            self.at_image[2] = load_image('hp_at_ef_03.png')

            self.sk_image[0] = load_image('klat_skill1.png')
            self.sk_image[1] = load_image('klat_skill2.png')
            self.sk_image[2] = load_image('klat_skill3.png')
            self.sk_image[3] = load_image('klat_skill4.png')
            self.sk_image[4] = load_image('klat_skill5.png')
            self.sk_image[5] = load_image('klat_skill6.png')
            self.sk_image[6] = load_image('klat_skill7.png')
            self.sk_image[7] = load_image('klat_skill8.png')

        self.IDLE = Idle(self)
        self.ATK = Attack(self)

        def _on_collide(ev):
            return isinstance(ev, tuple) and len(ev) >= 3 and ev[0] == 'COLLIDE' and isinstance(ev[2], object)
        def _on_separate(ev):
            return isinstance(ev, tuple) and len(ev) >= 1 and ev[0] == 'SEPARATE'

        # ATK 상태에서 중복 COLLIDE 이벤트를 무시하려면 ATK에 _on_collide를 자기 자신으로 매핑 가능
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE : { _on_collide: self.ATK },
                self.ATK  : { _on_separate: self.IDLE, _on_collide: self.ATK }
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
        for i in range(int((self.Hp / 2000) * 100 // 10)):
            self.font.draw(self.x - 50 + i * 10, self.y + 80, f'/', (100, 250, 100))

    def get_bb(self):
        return self.x - 40, self.y - 40, self.x + 40, self.y + 40

    def on_hit_by_monster(self, attacker):
        """몬스터에게 피격되었을 때 호출된다."""
        # 이미 공격 중이면 굳이 Idle -> Attack 전환 시도 안 함
        if self.state_machine.cur_state is self.ATK:
            return

        # 공격 가능한 범위 안인지 확인
        try:
            if not game_world.in_attack_range(self, attacker):
                return
        except Exception:
            return

        # 현재 타겟이 없을 때만 이 몬스터를 타겟으로 삼고 공격 상태 진입
        if getattr(self, 'target', None) is None:
            try:
                self.target = attacker
            except Exception:
                pass
            try:
                # Idle 상태에서 몬스터에게 공격받으면 ATK 상태로 넘기기 위한 이벤트
                self.state_machine.handle_state_event(('COLLIDE', 'DPTANK:MONSTER', attacker))
            except Exception:
                pass

    def handle_collision(self, group, other):
        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()

        # other 방어 코드(원래 써둔 부분 유지)
        if other is None:
            return
        try:
            if getattr(other, 'Hp', 0) <= 0:
                return
        except Exception:
            return

        # 이미 다른 유닛에 의해 저지된 몬스터는 건드리지 않음
        if getattr(other, '_blocked_by', None) is not None:
            return

        # HPTANK ↔ MONSTER 충돌만 특수 처리
        if (left == 'HPTANK' and right == 'MONSTER') or (left == 'MONSTER' and right == 'HPTANK'):
            # 아직 여유가 있을 때만 새 몬스터를 저지하고 이벤트를 쏜다
            if self.now_stop < self.stop:
                other._blocked_by = self
                self.now_stop += 1
                if getattr(self, 'target', None) is None:
                    self.target = other
                try:
                    self.state_machine.handle_state_event(('COLLIDE', group, other))
                except Exception:
                    pass
            # 여유가 없으면 아무것도 하지 않고 통과시킴
            return

        # fallback (Dptank 와 동일하게)
        if self.now_stop < self.stop:
            other._blocked_by = self
            self.now_stop += 1
            if getattr(self, 'target', None) is None:
                self.target = other
            try:
                self.state_machine.handle_state_event(('COLLIDE', group, other))
            except Exception:
                pass
        return

    def update(self):
        self.state_machine.update()
        try:
            dt = game_framework.frame_time
        except Exception:
            dt = 0.0

        if self.skill_state is True:
            self._skill_timer += dt
            while self._skill_timer >= 1.0 and self.skill > 0:
                # 스킬 게이지 감소
                self.skill = max(0, self.skill - 1)

                # Hp 회복: 최대 Hp 를 넘지 않도록 clamp
                if self.Hp < self.max_hp:
                    self.Hp = min(self.max_hp, self.Hp + 100)

                self._skill_timer -= 1.0

                # 스킬 소진 시 종료
                if self.skill == 0:
                    self.skill_state = False
                    break

        else:
            self._skill_timer += dt
            while self._skill_timer >= 1.0 and self.skill < 10:
                self.skill = min(10, self.skill + 1)
                self._skill_timer -= 1.0
    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))