from pico2d import load_image, load_font

import game_framework
import game_world
from state_machine import StateMachine
from link_helper import update_link_states_for_dptank_vanguard
from unit_collision_helper import handle_unit_vs_monster_collision


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
            # event 형식: ('COLLIDE', group, other)
            self.vanguard.target = e[2]
    def exit(self, e):
        self.vanguard.frame = 0
        self.attack_timer = 0.0
        tgt = getattr(self.vanguard, 'target', None)
        # 내가 직접 저지하던 타깃이면 now_stop 감소 및 block 해제
        try:
            if tgt is not None and getattr(tgt, '_blocked_by', None) is self.vanguard:
                try:
                    self.vanguard.now_stop = max(0, self.vanguard.now_stop - 1)
                except Exception:
                    pass
                try:
                    tgt._blocked_by = None
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self.vanguard.target = None
        except Exception:
            pass

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

    def _bb_overlap(self, a_bb, b_bb):
        la, ba, ra, ta = a_bb
        lb, bb, rb, tb = b_bb
        return not (ra < lb or la > rb or ta < bb or ba > tb)

    def _find_blocked_target(self):
        objs = self._collect_objects()
        if not objs:
            return None
        for o in list(objs):
            if o is None or o is self.vanguard:
                continue
            if getattr(o, '_blocked_by', None) is self.vanguard and getattr(o, 'Hp', 1) > 0:
                try:
                    if game_world.in_attack_range(self.vanguard, o):
                        return o
                except Exception:
                    continue
        return None

    def _find_colliding_target(self):
        objs = self._collect_objects()
        if not objs:
            return None
        my_bb = None
        if hasattr(self.vanguard, 'get_bb'):
            try:
                my_bb = self.vanguard.get_bb()
            except Exception:
                my_bb = None
        for o in list(objs):
            if o is None or o is self.vanguard:
                continue
            if getattr(o, 'Hp', 0) <= 0:
                continue
            if not hasattr(o, 'get_bb'):
                continue
            try:
                if my_bb is None:
                    my_bb = self.vanguard.get_bb()
                if self._bb_overlap(my_bb, o.get_bb()) and game_world.in_attack_range(self.vanguard, o):
                    return o
            except Exception:
                continue
        return None

    def do(self):
        # 애니 프레임 업데이트
        self.vanguard.frame = (self.vanguard.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 5
        target = getattr(self.vanguard, 'target', None)

        # 현재 타깃이 죽었거나 world에서 사라졌거나, 범위 밖이면 정리하고 새 타깃 탐색
        try:
            if target is not None:
                died = getattr(target, 'Hp', 0) <= 0
                try:
                    in_world = any(target in layer for layer in game_world.world)
                except Exception:
                    in_world = False
                if died or not in_world or not game_world.in_attack_range(self.vanguard, target):
                    try:
                        if getattr(target, '_blocked_by', None) is self.vanguard:
                            target._blocked_by = None
                            self.vanguard.now_stop = max(0, self.vanguard.now_stop - 1)
                    except Exception:
                        pass
                    target = None
                    self.vanguard.target = None
        except Exception:
            pass

        # 유효 타깃이 없으면 새로 찾기 (먼저 내가 막고 있던 타깃, 없으면 단순 충돌 타깃)
        if target is None:
            new_target = self._find_blocked_target()
            if new_target is None:
                new_target = self._find_colliding_target()
            if new_target is not None:
                self.vanguard.target = new_target
                target = new_target
            else:
                # 더 이상 때릴 수 있는 몬스터가 없으면 Attack 상태 종료
                self.vanguard.state_machine.handle_state_event(('SEPARATE', None))
                return

        # 공격 간격
        ATTACK_INTERVAL = 0.8
        if self.vanguard.skill > 0:
            ATTACK_INTERVAL = 0.4
        self.attack_timer += game_framework.frame_time
        if self.attack_timer < ATTACK_INTERVAL:
            return
        self.attack_timer -= ATTACK_INTERVAL

        # 실제 공격 수행
        dmg = max(0, self.vanguard.Atk - getattr(target, 'Def', 0))
        try:
            target.Hp -= dmg
        except Exception:
            pass
        print(f'Vanguard attacked Monster dmg={dmg} target_hp={getattr(target, "Hp", "?")}')

        # skill이 있는 상태라면 코스트 1 증가 (기존 기능 유지)
        if self.vanguard.skill > 0:
            try:
                import sys
                char = None
                for mod_name in ('stage02', 'stage01'):
                    mod = sys.modules.get(mod_name)
                    if mod:
                        c = getattr(mod, 'character', None)
                        if c is not None:
                            char = c
                            break
                if char is None:
                    import game_world as _gw
                    for layer in getattr(_gw, 'world', []):
                        for obj in list(layer):
                            if getattr(obj, '__class__', None) and obj.__class__.__name__ == 'Character':
                                char = obj
                                break
                        if char:
                            break
                if char is not None:
                    try:
                        char.cost += 1
                    except Exception:
                        pass
            except Exception:
                pass

        # 타깃이 죽었으면 정리 후 새 타깃 찾기
        if getattr(target, 'Hp', 1) <= 0:
            print(f'{target.__class__.__name__} died by Vanguard.')
            try:
                if hasattr(target, 'die'):
                    target.die()
            except Exception:
                pass
            try:
                game_world.remove_object(target)
            except Exception:
                pass
            try:
                game_world.remove_collision_object(target)
            except Exception:
                pass
            try:
                if getattr(target, '_blocked_by', None) is self.vanguard:
                    target._blocked_by = None
                    self.vanguard.now_stop = max(0, self.vanguard.now_stop - 1)
            except Exception:
                pass

            next_target = self._find_blocked_target()
            if next_target is None:
                next_target = self._find_colliding_target()
            if next_target:
                try:
                    if getattr(next_target, '_blocked_by', None) is None:
                        next_target._blocked_by = self.vanguard
                        self.vanguard.now_stop = min(self.vanguard.stop, self.vanguard.now_stop + 1)
                except Exception:
                    pass
                self.vanguard.target = next_target
                self.attack_timer = 0.0
            else:
                self.vanguard.target = None
                self.vanguard.state_machine.handle_state_event(('SEPARATE', None))
                return

    def draw(self):
        x = self.vanguard.x
        y = self.vanguard.y + 50
        if getattr(self.vanguard, 'face_dir', 0) == 0 or getattr(self.vanguard, 'face_dir', 0) == 2:
            self.vanguard.image[int(self.vanguard.frame) + 1].clip_draw(0, 0, 100, 100, x, y, 150, 160)
            if hasattr(self.vanguard, 'image_at') and self.vanguard.frame >= 3 and len(self.vanguard.image_at) > 0:
                idx = min(len(self.vanguard.image_at) - 1, int(self.vanguard.frame) - 3)
                self.vanguard.image_at[idx].clip_draw(0, 0, 124, 117, x + 50, y - 20, 100, 160)
        else:
            self.vanguard.image[int(self.vanguard.frame) + 1].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)
            if hasattr(self.vanguard, 'image_at') and self.vanguard.frame >= 3 and len(self.vanguard.image_at) > 0:
                idx = min(len(self.vanguard.image_at) - 1, int(self.vanguard.frame) - 3)
                self.vanguard.image_at[idx].clip_composite_draw(0, 0, 124, 117, 0, 'h', x - 50, y - 20, 150, 160)

