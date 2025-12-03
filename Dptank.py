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
# python
# python
class Attack:
    def __init__(self, dptank):
        self.dptank = dptank
        self.attack_timer = 0.0

    def enter(self, e):
        self.dptank.frame = 0
        self.attack_timer = 0.0
        if isinstance(e, tuple) and len(e) >= 3:
            self.dptank.target = e[2]

    def _collect_objects(self):
        # 우선적으로 game_world.world 플래트닝 사용
        try:
            if hasattr(game_world, 'world'):
                return [o for layer in game_world.world for o in layer]
        except Exception:
            pass
        # 기존 시도들 (호환성)
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
            if o is None or o is self.dptank:
                continue
            if getattr(o, '_blocked_by', None) is self.dptank and getattr(o, 'Hp', 1) > 0:
                if game_world.in_attack_range(self.dptank, o):
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
        if hasattr(self.dptank, 'get_bb'):
            try:
                my_bb = self.dptank.get_bb()
            except Exception:
                my_bb = None
        for o in list(objs):
            if o is None or o is self.dptank:
                continue
            if getattr(o, 'Hp', 0) <= 0:
                continue
            if not hasattr(o, 'get_bb'):
                continue
            try:
                if my_bb is None:
                    my_bb = self.dptank.get_bb()
                if self._bb_overlap(my_bb, o.get_bb()) and game_world.in_attack_range(self.dptank, o):
                    return o
            except Exception:
                continue
        return None

    def exit(self, e):
        self.dptank.frame = 0
        self.attack_timer = 0.0

    def do(self):
        self.dptank.frame = (self.dptank.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 4
        target = getattr(self.dptank, 'target', None)

        # 타겟이 없거나 범위 밖이면 후보 찾기
        if target is None or not game_world.in_attack_range(self.dptank, target):
            new_target = self._find_blocked_target()
            if new_target is None:
                new_target = self._find_colliding_target()
            if new_target is not None:
                self.dptank.target = new_target
                target = new_target
            else:
                self.dptank.state_machine.handle_state_event(('SEPARATE', None))
                return

        ATTACK_INTERVAL = 0.8
        self.attack_timer += game_framework.frame_time
        if self.attack_timer >= ATTACK_INTERVAL:
            self.attack_timer -= ATTACK_INTERVAL
            dmg = max(0, self.dptank.Atk - getattr(target, 'Def', 0))
            try:
                target.Hp -= dmg
            except Exception:
                pass
            print(f'Dptank attacked Monster dmg={dmg} target_hp={getattr(target, "Hp", "?")}')
            if getattr(target, 'Hp', 1) <= 0:
                print(f'{target.__class__.__name__} died by Dptank.')
                # 먼저 가능하면 target.die() 호출해서 몬스터 쪽 정리(특히 blocked 감소) 처리
                try:
                    if hasattr(target, 'die'):
                        target.die()
                    else:
                        # fallback: 직접 제거
                        try:
                            game_world.remove_object(target)
                        except Exception:
                            pass
                        try:
                            game_world.remove_collision_object(target)
                        except Exception:
                            pass
                        # 제거 시 now_stop 정리 (대상이 나를 막고 있었으면 감소)
                        try:
                            if getattr(target, '_blocked_by', None) is self.dptank:
                                target._blocked_by = None
                                self.dptank.now_stop = max(0, self.dptank.now_stop - 1)
                        except Exception:
                            pass
                except Exception:
                    # 안전하게 보정 시도
                    try:
                        if getattr(target, '_blocked_by', None) is self.dptank:
                            target._blocked_by = None
                            self.dptank.now_stop = max(0, self.dptank.now_stop - 1)
                    except Exception:
                        pass

                # 죽인 뒤 다른 충돌 대상(블록된 대상 우선, 없으면 실제 충돌중인 대상) 있으면 전환, 없으면 SEPARATE
                next_target = self._find_blocked_target()
                if next_target is None:
                    next_target = self._find_colliding_target()
                if next_target:
                    # 새 타겟이 아직 blocked_by가 없다면 강제로 설정(중복 카운트 방지)
                    try:
                        if getattr(next_target, '_blocked_by', None) is None:
                            next_target._blocked_by = self.dptank
                            # only increment now_stop if it wasn't counted already
                            # (we can't know previous state reliably, so try to keep safe)
                            self.dptank.now_stop = min(self.dptank.stop, self.dptank.now_stop + 1)
                    except Exception:
                        pass
                    self.dptank.target = next_target
                    self.attack_timer = 0.0
                else:
                    self.dptank.target = None
                    self.dptank.state_machine.handle_state_event(('SEPARATE', None))

    def draw(self):
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
        self.stop = 4
        self.now_stop = 0
        self.max_hp = 1500
        self.Hp = 1000
        self.Def = 30
        self.Atk = 60
        self.number = 4
        self.skill = 10
        self._skill_timer = 0.0
        self.skill_state = False
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
        return self.x - 40, self.y - 40, self.x + 40, self.y + 40

    def handle_collision(self, group, other):
        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()

        # 이미 다른 유닛에 의해 저지되었으면 패스
        if getattr(other, '_blocked_by', None) is not None:
            return

        if (left == 'DPTANK' and right == 'MONSTER') or (left == 'MONSTER' and right == 'DPTANK'):
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
        # fallback
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


    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))