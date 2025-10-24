from pico2d import load_image


class Knight:
    image = load_image('knight.png')
    def __init__(self):
        self.x, self.y = 0, 0
        self.frame = 0
        self.face_dir = 0
        self.Hp = 1000
        self.Def = 10
        self.Atk = 100