class Vanguard:
    image = []
    image_at = []
    image_s = None
    image_l = None
    for i in range(8):
        image.append(None)
    for i in range(3):
        image_at.append(None)

    def __init__(self):
        self.depth = 0
        self.x, self.y = 0, 0
        self.frame = 0
        self.face_dir = 0
        self.stop = 2
        self.now_stop = 0
        self.max_hp = 700
        self.Hp = 700
        self.Def = 10
        self.Atk = 60
        self.skill = 15
        self._skill_timer = 0.0
        self.number = 6
        self.linked = False
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        self.font = load_font('ENCR10B.TTF', 30)

        if self.image[0] is None:
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
        if self.image_l is None:
            self.image_l = load_image('asha_link.png')
        if self.image_at[0] is None:
            try:
                self.image_at[0] = load_image('va_at_ef_01.png')
                self.image_at[1] = load_image('va_at_ef_02.png')
                self.image_at[2] = load_image('va_at_ef_03.png')
            except Exception:
                self.image_at = []
        if self.image_s is None:
            self.image_s = load_image('asha_skill.png')

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
        if self.skill > 0:
            self.image_s.clip_draw(0, 0, 129, 136, self.x, self.y + 90, 100, 100)
        for i in range(int((self.Hp/self.max_hp)*100//10)):
            self.font.draw(self.x-50+i*10, self.y+80, f'/', (100, 250, 100))

    def update(self):
        self.state_machine.update()
        try:
            dt = game_framework.frame_time
        except Exception:
            dt = 0.0

        # Dptank-Vanguard 링크 상태 자동 갱신
        try:
            update_link_states_for_dptank_vanguard()
        except Exception:
            pass

        # 링크 상태에 따라 방어력 조정
        if getattr(self, 'linked', False):
            self.Def = 50
        else:
            self.Def = 10

        if dt > 0.0:
            self._skill_timer += dt
            if self.skill > 0:
                dec = int(self._skill_timer)
                if dec > 0:
                    self.skill = max(0.0, self.skill - dec)
                    self._skill_timer -= dec

    def get_bb(self):
        return self.x - 40, self.y - 40, self.x + 40, self.y + 40

    def handle_collision(self, group, other):
        # depth 0 유닛 공통 보조 함수로 저지/상태 전환 처리
        blocked = handle_unit_vs_monster_collision(self, group, other)
        return

    def on_hit_by_monster(self, attacker):
        """몬스터에게 피격되었을 때 호출된다."""
        if self.state_machine.cur_state is self.ATK:
            return
        try:
            if not game_world.in_attack_range(self, attacker):
                return
        except Exception:
            return
        if getattr(self, 'target', None) is None:
            try:
                self.target = attacker
            except Exception:
                pass
            try:
                self.state_machine.handle_state_event(('COLLIDE', 'VANGUARD:MONSTER', attacker))
            except Exception:
                pass