from pico2d import load_image, get_canvas_width, get_canvas_height
from sdl2 import SDL_KEYDOWN, SDLK_SPACE, SDLK_RIGHT, SDL_KEYUP, SDLK_LEFT, SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT, SDL_MOUSEBUTTONUP

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
        if e and e[0] == 'INPUT':
            sdl_e = e[1]

            if hasattr(sdl_e, 'x') and hasattr(sdl_e, 'y'):
                tile_size = 100
                mx = int(sdl_e.x)
                my = int(sdl_e.y)
                canvas_h = get_canvas_height()
                canvas_w = get_canvas_width()

                # SDL y -> pico2d y (반전)
                py = canvas_h - my

                # 타일 중앙으로 스냅
                gx = (mx // tile_size) * tile_size + tile_size // 2
                gy = (py // tile_size) * tile_size + tile_size // 2

                # 캔버스 경계 내로 클램프
                min_x = tile_size // 2
                max_x = (canvas_w // tile_size) * tile_size - tile_size // 2
                min_y = tile_size // 2
                max_y = (canvas_h // tile_size) * tile_size - tile_size // 2

                gx = max(min_x, min(gx, max_x))
                gy = max(min_y, min(gy, max_y))

                self.knight.x = gx
                self.knight.y = gy
        pass
    def do(self):
        mx = getattr(self.knight, 'last_mouse_x', None)
        if mx is None:
            return

        compare_x = getattr(self.knight, 'x', None)
        if compare_x is None or compare_x == 0:
            compare_x = get_canvas_width() // 2

        self.knight.face_dir = 0 if mx >= compare_x else 1
        pass
    def draw(self):
        self.knight.p_image.clip_draw(0, 0, 1022, 1022, self.knight.p_x, self.knight.p_y, 100, 100)
        pass



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
        if self.image is None:
            self.image = load_image('knight_01.png')
        if self.p_image is None:
            self.p_image = load_image('Knight_portrait.png')

        self.NON_APPEAR = Non_appear(self)
        self.READY_TO_APPEAR = Ready_to_appear(self)
        self.IDLE = Idle(self)
        self.state_machine = StateMachine(
            self.NON_APPEAR,
            {
                self.NON_APPEAR : {m_left_up : self.READY_TO_APPEAR},
                self.READY_TO_APPEAR : {m_left_up : self.IDLE},
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
        # 마우스 무브를 캐치해 화면 좌표로 변환하여 저장
        if getattr(event, 'type', None) == getattr(__import__('sdl2'), 'SDL_MOUSEMOTION', None):
            mx = getattr(event, 'x', 0)
            my = getattr(event, 'y', 0)
            try:
                self.last_mouse_x = int(mx)
                self.last_mouse_y = get_canvas_height() - int(my)
            except Exception:
                self.last_mouse_x = int(mx)
                self.last_mouse_y = int(my)
        self.state_machine.handle_state_event(('INPUT',event))