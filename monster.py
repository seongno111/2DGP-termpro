# python
from pico2d import load_image, get_canvas_height

import game_framework
import game_world
import stage01
from Tile import Tile
from state_machine import StateMachine

PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel 30 cm
RUN_SPEED_KMPH = 20.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

TIME_PER_ACTION = 0.8
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 2
FRAMES_PER_ACTION_ac = 3

class Idle:
    def __init__(self, monster):
        self.monster = monster
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        # 경로가 없을 때만 기본 전진 동작을 수행하도록 변경 (경로 따라갈 때 간섭 방지)
        if not getattr(self.monster, 'path', None) or self.monster.path_idx >= len(self.monster.path):
            self.monster.x += RUN_SPEED_PPS * game_framework.frame_time
            self.monster.frame = (self.monster.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 2
        else:
            # 경로가 있으면 애니메이션만 업데이트 (이동은 update()의 경로 로직에서 처리)
            self.monster.frame = (self.monster.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 2
    def draw(self):
        x = self.monster.x
        y = self.monster.y + 30
        face = getattr(self.monster, 'face_dir', 0)
        if face == 0:
            self.monster.image[int(self.monster.frame)].clip_draw(0, 0, 100, 100, x, y, 150, 150)
        else:
            self.monster.image[int(self.monster.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 150)



class Atack_state:
    def __init__(self, monster):
        self.monster = monster
        self.attack_timer = 0.0
    def enter(self, e):
        self.monster.frame = 0
        self.attack_timer = 0.0
        # 공격 상태 진입 플래그 설정
        try:
            self.monster.is_attacking = True
        except Exception:
            pass
        if isinstance(e, tuple) and len(e) >= 3:
            self.monster.target = e[2]
        else:
            self.monster.target = None

    def exit(self, e):
        self.monster.frame = 0
        self.attack_timer = 0.0
        # 공격 상태 종료 플래그 해제
        try:
            self.monster.is_attacking = False
        except Exception:
            pass
        # 저지했던 유닛의 now_stop 감소 처리
        try:
            blocked = getattr(self.monster, '_blocked_by', None)
            if blocked is not None and hasattr(blocked, 'now_stop'):
                blocked.now_stop = max(0, blocked.now_stop - 1)
                # 만약 blocked 유닛의 현재 타겟이 이 몬스터면 정리
                try:
                    if getattr(blocked, 'target', None) is self.monster:
                        blocked.target = None
                except Exception:
                    pass
            self.monster._blocked_by = None
        except Exception:
            pass
    def do(self):
        self.monster.frame = (self.monster.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 3
        target = getattr(self.monster, 'target', None)

        # 대상이 없거나 충돌이 끊기면 SEPARATE 발생
        if target is None or not game_world.collide(self.monster, target):
            self.monster.state_machine.handle_state_event(('SEPARATE', None))
            return

        # 공격 간격 (초)
        ATTACK_INTERVAL = 0.8
        self.attack_timer += game_framework.frame_time
        if self.attack_timer >= ATTACK_INTERVAL:
            self.attack_timer -= ATTACK_INTERVAL

            dmg = max(0, self.monster.Atk - getattr(target, 'Def', 0))
            # 체력 감소
            try:
                target.Hp -= dmg
            except Exception:
                pass
            print(
                f'Monster({self.monster.num}) attacked {target.__class__.__name__} dmg={dmg} target_hp={getattr(target, "Hp", "?")}')
            if getattr(target, 'Hp', 1) <= 0:
                print(f'{target.__class__.__name__} died.')
                try:
                    if hasattr(target, '_overlay'):
                        game_world.remove_object(target._overlay)
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
                    import stage01
                    ch = getattr(stage01, 'character', None)
                    if ch is not None:
                        key = getattr(target, '_placed_key', None)
                        idx = getattr(target, '_placed_idx', None)
                        if key:
                            ch.unit_placed[key] = False
                        if idx is not None and idx in ch.occupied_tiles:
                            ch.occupied_tiles.remove(idx)
                except Exception:
                    pass

                self.monster.target = None
                self.monster.state_machine.handle_state_event(('SEPARATE', None))

    def draw(self):
        x = self.monster.x
        y = self.monster.y + 30
        face = getattr(self.monster, 'face_dir', 0)
        if face == 0:
            self.monster.image[int(self.monster.frame)].clip_draw(0, 0, 100, 100, x, y, 150, 150)
        else:
            self.monster.image[int(self.monster.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 150)

class Monster:
    image = []
    image.append(None)
    image.append(None)
    image.append(None)
    def __init__(self, num, path=None):
        self.num = num
        col = num % 10
        row = num // 10
        tw, th = Tile.TILE_W, Tile.TILE_H
        canvas_h = get_canvas_height()
        tile_cx = col * tw + tw // 2
        tile_cy = canvas_h - (row * th + th // 2)
        self.dead = False
        self.x, self.y = tile_cx, tile_cy
        self.Hp = 300
        self.Def = 5
        self.removed = False
        self.state_machine = None
        self.Atk = 50
        self.frame = 0
        self.face_dir = 0
        self.target = None

        # path: list of (x,y) coords — 몬스터는 이 경로를 따라감
        self.path = path if path is not None else None
        self.path_idx = 0
        self.is_attacking = False

        if self.image[0] is None:
            self.image[0] = load_image('brownbear_01.png')
            self.image[1] = load_image('brownbear_02.png')
            self.image[2] = load_image('brownbear_03.png')
        self.IDLE = Idle(self)
        self.ATK = Atack_state(self)

        def _on_collide(ev):
            return isinstance(ev, tuple) and len(ev) >= 3 and ev[0] == 'COLLIDE'

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
        unit_groups = ['KNIGHT', 'ARCHER', 'HPTANK', 'DPTANK', 'HEALER', 'VANGUARD']
        for ug in unit_groups:
            game_world.add_collision_pair(f'{ug}:MONSTER', None, self)
        try:
            for group, pairs in list(game_world.collision_pairs.items()):
                left, right = (group.split(':') + ['', ''])[:2]
                left = left.strip().upper()
                right = right.strip().upper()
                # 그룹의 오른쪽이 MONSTER인데 몬스터가 없으면 추가
                if right == 'MONSTER':
                    if self not in pairs[1]:
                        pairs[1].append(self)
                # 그룹의 왼쪽이 MONSTER인 경우(혹시 반대로 등록된 그룹)도 처리
                if left == 'MONSTER':
                    if self not in pairs[0]:
                        pairs[0].append(self)
        except Exception:
            pass


    def update(self):
        # 공격 상태이면 경로 이동을 하지 않음
        if not getattr(self, 'is_attacking', False):
            # 경로가 있으면 경로 따라 이동 (속도 기반)
            if getattr(self, 'path', None) and self.path_idx < len(self.path):
                try:
                    tx, ty = self.path[self.path_idx]
                    dx = tx - self.x
                    dy = ty - self.y
                    dist = (dx * dx + dy * dy) ** 0.5
                    step = RUN_SPEED_PPS * game_framework.frame_time
                    # face_dir 설정 (오른쪽 0 / 왼쪽 1) : x 이동 기준
                    try:
                        if abs(dx) > 1e-6:
                            self.face_dir = 0 if dx > 0 else 1
                    except Exception:
                        pass
                    if dist <= 1e-6 or step >= dist:
                        # 다음 포인트로 도달
                        self.x, self.y = tx, ty
                        self.path_idx += 1
                    else:
                        self.x += dx / dist * step
                        self.y += dy / dist * step
                except Exception:
                    pass
                try:
                    # 타일 높이로 depth 결정 (기존 스테이지에서 사용하던 100 또는 Tile.TILE_H 사용)
                    tile_h = getattr(Tile, 'TILE_H', 100)
                    canvas_h = get_canvas_height()
                    desired_depth = int((canvas_h - self.y) // tile_h)
                    # clamp
                    desired_depth = max(0, min(desired_depth, len(game_world.world) - 1))

                    # 현재 레이어 인덱스 검색
                    current_idx = None
                    for i, layer in enumerate(game_world.world):
                        if self in layer:
                            current_idx = i
                            break

                    if current_idx is None:
                        # 월드에 아직 없으면 안전하게 추가
                        try:
                            game_world.add_object(self, desired_depth)
                        except Exception:
                            pass
                    elif current_idx != desired_depth:
                        # 레이어 변경
                        try:
                            game_world.change_object_depth(self, desired_depth)
                        except Exception:
                            # fallback: 직접 제거/추가
                            try:
                                game_world.remove_object(self)
                                game_world.add_object(self, desired_depth)
                            except Exception:
                                pass
                except Exception:
                    pass

        # 상태머신 업데이트 (공격 등)
        try:
            self.state_machine.update()
        except Exception:
            pass

        # 경계 처리 유지
        if self.x > 950:
            try:
                game_world.remove_object(self)
            except Exception:
                pass
            try:
                game_world.remove_collision_object(self)
            except Exception:
                pass
    def die(self):
        try:
            blocked = getattr(self, '_blocked_by', None)
            if blocked is not None and hasattr(blocked, 'now_stop'):
                blocked.now_stop = max(0, blocked.now_stop - 1)
        except Exception:
            pass

        if self.removed:
            return
        self.removed = True

        try:
            game_world.remove_object(self)
        except Exception:
            try:
                for layer in list(game_world.world):
                    if self in layer:
                        layer.remove(self)
            except Exception:
                pass

        try:
            game_world.remove_collision_object(self)
        except Exception:
            pass

        # 활성 스테이지 모듈을 찾아 해당 killed_monster 증가
        try:
            import sys
            incremented = False
            for mod_name in ('stage01', 'stage02'):
                mod = sys.modules.get(mod_name)
                if not mod:
                    continue
                ch = getattr(mod, 'character', None)
                if ch is None:
                    continue
                try:
                    in_world = any(ch in layer for layer in game_world.world)
                except Exception:
                    in_world = False
                if in_world:
                    try:
                        mod.killed_monster = getattr(mod, 'killed_monster', 0) + 1
                        print(f'[MONSTER_DIE] {mod_name}.killed_monster={mod.killed_monster}')
                        incremented = True
                        break
                    except Exception:
                        pass

            if not incremented:
                # 폴백: stage02 먼저, 없으면 stage01
                for fb in ('stage02', 'stage01'):
                    try:
                        mod = __import__(fb)
                        mod.killed_monster = getattr(mod, 'killed_monster', 0) + 1
                        print(f'[MONSTER_DIE] fallback {fb}.killed_monster={mod.killed_monster}')
                        break
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            if hasattr(self, 'state_machine') and self.state_machine is not None:
                self.state_machine = None
        except Exception:
            pass
    def draw(self):
        self.state_machine.draw()

    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50
    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))

    def handle_collision(self, group, other):
        try:
            if other is None:
                return
            if not any(other in layer for layer in game_world.world):
                return
        except Exception:
            return

        if getattr(self, 'Hp', 1) <= 0 or self.removed:
            return

        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()

        # 상대가 이미 다른 유닛에 의해 저지되어 있으면 통과시킨다
        if getattr(other, '_blocked_by', None) is not None:
            return

        # 상대 유닛이 더 이상 추가 저지를 받을 수 없는 상태면 통과시킨다
        if getattr(other, 'now_stop', 0) >= getattr(other, 'stop', 0):
            return
        # 공격자 이름을 대문자로 맞춤하여 비교
        attackers = {'KNIGHT', 'DPTANK', 'VANGUARD', 'HPTANK', 'ARCHER'}
        if (left in attackers and right == 'MONSTER') or (right in attackers and left == 'MONSTER'):
            try:
                if getattr(self, 'target', None) is other:
                    return
                self.target = other
                if hasattr(self, 'state_machine') and self.state_machine is not None:
                    try:
                        self.state_machine.handle_state_event(('COLLIDE', group, other))
                    except Exception:
                        pass
            except Exception:
                pass
            return

        # 기본 폴백: 다른 그룹과의 충돌도 처리
        try:
            if getattr(self, 'target', None) is other:
                return
            self.target = other
            if hasattr(self, 'state_machine') and self.state_machine is not None:
                try:
                    self.state_machine.handle_state_event(('COLLIDE', group, other))
                except Exception:
                    pass
        except Exception:
            pass
        return