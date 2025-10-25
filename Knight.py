from pico2d import load_image, get_canvas_width, get_canvas_height
from sdl2 import SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT, SDL_MOUSEBUTTONUP, SDL_MOUSEMOTION

from state_machine import StateMachine

def m_left_down(e):
    return e[0] == 'INPUT' and e[1].type == SDL_MOUSEBUTTONDOWN and getattr(e[1], 'button', None) == SDL_BUTTON_LEFT

def m_left_up(e):
    return e[0] == 'INPUT' and e[1].type == SDL_MOUSEBUTTONUP and getattr(e[1], 'button', None) == SDL_BUTTON_LEFT

class Non_appear:
    def __init__(self, knight):
        self.knight = knight
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
       pass
    def draw(self):
        self.knight.p_image.clip_draw(0, 0, 1022, 1022, self.knight.p_x, self.knight.p_y, 100, 100)


class Idle:
    def __init__(self, knight):
        self.knight = knight
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        pass
    def draw(self):
        x = self.knight.x
        y = self.knight.y + 50
        # face_dir == 0 -> 오른쪽, 1 -> 왼쪽(수평 반전)
        if getattr(self.knight, 'face_dir', 0) == 0:
            self.knight.image.clip_draw(0, 0, 100, 100, x, y, 150, 150)
        else:
            # 'h' 플래그로 수평 반전
            self.knight.image.clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 150)
        self.knight.p_image.clip_draw(0, 0, 1022, 1022, self.knight.p_x, self.knight.p_y, 100, 100)



class Ready_to_appear:
    def __init__(self, knight):
        self.knight = knight
    def enter(self, e):
        pass
    def exit(self, e):
        # placement happens on mouse-up: Ready->Idle transition triggers this exit
        pass
    def do(self):

        return
    def draw(self):
        self.knight.p_image.clip_draw(0, 0, 1022, 1022, self.knight.p_x, self.knight.p_y, 100, 100)


class Decide_direction:
    def __init__(self, knight):
        self.knight = knight

    def enter(self, e):
        sdl_e = e[1] if isinstance(e, tuple) and len(e) > 1 else e
        if not (hasattr(sdl_e, 'x') and hasattr(sdl_e, 'y')):
            return
        mx = int(sdl_e.x)
        my = int(sdl_e.y)
        canvas_h = get_canvas_height()
        py = canvas_h - my

        tw, th = self.knight.tile_w, self.knight.tile_h
        tile_cx = (mx // tw) * tw + tw // 2
        tile_cy = (py // th) * th + th // 2

        self.knight.tile_center_x = tile_cx
        self.knight.tile_center_y = tile_cy
        self.knight.x = tile_cx
        self.knight.y = tile_cy - 20

        # 초기 방향 결정
        self.knight.face_dir = 0 if mx >= tile_cx else 1

        self.knight.in_decide = True
        # 초기화: handle_event가 업데이트한 마지막 위치를 사용
        if getattr(self.knight, 'last_motion_x', None) is None:
            self.knight.last_motion_x = mx
            self.knight.last_motion_y = my

    def exit(self, e):
        self.knight.in_decide = False
        self.knight.last_motion_x = None
        self.knight.last_motion_y = None

    def do(self):
        # handle_event가 갱신한 최신 마우스 x로 facing 결정
        lm_x = getattr(self.knight, 'last_motion_x', None)
        if lm_x is None:
            return
        if lm_x >= getattr(self.knight, 'tile_center_x', self.knight.x):
            self.knight.face_dir = 0
        else:
            self.knight.face_dir = 1

    def draw(self):
        x = self.knight.x
        y = self.knight.y + 50
        if getattr(self.knight, 'face_dir', 0) == 0:
            self.knight.image.clip_draw(0, 0, 100, 100, x, y, 150, 150)
        else:
            self.knight.image.clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 150)
        self.knight.p_image.clip_draw(0, 0, 1022, 1022, self.knight.p_x, self.knight.p_y, 100, 100)


class Knight:
    image = None
    p_image = None
    def __init__(self):
        self.x, self.y = 0, 0
        self.p_x, self.p_y = 0, 0
        self.frame = 0
        self.face_dir = 0
        self.Hp = 1000
        self.Def = 10
        self.Atk = 100
        self.number = 1
        self.last_mouse_x = None
        self.last_mouse_y = None
        self.last_motion_x = None
        self.last_motion_y = None
        self.tile_w = 100
        self.tile_h = 100
        self.in_decide = False
        self.tile_center_x = 0
        self.tile_center_y = 0
        if self.image is None:
            self.image = load_image('knight_01.png')
        if self.p_image is None:
            self.p_image = load_image('Knight_portrait.png')
        self.NON_APPEAR = Non_appear(self)
        self.READY_TO_APPEAR = Ready_to_appear(self)
        self.DECIDE_DIRECTION = Decide_direction(self)
        self.IDLE = Idle(self)

        def m_left_up_on_portrait(e, _self=self):
            if e[0] != 'INPUT':
                return False
            sdl_e = e[1]
            if getattr(sdl_e, 'type', None) != SDL_MOUSEBUTTONUP or getattr(sdl_e, 'button', None) != SDL_BUTTON_LEFT:
                return False
            if not (hasattr(sdl_e, 'x') and hasattr(sdl_e, 'y')):
                return False

            mx = int(sdl_e.x)
            my = int(sdl_e.y)
            canvas_h = get_canvas_height()

            # SDL Y -> pico2d Y 변환
            py = canvas_h - my

            # portrait 크기(코드에서 draw에 사용한 100x100)
            pw, ph = 100, 100
            left = _self.p_x - pw // 2
            right = _self.p_x + pw // 2
            bottom = _self.p_y - ph // 2
            top = _self.p_y + ph // 2

            return left <= mx <= right and bottom <= py <= top

        self.state_machine = StateMachine(
            self.NON_APPEAR,
            {
                self.NON_APPEAR : {m_left_up_on_portrait : self.READY_TO_APPEAR},
                self.READY_TO_APPEAR : {m_left_down : self.DECIDE_DIRECTION},
                self.DECIDE_DIRECTION : {m_left_up : self.IDLE},
                self.IDLE : {}
             }
        )

    def draw(self):
        self.state_machine.draw()
    def set_number(self, number):
        self.number = number
        self.p_x, self.p_y = (number-1)*100+50, 50
    def update(self):
        self.state_machine.update()
    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT',event))
        if getattr(event, 'type', None) == SDL_MOUSEMOTION and hasattr(event, 'x') and hasattr(event, 'y'):
            self.last_motion_x = int(event.x)
            self.last_motion_y = int(event.y)
