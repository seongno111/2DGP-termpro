# python
from pico2d import *
from sdl2 import SDL_BUTTON_LEFT, SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP, SDL_MOUSEMOTION, SDL_GetMouseState
from ctypes import c_int

import game_world
import play_mode
from state_machine import StateMachine
from Knight import Knight

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
    ch_num = 0
    placing = False

    def __init__(self):
        self.p_y = 50
        self.k_p_x = 50
        if self.k_p_image is None:
            self.k_p_image = load_image('Knight_portrait.png')

        self._placed_knight = None

        def _left_up_if_placing(e):
            # left up 시 PLACING으로 전이, 하지만 placing 플래그는 바로 끄지 않음(실제 배치 성공시 끔)
            if left_m_up(e) and self.placing:
                print("LEFT UP -> PLACING 트리거 (placing remains True until placed)")
                return True
            return False

        def _portrait_mouse_down(ev_tuple):
            if not left_m_down(ev_tuple):
                return False
            ev = ev_tuple[1]
            mx, my = _get_mouse_pos(ev)
            if self.k_p_x - 50 <= mx <= self.k_p_x + 50 and self.p_y - 50 <= my <= self.p_y + 50:
                print("Portrait clicked: setting placing=True")
                self.placing = True
            return False

        def _place_knight_on_tile(ev_tuple):
            # PLACING 상태에서 실제 타일 클릭으로 배치 시도
            if not left_m_down(ev_tuple):
                return False
            if not self.placing:
                print("PLACING state but placing flag is False -> ignoring")
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
            row = int(my // TILE_H)
            idx = row * COLS + col

            print(f"Attempt place: mx={mx}, my={my}, col={col}, row={row}, idx={idx}")

            if not (0 <= col < COLS and 0 <= row < ROWS):
                print("Clicked outside grid")
                return False
            if not (0 <= idx < len(play_mode.stage_temp)):
                print("Idx out of range")
                return False

            # stage_temp 값(1..3) 에서 실제 depth = value - 1
            tile_depth = play_mode.stage_temp[idx] - 1
            candidate_depth = Knight().depth
            print(f"tile_depth={tile_depth}, candidate_depth={candidate_depth}, stage_val={play_mode.stage_temp[idx]}")

            # 수정: 같은 깊이뿐 아니라 타일 깊이가 후보 깊이보다 크거나 같으면 배치 허용
            if tile_depth < candidate_depth:
                print("Depth too shallow -> cannot place here")
                return False

            knight = Knight()
            # 타일 중앙에 배치
            knight.x = col * TILE_W + TILE_W // 2
            knight.y = row * TILE_H + TILE_H // 2
            knight.tile_center_x = knight.x
            knight.tile_center_y = knight.y
            # 레이어는 knight.depth로 등록
            game_world.add_object(knight, my//100)
            self._placed_knight = knight
            self.placing = False  # 배치 완료하면 플래그 끔
            print(f"Knight placed at idx={idx}, x={knight.x}, y={knight.y}")
            return True

        def _motion_update_direction(ev_tuple):
            if not (isinstance(ev_tuple, tuple) and len(ev_tuple) >= 2 and ev_tuple[0] == 'INPUT' and getattr(ev_tuple[1], 'type', None) == SDL_MOUSEMOTION):
                return False
            ev = ev_tuple[1]
            mx, _ = _get_mouse_pos(ev)
            if self._placed_knight is None:
                return False
            self._placed_knight.face_dir = 0 if mx >= self._placed_knight.x else 1
            return True

        def _left_up_finalize(ev_tuple):
            if left_m_up(ev_tuple) and self._placed_knight is not None:
                print("Placement finalized, returning to IDLE")
                self._placed_knight = None
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
                    _place_knight_on_tile: self.DECIDE
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

    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))