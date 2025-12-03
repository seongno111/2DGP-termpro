from pico2d import *
from sdl2 import SDL_BUTTON_LEFT, SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP, SDL_MOUSEMOTION, SDL_GetMouseState
from ctypes import c_int
from collections import OrderedDict

import game_framework
import game_world
import stage01
from state_machine import StateMachine

from Knight import Knight
from Archer import Archer
from Hptank import Hptank
from Dptank import Dptank
from Healer import Healer
from Vanguard import Vanguard

def left_m_down(e):
    return isinstance(e, tuple) and len(e) >= 2 and e[0] == 'INPUT' and getattr(e[1], 'type', None) == SDL_MOUSEBUTTONDOWN and getattr(e[1], 'button', None) == SDL_BUTTON_LEFT

def left_m_up(e):
    return isinstance(e, tuple) and len(e) >= 2 and e[0] == 'INPUT' and getattr(e[1], 'type', None) == SDL_MOUSEBUTTONUP and getattr(e[1], 'button', None) == SDL_BUTTON_LEFT

def _get_mouse_pos(ev):
    """SDL 이벤트에서 안전하게 (mx, my) 반환. pico2d 기준(Y 위쪽 증가)으로 보정함."""
    if ev is None:
        return 0, 0
    if hasattr(ev, 'button') and getattr(ev.button, 'x', None) is not None and getattr(ev.button, 'y', None) is not None:
        mx = int(ev.button.x); my_raw = int(ev.button.y)
    elif hasattr(ev, 'motion') and getattr(ev.motion, 'x', None) is not None and getattr(ev.motion, 'y', None) is not None:
        mx = int(ev.motion.x); my_raw = int(ev.motion.y)
    elif getattr(ev, 'x', None) is not None and getattr(ev, 'y', None) is not None:
        mx = int(getattr(ev, 'x')); my_raw = int(getattr(ev, 'y'))
    else:
        x = c_int(); y = c_int()
        try:
            SDL_GetMouseState(x, y)
            mx, my_raw = x.value, y.value
        except Exception:
            return 0, 0
    try:
        my = get_canvas_height() - my_raw
    except Exception:
        my = my_raw
    return mx, my

class BorderOverlay:
    def __init__(self, unit):
        self.unit = unit
    def draw(self):
        if hasattr(self.unit, 'get_at_bound'):
            draw_rectangle(*self.unit.get_at_bound())
    def update(self):
        pass

class Decide:
    def __init__(self, character):
        self.character = character
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        pass
    def draw(self):
        self.character.draw()

class Place:
    def __init__(self, character):
        self.character = character
    def enter(self, e):
        print("ENTER PLACING")
    def exit(self, e):
        pass
    def do(self):
        pass
    def draw(self):
        self.character.draw()

class Idle:
    def __init__(self, character):
        self.character = character
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        pass
    def draw(self):
        self.character.draw()

