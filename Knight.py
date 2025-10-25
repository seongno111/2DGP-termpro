from pico2d import load_image


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
        if self.image is None:
            self.image = load_image('knight_01.png')
        if self.p_image is None:
            self.p_image = load_image('Knight_portrait.png')
    def draw(self):
        self.image.clip_draw(0, 0, 100, 100, self.x, self.y)
    def set_number(self, number):
        self.number = number
        self.p_x, self.p_y = (number-1)*100+50, 50
    def update(self):
        pass