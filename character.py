# python
from pico2d import *
from sdl2 import SDL_BUTTON_LEFT, SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP, SDL_MOUSEMOTION, SDL_GetMouseState
from ctypes import c_int
from collections import OrderedDict

import game_world
import play_mode
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
    """
    유닛의 get_at_bound() 를 이용해 경계 사각형만 그리는 오버레이.
    이 객체를 항상 최상위 레이어에 추가하면 타일보다 위에 그려짐.
    """
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
        # 진입시 디버그
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

    def __init__(self):
        self.p_y = 50
        self.k_p_x = 50
        self.a_p_x = 150
        self.h_p_x = 250
        self.d_p_x = 350
        self.s_p_x = 450
        self.v_p_x = 550
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

        self.unit_map = OrderedDict([
            ('knight', {'x': self.k_p_x, 'image': self.k_p_image, 'class': Knight}),
            ('archer', {'x': self.a_p_x, 'image': self.a_p_image, 'class': Archer}),
            ('hptank', {'x': self.h_p_x, 'image': self.h_p_image, 'class': Hptank}),
            ('dptank', {'x': self.d_p_x, 'image': self.d_p_image, 'class': Dptank}),
            ('healer', {'x': self.s_p_x, 'image': self.s_p_image, 'class': Healer}),
            ('vanguard', {'x': self.v_p_x, 'image': self.v_p_image, 'class': Vanguard}),
        ])

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
                    print(f"Portrait clicked: setting placing_unit={key}")
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
            if len(play_mode.stage_temp) == 0:
                print("stage_temp empty")
                return False
            ROWS = len(play_mode.stage_temp) // COLS

            col = int(mx // TILE_W)
            row = int((get_canvas_height() - my) // TILE_H)
            idx = row * COLS + col

            print(f"Attempt place {self.placing_unit}: mx={mx}, my={my}, col={col}, row={row}, idx={idx}")

            if not (0 <= col < COLS and 0 <= row < ROWS):
                print("Clicked outside grid")
                return False
            if not (0 <= idx < len(play_mode.stage_temp)):
                print("Idx out of range")
                return False

            tile_depth = play_mode.stage_temp[idx] - 1
            unit_cls = self.unit_map[self.placing_unit]['class']
            candidate_depth = unit_cls().depth
            print(f"tile_depth={tile_depth}, candidate_depth={candidate_depth}, stage_val={play_mode.stage_temp[idx]}")

            if tile_depth != candidate_depth:
                print("Depth mismatch -> cannot place here")
                return False

            unit = unit_cls()
            unit.x = col * TILE_W + TILE_W // 2
            unit.y = (get_canvas_height() - ((row + 1) * TILE_H)) + TILE_H // 2
            unit.tile_center_x = unit.x
            unit.tile_center_y = unit.y

            game_world.add_object(unit, (get_canvas_height() - my) // 100)

            overlay = BorderOverlay(unit)
            unit._overlay = overlay  # 필요하면 참조 저장
            game_world.add_object(overlay, 7)

            # 배치 완료 처리: 플래그 설정
            placed_key = self.placing_unit
            self.unit_placed[placed_key] = True
            self._placed_unit = unit
            self.placing_unit = None
            print(f"{placed_key} placed at idx={idx}, x={unit.x}, y={unit.y}")
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
            threshold = 5  # 작은 떨림 무시

            if abs(dy) > abs(dx) and abs(dy) > threshold:
                # 수직 이동이 더 크면 위(2) 또는 아래(3)
                self._placed_unit.face_dir = 2 if dy > 0 else 3
            else:
                # 수평 기준: 오른쪽(0) 또는 왼쪽(1)
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

    def check(self):
        x = c_int()
        y = c_int()
        SDL_GetMouseState(x, y)
        mx, my = x.value, get_canvas_height() - y.value
        if self.k_p_x - 50 <= mx <= self.k_p_x + 50 and self.p_y - 50 <= my <= self.p_y + 50:
            print('Character clicked!')
            self.ch_num += 1
            print(f'Character number is now: {self.ch_num}')
            self.placing = True

    def update(self):
        pass

    def draw(self):
        self.k_p_image.clip_draw(0, 0, 1022, 1022, self.k_p_x, self.p_y, 100, 100)
        self.a_p_image.clip_draw(0, 0, 1022, 1022, self.a_p_x, self.p_y, 100, 100)
        self.h_p_image.clip_draw(0, 0, 1022, 1022, self.h_p_x, self.p_y, 100, 100)
        self.d_p_image.clip_draw(0, 0, 1022, 1022, self.d_p_x, self.p_y, 100, 100)
        self.s_p_image.clip_draw(0, 0, 1022, 1022, self.s_p_x, self.p_y, 100, 100)
        self.v_p_image.clip_draw(0, 0, 1022, 1022, self.v_p_x, self.p_y, 100, 100)

        for key, info in self.unit_map.items():
            if self.unit_placed.get(key, False):
                x = info['x']
                left = x - 50
                bottom = self.p_y - 50
                right = x + 50
                top = self.p_y + 50
                draw_rectangle(left, bottom, right, top)

    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))