class Character:
    k_p_image = None
    a_p_image = None
    h_p_image = None
    d_p_image = None
    s_p_image = None
    v_p_image = None
    ch_num = 0
    placing = False

    # 숫자->키 매핑
    NUM_TO_KEY = {
        1: 'knight',
        2: 'archer',
        3: 'hptank',
        4: 'dptank',
        5: 'healer',
        6: 'vanguard'
    }

    def __init__(self, allowed_numbers=None):
        self.p_y = 50
        self.font = load_font('ENCR10B.TTF', 32)
        self.cost = 40

        # portraits 로드(한번만)
        if self.k_p_image is None:
            self.k_p_image = load_image('Knight_portrait.png')
        if self.a_p_image is None:
            self.a_p_image = load_image('Archer_portrait.png')
        if self.h_p_image is None:
            self.h_p_image = load_image('Hptank_portrait.png')
        if self.d_p_image is None:
            self.d_p_image = load_image('Dptank_portrait.png')
        if self.s_p_image is None:
            self.s_p_image = load_image('Healer_portrait.png')
        if self.v_p_image is None:
            self.v_p_image = load_image('Vanguard_portrait.png')

        # 기본 순서
        full_keys_order = ['knight','archer','hptank','dptank','healer','vanguard']

        # allowed_numbers가 주어지면 숫자->키로 변환, 없으면 전체 허용
        if allowed_numbers:
            selected_keys = []
            for n in allowed_numbers:
                k = self.NUM_TO_KEY.get(n)
                if k and k not in selected_keys:
                    selected_keys.append(k)
            if not selected_keys:
                selected_keys = full_keys_order
        else:
            selected_keys = full_keys_order

        # 사용할 유닛 클래스/이미지/비용 매핑
        class_map = {
            'knight': (Knight, self.k_p_image, 19),
            'archer': (Archer, self.a_p_image, 14),
            'hptank': (Hptank, self.h_p_image, 22),
            'dptank': (Dptank, self.d_p_image, 22),
            'healer': (Healer, self.s_p_image, 14),
            'vanguard': (Vanguard, self.v_p_image, 12),
        }

        # portrait x 재배치 (선택된 순서대로)
        base_positions = [50, 150, 250, 350, 450, 550]
        self.unit_map = OrderedDict()
        for i, key in enumerate(selected_keys):
            cls, img, cost = class_map[key]
            x = base_positions[i] if i < len(base_positions) else base_positions[-1] + 100*(i-len(base_positions)+1)
            self.unit_map[key] = {'x': x, 'image': img, 'class': cls, 'cost': cost}

        self.placing_unit = None
        self._placed_unit = None
        self.unit_placed = {key: False for key in self.unit_map.keys()}

        # ----- state handlers (일반화) -----
        def _left_up_if_placing(e):
            if left_m_up(e) and self.placing_unit is not None:
                print("LEFT UP -> PLACING 트리거 (placing remains until placed)")
                return True
            return False

        def _portrait_mouse_down(ev_tuple):
            if not left_m_down(ev_tuple):
                return False
            ev = ev_tuple[1]
            mx, my = _get_mouse_pos(ev)
            for key, info in self.unit_map.items():
                x = info['x']
                if x - 50 <= mx <= x + 50 and self.p_y - 50 <= my <= self.p_y + 50:
                    if self.unit_placed.get(key, False):
                        print(f"Portrait clicked: {key} already placed -> cannot start placing")
                        return False
                    unit_cost = info.get('cost', 0)
                    if self.cost < unit_cost:
                        print(f"Not enough cost to place {key}: need={unit_cost}, have={int(self.cost)}")
                        return False
                    print(f"Portrait clicked: setting placing_unit={key} (cost={unit_cost})")
                    self.placing_unit = key
                    return True
            return False

        def _place_unit_on_tile(ev_tuple):
            if not left_m_down(ev_tuple):
                return False
            if self.placing_unit is None:
                return False
            ev = ev_tuple[1]
            mx, my = _get_mouse_pos(ev)

            TILE_W = 100
            TILE_H = 100
            COLS = 10

            # 현재 로드된 스테이지 모듈을 동적으로 찾아 사용 (stage02 우선, 없으면 stage01)
            import sys
            stage_module = None
            for mod_name in ('stage02', 'stage01'):
                if mod_name in sys.modules:
                    stage_module = sys.modules[mod_name]
                    break
            if stage_module is None:
                stage_module = stage01

            if not hasattr(stage_module, 'stage_temp') or len(stage_module.stage_temp) == 0:
                print("stage_temp empty")
                return False
            ROWS = len(stage_module.stage_temp) // COLS

            col = int(mx // TILE_W)
            row = int((get_canvas_height() - my) // TILE_H)
            idx = row * COLS + col

            print(f"Attempt place {self.placing_unit}: mx={mx}, my={my}, col={col}, row={row}, idx={idx}")

            if not (0 <= col < COLS and 0 <= row < ROWS):
                print("Clicked outside grid")
                return False
            if not (0 <= idx < len(stage_module.stage_temp)):
                print("Idx out of range")
                return False

            if idx in self.occupied_tiles:
                print(f"Tile {idx} already occupied -> cannot place here")
                return False

            tile_depth = stage_module.stage_temp[idx] - 1
            unit_cls = self.unit_map[self.placing_unit]['class']
            candidate_depth = unit_cls().depth
            print(f"DEBUG: tile_depth={tile_depth}, candidate_depth={candidate_depth}, idx={idx}")

            # 허용 규칙: 동일 깊이는 항상 허용, 추가로 'candidate_depth == 0' 인 유닛은 tile_depth == 4 에도 배치 가능하게 함
            if not (tile_depth == candidate_depth or (candidate_depth == 0 and tile_depth == 4)):
                print("Depth mismatch -> cannot place here")
                return False

            placed_key = self.placing_unit
            unit = unit_cls()
            unit.x = col * TILE_W + TILE_W // 2
            unit.y = (get_canvas_height() - ((row + 1) * TILE_H)) + TILE_H // 2
            unit.tile_center_x = unit.x
            unit.tile_center_y = unit.y

            unit._placed_key = placed_key
            unit._placed_idx = idx

            # 배치된 타일의 깊이를 기록 (heal 조건 등에서 사용)
            unit._placed_on_depth = tile_depth
            # 깊이 4에 배치되었을 때 회복을 활성화할 수 있도록 초기값 설정
            if tile_depth == 4:
                unit._depth4_heal = True
                unit._depth4_heal_timer = 0.0

            unit_depth = int((get_canvas_height() - my) // 100)
            game_world.add_object(unit, unit_depth)

            group = f'{unit.__class__.__name__.upper()}:MONSTER'
            game_world.add_collision_pair(group, unit, None)

            g_heal = f'HEALER:{placed_key.upper()}'
            if g_heal not in game_world.collision_pairs:
                game_world.add_collision_pair(g_heal, None, None)
            if unit not in game_world.collision_pairs[g_heal][1]:
                game_world.collision_pairs[g_heal][1].append(unit)

            overlay = BorderOverlay(unit)
            unit._overlay = overlay
            game_world.add_object(overlay, 7)

            unit_cost = self.unit_map[placed_key].get('cost', 0)
            self.unit_placed[placed_key] = True
            self._placed_unit = unit
            self.placing_unit = None
            self.occupied_tiles.add(idx)

            self.cost -= unit_cost
            return True

        def _motion_update_direction(ev_tuple):
            if not (isinstance(ev_tuple, tuple) and len(ev_tuple) >= 2 and ev_tuple[0] == 'INPUT' and getattr(
                    ev_tuple[1], 'type', None) == SDL_MOUSEMOTION):
                return False
            ev = ev_tuple[1]
            mx, my = _get_mouse_pos(ev)
            if self._placed_unit is None:
                return False
            dx = mx - self._placed_unit.x
            dy = my - self._placed_unit.y
            threshold = 5

            if abs(dy) > abs(dx) and abs(dy) > threshold:
                self._placed_unit.face_dir = 2 if dy > 0 else 3
            else:
                self._placed_unit.face_dir = 0 if dx >= 0 else 1
            return True

        def _left_up_finalize(ev_tuple):
            if left_m_up(ev_tuple) and self._placed_unit is not None:
                print("Placement finalized, returning to IDLE")
                self._placed_unit = None
                return True
            return False

        self.IDLE = Idle(self)
        self.PLACING = Place(self)
        self.DECIDE = Decide(self)
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {
                    _portrait_mouse_down: self.IDLE,
                    _left_up_if_placing: self.PLACING
                },
                self.PLACING: {
                    _place_unit_on_tile: self.DECIDE
                },
                self.DECIDE: {
                    _motion_update_direction: self.DECIDE,
                    _left_up_finalize: self.IDLE
                },
            }
        )

        # occupied_tiles는 외부에서 참조되므로 초기화
        self.occupied_tiles = set()

    def check(self):
        x = c_int()
        y = c_int()
        SDL_GetMouseState(x, y)
        mx, my = x.value, get_canvas_height() - y.value
        for key, info in self.unit_map.items():
            x_pos = info['x']
            if x_pos - 50 <= mx <= x_pos + 50 and self.p_y - 50 <= my <= self.p_y + 50:
                print('Character portrait clicked:', key)
                self.ch_num += 1
                print(f'Character number is now: {self.ch_num}')
                self.placing = True

    def update(self):
        self.cost = (self.cost + game_framework.frame_time)
        pass

    def draw(self):
        # 동적으로 등록된 유닛들만 그림
        for key, info in self.unit_map.items():
            img = info['image']
            x = info['x']
            img.clip_draw(0, 0, 1022, 1022, x, self.p_y, 100, 100)
        self.font.draw(0,110, f'{int(self.cost):02d}', (255, 255, 0))
        for key, info in self.unit_map.items():
            if self.unit_placed.get(key, False):
                x = info['x']
                left = x - 50
                bottom = self.p_y - 50
                right = x + 50
                top = self.p_y + 50
                draw_rectangle(left, bottom, right, top)
        for layer in getattr(game_world, 'world', []):
            for obj in list(layer):
                if obj is None:
                    continue
                if not (hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'skill')):
                    continue
                try:
                    if getattr(obj, 'skill', 0) == 10 and getattr(obj, 'depth', 0)  == 0:
                        draw_rectangle(obj.x - 10, obj.y + 90, obj.x + 10, obj.y + 110, 255, 215, 0, 3, True)
                    elif getattr(obj, 'skill', 0) == 10 and getattr(obj, 'depth', 0)  == 1:
                        draw_rectangle(obj.x - 10, obj.y + 130, obj.x + 10, obj.y + 150, 255, 215, 0, 3, True)
                    draw_rectangle(obj.x - 50, obj.y - 50, obj.x - 30, obj.y - 30, 255, 0, 0, 3, True)
                except Exception:
                    pass
    def handle_event(self, event):
        try:
            # 마우스 좌클릭만 특별 처리
            if getattr(event, 'type', None) == SDL_MOUSEBUTTONDOWN and getattr(event, 'button',
                                                                               None) == SDL_BUTTON_LEFT:
                mx, my = _get_mouse_pos(event)

                # 1\) 먼저 퇴각 클릭(빨간 사각형) 판정
                for layer in list(getattr(game_world, 'world', [])):
                    for obj in list(layer):
                        if obj is None:
                            continue
                        # 배치된 유닛으로 한정: x,y,skill 이 있고, `_placed_key` 가 존재하는 것만
                        if not (hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'skill')):
                            continue

                        # draw()에서 그린 빨간 사각형과 동일 범위
                        left = obj.x - 50
                        right = obj.x - 30
                        bottom = obj.y - 50
                        top = obj.y - 30

                        if left <= mx <= right and bottom <= my <= top:
                            # 이 유닛의 배치 키와 타일 인덱스 조회
                            placed_key = getattr(obj, '_placed_key', None)
                            placed_idx = getattr(obj, '_placed_idx', None)

                            # 비용 회수: 자신의 비용 절반의 정수만큼 추가
                            if placed_key and placed_key in self.unit_map:
                                unit_cost = self.unit_map[placed_key].get('cost', 0)
                                try:
                                    self.cost += int(unit_cost / 2)
                                except Exception:
                                    pass

                                # 배치 상태 해제
                                try:
                                    self.unit_placed[placed_key] = False
                                except Exception:
                                    pass

                            # 점유 타일 해제
                            if placed_idx is not None:
                                try:
                                    if placed_idx in self.occupied_tiles:
                                        self.occupied_tiles.remove(placed_idx)
                                except Exception:
                                    pass

                            # 유닛에 부착된 오버레이 제거
                            try:
                                overlay = getattr(obj, '_overlay', None)
                                if overlay is not None:
                                    game_world.remove_object(overlay)
                            except Exception:
                                pass

                            # 실제 유닛 제거
                            try:
                                game_world.remove_object(obj)
                            except Exception:
                                pass
                            try:
                                game_world.remove_collision_object(obj)
                            except Exception:
                                pass

                            # 퇴각 하나만 처리하고 종료
                            return

                # 2\) 스킬 발동 클릭(노란 사각형) 처리
                sm = getattr(self, 'state_machine', None)
                cur_state = None
                if sm is not None:
                    cur_state = getattr(sm, 'state', None) or getattr(sm, 'current_state', None) or getattr(sm,
                                                                                                            'cur_state',
                                                                                                            None)

                for layer in getattr(game_world, 'world', []):
                    for obj in list(layer):
                        if obj is None:
                            continue
                        # 필요한 속성들이 있는지 확인
                        if not (hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'skill') and hasattr(obj,
                                                                                                              'skill_state')):
                            continue

                        # 스킬 게이지가 가득 찬 유닛만 대상
                        if getattr(obj, 'skill', 0) != 10:
                            continue

                        # depth 에 따라 노란 사각형 위치 결정
                        if getattr(obj, 'depth', 0) == 0:
                            left = obj.x - 10
                            right = obj.x + 10
                            bottom = obj.y + 90
                            top = obj.y + 110
                        elif getattr(obj, 'depth', 0) == 1:
                            left = obj.x - 10
                            right = obj.x + 10
                            bottom = obj.y + 130
                            top = obj.y + 150
                        else:
                            continue

                        # 노란 사각형 클릭 \-> 스킬 발동
                        if left <= mx <= right and bottom <= my <= top:
                            try:
                                obj.skill_state = True
                            except Exception:
                                pass
                            return

            # 퇴각/스킬 처리 외의 나머지 입력은 기존 상태머신으로 전달
            try:
                self.state_machine.handle_state_event(('INPUT', event))
            except Exception:
                pass

        except Exception:
            # 예상치 못한 예외로 게임이 멈추지 않도록 방어
            try:
                self.state_machine.handle_state_event(('INPUT', event))
            except Exception:
                pass