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
        self.cost = 20

        # portraits 로드(한번만)
        if self.k_p_image is None:
            self.k_p_image = load_image('char/Knight_portrait.png')
        if self.a_p_image is None:
            self.a_p_image = load_image('char/Archer_portrait.png')
        if self.h_p_image is None:
            self.h_p_image = load_image('char/Hptank_portrait.png')
        if self.d_p_image is None:
            self.d_p_image = load_image('char/Dptank_portrait.png')
        if self.s_p_image is None:
            self.s_p_image = load_image('char/Healer_portrait.png')
        if self.v_p_image is None:
            self.v_p_image = load_image('char/Vanguard_portrait.png')

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

            import sys

            stage_module = None
            # 1순위: 이 Character 인스턴스를 가진 stage 모듈을 찾는다.
            for mod_name in ('stage03', 'stage02', 'stage01'):
                mod = sys.modules.get(mod_name)
                if not mod:
                    continue
                try:
                    ch = getattr(mod, 'character', None)
                except Exception:
                    ch = None
                if ch is self:
                    stage_module = mod
                    break

            # 2순위: 기존처럼 로드된 모듈 중 하나를 사용하되, 위에서 못 찾았을 때만
            if stage_module is None:
                for mod_name in ('stage03', 'stage02', 'stage01'):
                    if mod_name in sys.modules:
                        stage_module = sys.modules[mod_name]
                        break

            # 어떤 스테이지도 로드되지 않았다면 기본값으로 stage01 사용
            if stage_module is None:
                stage_module = stage01

            # stage_temp 존재 및 길이 검사
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
            print(f"DEBUG: tile_depth={tile_depth}, candidate_depth={candidate_depth}, idx={idx}, stage={stage_module.__name__}")

            # 허용 규칙: 동일 깊이는 항상 허용,
            # 추가로 'candidate_depth == 0' 인 유닛은 tile_depth == 4(타일값 5) 또는 tile_depth == 5(타일값 6) 에도 배치 가능하게 함
            if not (tile_depth == candidate_depth or (candidate_depth == 0 and tile_depth in (4, 5))):
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
        # 코스트만 표시 (몬스터 HUD는 각 스테이지 draw()에서 그림)
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
                    can_use_skill = (getattr(obj, 'skill', 0) >= 10 and not getattr(obj, 'skill_state', False))
                    # depth 에 따라 스킬/퇴각 UI 위치 조정
                    if getattr(obj, 'depth', 0) == 0:
                        # 스킬 버튼: skill==10 이고 아직 발동 중이 아닐 때만 노란 버튼 그리기
                        if can_use_skill:
                            draw_rectangle(obj.x - 10, obj.y + 90, obj.x + 10, obj.y + 110, 255, 215, 0, 3, True)
                        # depth 0 퇴각 버튼
                        draw_rectangle(obj.x - 50, obj.y - 50, obj.x - 30, obj.y - 30, 255, 0, 0, 3, True)
                    elif getattr(obj, 'depth', 0) == 1:
                        if can_use_skill:
                            draw_rectangle(obj.x - 10, obj.y + 130, obj.x + 10, obj.y + 150, 255, 215, 0, 3, True)
                        draw_rectangle(obj.x - 50, obj.y - 10, obj.x - 30, obj.y + 10, 255, 0, 0, 3, True)
                    else:
                        # 다른 depth 는 퇴각 버튼을 그리지 않음
                        pass
                except Exception:
                    pass

        # 링크 아이콘을 항상 최상위 UI 레이어에서 그리기 (linked == True 인 모든 유닛 대상)
        try:
            # Knight 클래스에 정의된 공용 링크 아이콘(있으면 사용)
            try:
                default_icon = getattr(Knight, 'image_l', None)
            except Exception:
                default_icon = None

            for layer in getattr(game_world, 'world', []):
                for obj in list(layer):
                    if obj is None:
                        continue
                    # linked 플래그가 True 인 오브젝트만 대상
                    if not getattr(obj, 'linked', False):
                        continue
                    # 개별 유닛에 image_l 가 있으면 우선 사용, 없으면 Knight 의 공용 아이콘 사용
                    img_l = getattr(obj, 'image_l', default_icon)
                    if img_l is None:
                        continue
                    try:
                        # Vanguard 의 asha_link.png 는 원본 크기 56x56 이므로 그 크기로 clip
                        if obj.__class__.__name__ == 'Vanguard':
                            src_w, src_h = 56, 56
                        else:
                            src_w, src_h = 84, 84

                        if getattr(obj, 'depth', 0) == 0:
                            img_l.clip_draw(0, 0, src_w, src_h, obj.x + 40, obj.y - 40, 20, 20)
                        elif getattr(obj, 'depth', 0) == 1:
                            img_l.clip_draw(0, 0, src_w, src_h, obj.x + 40, obj.y, 20, 20)
                    except Exception:
                        pass
        except Exception:
            pass

    def handle_event(self, event):
        def _get_mouse_pos(ev):
            try:
                if getattr(ev, 'type', None) == SDL_MOUSEBUTTONDOWN:
                    return ev.button.x, get_canvas_height() - ev.button.y - 1
            except Exception:
                pass
            try:
                from sdl2 import SDL_GetMouseState
                mx = c_int(0)
                my = c_int(0)
                SDL_GetMouseState(mx, my)
                return mx.value, get_canvas_height() - my.value - 1
            except Exception:
                return 0, 0

        # 1) 기존 상태머신 입력 이벤트 전달(배치/선택 등)
        try:
            self.state_machine.handle_state_event(('INPUT', event))
        except Exception:
            pass

        # 2) 마우스 좌클릭이 아닌 경우 추가 처리 없음
        if getattr(event, 'type', None) != SDL_MOUSEBUTTONDOWN:
            return
        if getattr(event, 'button', None) != SDL_BUTTON_LEFT:
            return

        mx, my = _get_mouse_pos(event)

        # 3) 먼저 "퇴각" 영역(각 유닛 좌하단 빨간 사각형)을 클릭했는지 검사
        retreat_target = None
        for layer in list(getattr(game_world, 'world', [])):
            for obj in list(layer):
                if obj is None:
                    continue
                # 배치된 유닛만 대상: x,y,skill 을 가진 depth 0 또는 1 유닛
                if not (hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'skill')):
                    continue
                try:
                    if getattr(obj, 'depth', 0) == 0:
                        # depth 0: draw()에서 그린 y - 50 ~ y - 30 과 동일한 영역
                        left = obj.x - 50
                        bottom = obj.y - 50
                        right = obj.x - 30
                        top = obj.y - 30
                    elif getattr(obj, 'depth', 0) == 1:
                        # depth 1: draw()에서 그린 y - 10 ~ y + 10 과 동일한 영역
                        left = obj.x - 50
                        bottom = obj.y - 10
                        right = obj.x - 30
                        top = obj.y + 10
                    else:
                        continue
                except Exception:
                    continue

                if left <= mx <= right and bottom <= my <= top:
                    retreat_target = obj
                    break
            if retreat_target is not None:
                break

        if retreat_target is not None:
            # 퇴각 처리: cost//2 반환, 유닛/오버레이 및 충돌 제거, 타일/배치 상태 정리
            unit = retreat_target
            try:
                # 어떤 키로 배치되었는지 (_placed_key)가 있으면 그 키의 cost 기준으로 환급
                placed_key = getattr(unit, '_placed_key', None)
                if placed_key and placed_key in self.unit_map:
                    unit_cost = self.unit_map[placed_key].get('cost', 0)
                    refund = unit_cost // 2
                    self.cost += refund
                    # 하나만 배치 가능한 유닛이면 배치 상태도 해제
                    if placed_key in self.unit_placed:
                        self.unit_placed[placed_key] = False
                # _placed_idx 가 있다면 occupied_tiles 집합에서 제거
                idx = getattr(unit, '_placed_idx', None)
                if idx is not None and idx in self.occupied_tiles:
                    self.occupied_tiles.discard(idx)
            except Exception:
                pass

            # world/collision/overlay 에서 안전하게 제거
            try:
                overlay = getattr(unit, '_overlay', None)
                if overlay is not None:
                    try:
                        game_world.remove_object(overlay)
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                game_world.remove_object(unit)
            except Exception:
                pass
            try:
                game_world.remove_collision_object(unit)
            except Exception:
                pass

            # 유닛 쪽에 별도 clean-up 메서드가 있다면 호출
            try:
                if hasattr(unit, 'die'):
                    unit.die()
            except Exception:
                pass

            return  # 퇴각 클릭이면 여기서 종료 (스킬 클릭은 처리하지 않음)

        # 4) 퇴각이 아니라면 기존 스킬 클릭 처리 수행
        selected_unit = None

        # 월드 전체를 훑어서 스킬 영역을 클릭한 유닛 1개만 선택
        for layer in list(game_world.world):
            for obj in list(layer):
                if obj is None:
                    continue
                # 스킬 보유 유닛만 대상
                if not (hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'skill')):
                    continue

                try:
                    # 각 depth 에 따른 스킬 클릭 영역
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
                        # 다른 depth 에서는 스킬 클릭 영역 없음
                        continue
                except Exception:
                    continue

                # skill 이 10이 아니면 발동 불가
                if getattr(obj, 'skill', 0) < 10:
                    continue

                # 클릭 위치가 영역 안인지 판정
                if left <= mx <= right and bottom <= my <= top:
                    selected_unit = obj
                    break
            if selected_unit is not None:
                break

        # 실제 스킬 발동은 여기서 딱 한 번만
        if selected_unit is not None:
            try:
                # 이미 켜져 있으면 다시 켜지지 않음
                if not getattr(selected_unit, 'skill_state', False):
                    selected_unit.skill_state = True
                    # skill 감소는 각 유닛 update() 에서만 처리
            except Exception:
                pass
