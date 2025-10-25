from pico2d import load_image


class Knight:
    image = None
    def __init__(self):
        self.x, self.y = 0, 0
        self.frame = 0
        self.face_dir = 0
        self.Hp = 1000
        self.Def = 10
        self.Atk = 100
        if self.image is None:
            self.image = load_image('knight_01.png')
    def draw(self):
        self.image.clip_draw(0, 0, 100, 100, self.x, self.y)
    def update(self):
        pass