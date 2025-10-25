from pico2d import load_image, get_canvas_height


class Tile:
    image_first = None
    image_second = None
    TILE_W = 100
    TILE_H = 100
    def __init__(self):
        if self.image_first is None and self.image_second is None:
            self.image_first = load_image('ground.png')
            self.image_second = load_image('floor_nd.png')
    def draw(self, stage):
        canvas_h = get_canvas_height()
        for i in range(len(stage)):
            col = i % 10
            row = i // 10
            x = col * Tile.TILE_W + Tile.TILE_W // 2
            # 위에서부터 그리려면 캔버스 높이에서 오프셋을 뺌
            y = canvas_h - (row * Tile.TILE_H + Tile.TILE_H // 2)
            if stage[i] == 1:
                self.image_first.clip_draw(0, 0, 100, 100, x, y)
            elif stage[i] == 2:
                self.image_second.clip_draw(0, 0,100, 150, x, y)
    def update(self):
        pass
