from pico2d import load_image, get_canvas_height

import game_framework

TIME_PER_ACTION = 0.3
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 2

class Tile:
    image_first = None
    image_second = None
    image_third = None
    image_forth = None
    s_image = None
    d_image = None
    frame = 0
    TILE_W = 100
    TILE_H = 100
    def __init__(self, num = 0, dep = 0):
        self.number, self.depth = num, dep
        if self.image_first is None and self.image_second is None:
            self.image_first = load_image('ground.png')
            self.image_second = load_image('floor_nd.png')
        if self.image_third is None and self.depth == 2:
            self.image_first = load_image('ground.png')
            self.image_third = load_image('cave.png')
        if self.image_forth is None and self.depth == 3 :
            self.image_first = load_image('ground.png')
            self.image_forth = load_image('de_place.png')
        if self.s_image is None and self.depth == 4:
            self.s_image = load_image('special_tile_recover.png')
        if self.d_image is None and self.depth == 5:
            self.d_image = load_image('special_tile_damage.png')

    def draw(self):
        canvas_h = get_canvas_height()
        col = self.number % 10
        row = self.number // 10
        x = col * Tile.TILE_W + Tile.TILE_W // 2
        # 위에서부터 그리려면 캔버스 높이에서 오프셋을 뺌
        y = canvas_h - (row * Tile.TILE_H + Tile.TILE_H // 2)
        if self.depth == 0:
            self.image_first.clip_draw(0, 0, 100, 100, x, y)
        elif self.depth == 1:
            self.image_second.clip_draw(0, 0, 47, 65, x, y, 100, 160)
        elif self.depth == 4:
            self.s_image.clip_draw(0, 0, 100, 100, x, y)
        elif self.depth == 5:
            self.d_image.clip_draw(0, 0, 100, 100, x, y)
        if self.depth == 2:
            self.image_first.clip_draw(0, 0, 100, 100, x, y)
            self.image_third.clip_composite_draw(0, 0, 78, 47, 0, 'h', x, y, 140, 160)
        if self.depth == 3:
            self.image_first.clip_draw(0, 0, 100, 100, x, y)
            self.image_forth.clip_draw(int(self.frame)*48, 0, 48, 45, x, y, 100, 100)


    def update(self):
        if self.depth == 3:
            self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 3

